//! Handoff orchestration pattern

use super::{
    Orchestration, OrchestrationContext, OrchestrationResult, OrchestrationState,
    OrchestrationStep,
};
use crate::agent::Agent;
use crate::errors::{AgentError, Result};
use async_trait::async_trait;
use semantic_kernel::{ChatMessageContent, AuthorRole};
use std::collections::HashMap;
use std::sync::Arc;
use std::time::Instant;

/// Defines handoff rules for agent orchestration.
/// 
/// A handoff rule specifies when and how an agent should transfer
/// control to another agent based on certain conditions.
#[derive(Debug, Clone)]
pub struct HandoffRule {
    /// The agent that this rule applies to
    pub from_agent: String,
    /// The target agent to hand off to
    pub to_agent: String,
    /// Condition that triggers the handoff (e.g., "TECHNICAL", "BILLING")
    pub condition: String,
    /// Optional description of when this handoff should occur
    pub description: Option<String>,
}

impl HandoffRule {
    /// Creates a new handoff rule.
    pub fn new(
        from_agent: impl Into<String>,
        to_agent: impl Into<String>,
        condition: impl Into<String>,
    ) -> Self {
        Self {
            from_agent: from_agent.into(),
            to_agent: to_agent.into(),
            condition: condition.into(),
            description: None,
        }
    }
    
    /// Sets the description for this handoff rule.
    pub fn with_description(mut self, description: impl Into<String>) -> Self {
        self.description = Some(description.into());
        self
    }
}

/// Configuration for handoff-based orchestration.
#[derive(Debug, Clone)]
pub struct HandoffConfig {
    /// Rules that define when agents should hand off to each other
    pub rules: Vec<HandoffRule>,
    /// The initial agent to start with
    pub initial_agent: String,
    /// Maximum number of handoffs to prevent infinite loops
    pub max_handoffs: usize,
    /// Whether agents should include handoff instructions in their prompts
    pub include_handoff_instructions: bool,
}

impl HandoffConfig {
    /// Creates a new handoff configuration.
    pub fn new(initial_agent: impl Into<String>) -> Self {
        Self {
            rules: Vec::new(),
            initial_agent: initial_agent.into(),
            max_handoffs: 10,
            include_handoff_instructions: true,
        }
    }
    
    /// Adds a handoff rule.
    pub fn add_rule(mut self, rule: HandoffRule) -> Self {
        self.rules.push(rule);
        self
    }
    
    /// Sets the maximum number of handoffs.
    pub fn with_max_handoffs(mut self, max_handoffs: usize) -> Self {
        self.max_handoffs = max_handoffs;
        self
    }
    
    /// Sets whether to include handoff instructions.
    pub fn with_handoff_instructions(mut self, include: bool) -> Self {
        self.include_handoff_instructions = include;
        self
    }
    
    /// Gets all possible target agents for a given source agent.
    pub fn get_targets(&self, from_agent: &str) -> Vec<&HandoffRule> {
        self.rules.iter()
            .filter(|rule| rule.from_agent == from_agent)
            .collect()
    }
    
    /// Finds a target agent based on a condition keyword.
    pub fn find_target(&self, from_agent: &str, condition: &str) -> Option<&str> {
        self.rules.iter()
            .find(|rule| rule.from_agent == from_agent && 
                  condition.to_lowercase().contains(&rule.condition.to_lowercase()))
            .map(|rule| rule.to_agent.as_str())
    }
}

/// An orchestration that supports dynamic handoff between agents based on
/// the content and intent of messages.
/// 
/// This pattern allows agents to evaluate incoming requests and decide
/// whether they should handle the request themselves or hand it off to
/// a more specialized agent.
pub struct HandoffOrchestration {
    agents: Vec<Arc<dyn Agent>>,
    agent_map: HashMap<String, Arc<dyn Agent>>,
    config: HandoffConfig,
}

impl HandoffOrchestration {
    /// Creates a new handoff orchestration.
    pub fn new(agents: Vec<Arc<dyn Agent>>, config: HandoffConfig) -> Result<Self> {
        // Create a map for quick agent lookup
        let mut agent_map = HashMap::new();
        for agent in &agents {
            agent_map.insert(agent.id().to_string(), agent.clone());
            if let Some(name) = agent.name() {
                agent_map.insert(name.to_string(), agent.clone());
            }
        }
        
        // Validate that initial agent exists
        if !agent_map.contains_key(&config.initial_agent) {
            return Err(AgentError::Configuration(
                format!("Initial agent '{}' not found in provided agents", config.initial_agent),
            ));
        }
        
        // Validate that all agents referenced in rules exist
        for rule in &config.rules {
            if !agent_map.contains_key(&rule.from_agent) {
                return Err(AgentError::Configuration(
                    format!("Agent '{}' in handoff rule not found", rule.from_agent),
                ));
            }
            if !agent_map.contains_key(&rule.to_agent) {
                return Err(AgentError::Configuration(
                    format!("Target agent '{}' in handoff rule not found", rule.to_agent),
                ));
            }
        }
        
        Ok(Self {
            agents,
            agent_map,
            config,
        })
    }
    
    /// Creates handoff instructions for an agent based on available rules.
    fn create_handoff_instructions(&self, agent_id: &str) -> String {
        let targets = self.config.get_targets(agent_id);
        if targets.is_empty() {
            return String::new();
        }
        
        let mut instructions = String::from("\n\nHandoff Instructions:\n");
        instructions.push_str("If you cannot handle a request or determine it would be better handled by another agent, ");
        instructions.push_str("include 'HANDOFF:' followed by the appropriate keyword in your response:\n");
        
        for rule in targets {
            instructions.push_str(&format!(
                "- Use 'HANDOFF: {}' for {} (to {})\n",
                rule.condition,
                rule.description.as_deref().unwrap_or("relevant requests"),
                rule.to_agent
            ));
        }
        
        instructions
    }
    
    /// Extracts handoff instruction from an agent's response.
    fn extract_handoff(&self, response: &str) -> Option<String> {
        // Look for HANDOFF: anywhere in the response
        if let Some(start) = response.find("HANDOFF:") {
            let after_handoff = &response[start + 8..]; // 8 is length of "HANDOFF:"
            if let Some(condition) = after_handoff.split_whitespace().next() {
                return Some(condition.to_string());
            }
        }
        None
    }
    
    /// Gets the agent for a given ID or name.
    fn get_agent(&self, id_or_name: &str) -> Option<Arc<dyn Agent>> {
        self.agent_map.get(id_or_name).cloned()
    }
}

#[async_trait]
impl Orchestration for HandoffOrchestration {
    fn agents(&self) -> &[Arc<dyn Agent>] {
        &self.agents
    }
    
    fn orchestration_type(&self) -> &str {
        "Handoff"
    }
    
    async fn execute_async(
        &self,
        input: &str,
        context: Option<OrchestrationContext>,
    ) -> Result<OrchestrationResult> {
        let ctx = context.unwrap_or_default();
        let start_time = Instant::now();
        let mut state = OrchestrationState::new(input.to_string(), ctx.trace_enabled);
        
        let mut current_agent_id = self.config.initial_agent.clone();
        let mut current_input = input.to_string();
        let mut handoff_count = 0;
        let mut final_output = ChatMessageContent::new(AuthorRole::Assistant, String::new());
        
        loop {
            // Check for maximum handoffs
            if handoff_count >= self.config.max_handoffs {
                return Err(AgentError::Orchestration(
                    format!("Maximum handoffs ({}) exceeded", self.config.max_handoffs),
                ));
            }
            
            // Check timeout
            if let Some(timeout) = ctx.timeout_seconds {
                let elapsed = start_time.elapsed().as_secs();
                if elapsed >= timeout as u64 {
                    return Err(AgentError::Orchestration(
                        "Handoff orchestration timed out".to_string(),
                    ));
                }
            }
            
            // Get the current agent
            let agent = self.get_agent(&current_agent_id)
                .ok_or_else(|| AgentError::AgentNotFound(current_agent_id.clone()))?;
            
            let step_start = Instant::now();
            
            // Create the prompt with handoff instructions if enabled
            let prompt = if self.config.include_handoff_instructions {
                format!("{}{}", current_input, self.create_handoff_instructions(&current_agent_id))
            } else {
                current_input.clone()
            };
            
            // Execute the agent
            match agent.invoke_async(&mut state.thread, &prompt).await {
                Ok(response) => {
                    let step_time = step_start.elapsed().as_millis() as u64;
                    final_output = response.clone();
                    
                    // Check if the agent wants to hand off
                    if let Some(handoff_condition) = self.extract_handoff(&response.content) {
                        // Find the target agent for this handoff
                        if let Some(target_agent) = self.config.find_target(&current_agent_id, &handoff_condition) {
                            // Record the handoff step
                            let step = OrchestrationStep::success(
                                agent.id().to_string(),
                                agent.name().map(|s| s.to_string()),
                                current_input.clone(),
                                format!("HANDOFF to {} ({})", target_agent, handoff_condition),
                                step_time,
                            );
                            state.add_trace_step(step);
                            
                            // Update for next iteration
                            current_agent_id = target_agent.to_string();
                            current_input = input.to_string(); // Reset to original input for new agent
                            handoff_count += 1;
                            continue;
                        } else {
                            // Invalid handoff condition, treat as final response
                            let step = OrchestrationStep::success(
                                agent.id().to_string(),
                                agent.name().map(|s| s.to_string()),
                                current_input.clone(),
                                response.content.clone(),
                                step_time,
                            );
                            state.add_trace_step(step);
                            break;
                        }
                    } else {
                        // No handoff, this is the final response
                        let step = OrchestrationStep::success(
                            agent.id().to_string(),
                            agent.name().map(|s| s.to_string()),
                            current_input.clone(),
                            response.content.clone(),
                            step_time,
                        );
                        state.add_trace_step(step);
                        break;
                    }
                }
                Err(e) => {
                    let step_time = step_start.elapsed().as_millis() as u64;
                    
                    // Add failure step to trace
                    let step = OrchestrationStep::failure(
                        agent.id().to_string(),
                        agent.name().map(|s| s.to_string()),
                        current_input.clone(),
                        e.to_string(),
                        step_time,
                    );
                    state.add_trace_step(step);
                    
                    // Complete trace as failure and return error
                    if let Some(ref mut trace) = state.trace {
                        trace.complete_failure(start_time.elapsed().as_millis() as u64);
                    }
                    
                    return Err(AgentError::Orchestration(
                        format!("Agent {} failed in handoff orchestration: {}", agent.id(), e),
                    ));
                }
            }
        }
        
        // Complete the trace
        let total_time = start_time.elapsed().as_millis() as u64;
        if let Some(mut trace) = state.trace {
            trace.complete_success(total_time);
            Ok(OrchestrationResult::with_trace(
                final_output,
                current_agent_id,
                trace,
            ))
        } else {
            Ok(OrchestrationResult::new(final_output, current_agent_id))
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::chat_completion_agent::{ChatCompletionAgent, CustomerServiceAgent, TechnicalSupportAgent};
    use semantic_kernel::KernelBuilder;

    #[test]
    fn test_handoff_rule() {
        let rule = HandoffRule::new("agent1", "agent2", "TECHNICAL")
            .with_description("For technical issues");
        
        assert_eq!(rule.from_agent, "agent1");
        assert_eq!(rule.to_agent, "agent2");
        assert_eq!(rule.condition, "TECHNICAL");
        assert_eq!(rule.description, Some("For technical issues".to_string()));
    }
    
    #[test]
    fn test_handoff_config() {
        let config = HandoffConfig::new("customer_service")
            .add_rule(HandoffRule::new("customer_service", "technical_support", "TECHNICAL"))
            .add_rule(HandoffRule::new("customer_service", "billing", "BILLING"))
            .with_max_handoffs(5);
        
        assert_eq!(config.initial_agent, "customer_service");
        assert_eq!(config.max_handoffs, 5);
        assert_eq!(config.rules.len(), 2);
        
        let targets = config.get_targets("customer_service");
        assert_eq!(targets.len(), 2);
        
        let target = config.find_target("customer_service", "I have a technical problem");
        assert_eq!(target, Some("technical_support"));
        
        let target = config.find_target("customer_service", "billing issue");
        assert_eq!(target, Some("billing"));
    }
    
    #[tokio::test]
    async fn test_handoff_orchestration() {
        let kernel1 = KernelBuilder::new().build();
        let kernel2 = KernelBuilder::new().build();
        
        let cs_agent = Arc::new(CustomerServiceAgent::new(kernel1).unwrap()) as Arc<dyn Agent>;
        let tech_agent = Arc::new(TechnicalSupportAgent::new(kernel2).unwrap()) as Arc<dyn Agent>;
        
        let config = HandoffConfig::new("Customer Service Agent")
            .add_rule(HandoffRule::new(
                "Customer Service Agent",
                "Technical Support Agent", 
                "TECHNICAL"
            ));
        
        let orchestration = HandoffOrchestration::new(
            vec![cs_agent, tech_agent],
            config,
        ).unwrap();
        
        assert_eq!(orchestration.orchestration_type(), "Handoff");
        assert_eq!(orchestration.agents().len(), 2);
    }
    
    #[test]
    fn test_handoff_orchestration_invalid_config() {
        let kernel = KernelBuilder::new().build();
        let agent = Arc::new(ChatCompletionAgent::builder()
            .name("TestAgent")
            .kernel(kernel)
            .build()
            .unwrap()) as Arc<dyn Agent>;
        
        // Config with non-existent initial agent
        let config = HandoffConfig::new("NonExistentAgent");
        let result = HandoffOrchestration::new(vec![agent], config);
        assert!(result.is_err());
        match result {
            Err(e) => assert!(e.to_string().contains("not found")),
            Ok(_) => panic!("Expected error"),
        }
    }
    
    #[test]
    fn test_extract_handoff() {
        let kernel1 = KernelBuilder::new().build();
        let kernel2 = KernelBuilder::new().build();
        let cs_agent = Arc::new(CustomerServiceAgent::new(kernel1).unwrap()) as Arc<dyn Agent>;
        let tech_agent = Arc::new(TechnicalSupportAgent::new(kernel2).unwrap()) as Arc<dyn Agent>;
        
        let config = HandoffConfig::new("Customer Service Agent");
        let orchestration = HandoffOrchestration::new(
            vec![cs_agent, tech_agent],
            config,
        ).unwrap();
        
        // Test extracting handoff from response
        let response = "I can help with that. HANDOFF: TECHNICAL";
        let handoff = orchestration.extract_handoff(response);
        assert_eq!(handoff, Some("TECHNICAL".to_string()));
        
        let response = "This is a normal response without handoff.";
        let handoff = orchestration.extract_handoff(response);
        assert_eq!(handoff, None);
    }
    
    #[test]
    fn test_create_handoff_instructions() {
        let kernel1 = KernelBuilder::new().build();
        let kernel2 = KernelBuilder::new().build();
        let cs_agent = Arc::new(CustomerServiceAgent::new(kernel1).unwrap()) as Arc<dyn Agent>;
        let tech_agent = Arc::new(TechnicalSupportAgent::new(kernel2).unwrap()) as Arc<dyn Agent>;
        
        let config = HandoffConfig::new("Customer Service Agent")
            .add_rule(HandoffRule::new(
                "Customer Service Agent",
                "Technical Support Agent",
                "TECHNICAL"
            ).with_description("technical issues"));
        
        let orchestration = HandoffOrchestration::new(
            vec![cs_agent, tech_agent],
            config,
        ).unwrap();
        
        let instructions = orchestration.create_handoff_instructions("Customer Service Agent");
        assert!(instructions.contains("HANDOFF:"));
        assert!(instructions.contains("TECHNICAL"));
        assert!(instructions.contains("technical issues"));
    }
}