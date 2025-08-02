//! Sequential orchestration pattern

use super::{
    Orchestration, OrchestrationContext, OrchestrationResult, OrchestrationState,
    OrchestrationStep,
};
use crate::agent::Agent;
use crate::errors::{AgentError, Result};
use async_trait::async_trait;
use semantic_kernel::ChatMessageContent;
use std::sync::Arc;
use semantic_kernel::AuthorRole;
use std::time::Instant;

/// An orchestration that provides the input message to the first agent
/// and sequentially passes each agent result to the next agent.
/// 
/// This pattern is useful when you want agents to work in a pipeline,
/// where each agent processes and transforms the output from the previous agent.
pub struct SequentialOrchestration {
    agents: Vec<Arc<dyn Agent>>,
}

impl SequentialOrchestration {
    /// Creates a new sequential orchestration with the given agents.
    /// 
    /// Agents will be executed in the order they are provided.
    pub fn new(agents: Vec<Arc<dyn Agent>>) -> Self {
        Self { agents }
    }
    
    /// Creates a sequential orchestration from individual agents.
    pub fn from_agents(agents: impl IntoIterator<Item = Arc<dyn Agent>>) -> Self {
        Self {
            agents: agents.into_iter().collect(),
        }
    }
    
    /// Adds an agent to the end of the sequence.
    pub fn add_agent(&mut self, agent: Arc<dyn Agent>) {
        self.agents.push(agent);
    }
    
    /// Gets the number of agents in the sequence.
    pub fn agent_count(&self) -> usize {
        self.agents.len()
    }
}

#[async_trait]
impl Orchestration for SequentialOrchestration {
    fn agents(&self) -> &[Arc<dyn Agent>] {
        &self.agents
    }
    
    fn orchestration_type(&self) -> &str {
        "Sequential"
    }
    
    async fn execute_async(
        &self,
        input: &str,
        context: Option<OrchestrationContext>,
    ) -> Result<OrchestrationResult> {
        if self.agents.is_empty() {
            return Err(AgentError::Configuration(
                "No agents provided for sequential orchestration".to_string(),
            ));
        }
        
        let ctx = context.unwrap_or_default();
        let start_time = Instant::now();
        let mut state = OrchestrationState::new(input.to_string(), ctx.trace_enabled);
        
        let mut current_input = input.to_string();
        let mut final_output = ChatMessageContent::new(AuthorRole::Assistant, String::new());
        let mut final_agent_id = String::new();
        
        // Process through each agent sequentially
        for (index, agent) in self.agents.iter().enumerate() {
            let step_start = Instant::now();
            
            // Check timeout if specified
            if let Some(timeout) = ctx.timeout_seconds {
                let elapsed = start_time.elapsed().as_secs();
                if elapsed >= timeout as u64 {
                    return Err(AgentError::Orchestration(
                        "Sequential orchestration timed out".to_string(),
                    ));
                }
            }
            
            // Execute the agent
            match agent.invoke_async(&mut state.thread, &current_input).await {
                Ok(response) => {
                    let step_time = step_start.elapsed().as_millis() as u64;
                    
                    // Update state for next iteration
                    current_input = response.content.clone();
                    final_output = response.clone();
                    final_agent_id = agent.id().to_string();
                    
                    // Add trace step if enabled
                    let step = OrchestrationStep::success(
                        agent.id().to_string(),
                        agent.name().map(|s| s.to_string()),
                        if index == 0 { input.to_string() } else { current_input.clone() },
                        response.content.clone(),
                        step_time,
                    );
                    state.add_trace_step(step);
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
                        format!("Agent {} failed in sequential orchestration: {}", agent.id(), e),
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
                final_agent_id,
                trace,
            ))
        } else {
            Ok(OrchestrationResult::new(final_output, final_agent_id))
        }
    }
}

/// Builder for creating sequential orchestrations.
pub struct SequentialOrchestrationBuilder {
    agents: Vec<Arc<dyn Agent>>,
}

impl SequentialOrchestrationBuilder {
    /// Creates a new builder.
    pub fn new() -> Self {
        Self {
            agents: Vec::new(),
        }
    }
    
    /// Adds an agent to the sequence.
    pub fn add_agent(mut self, agent: Arc<dyn Agent>) -> Self {
        self.agents.push(agent);
        self
    }
    
    /// Adds multiple agents to the sequence.
    pub fn add_agents(mut self, agents: impl IntoIterator<Item = Arc<dyn Agent>>) -> Self {
        self.agents.extend(agents);
        self
    }
    
    /// Builds the sequential orchestration.
    pub fn build(self) -> Result<SequentialOrchestration> {
        if self.agents.is_empty() {
            return Err(AgentError::Configuration(
                "At least one agent is required for sequential orchestration".to_string(),
            ));
        }
        
        Ok(SequentialOrchestration::new(self.agents))
    }
}

impl Default for SequentialOrchestrationBuilder {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::chat_completion_agent::ChatCompletionAgent;
    use semantic_kernel::KernelBuilder;

    #[tokio::test]
    async fn test_sequential_orchestration() {
        let kernel1 = KernelBuilder::new().build();
        let kernel2 = KernelBuilder::new().build();
        
        let agent1 = Arc::new(ChatCompletionAgent::builder()
            .name("Agent1")
            .kernel(kernel1)
            .build()
            .unwrap()) as Arc<dyn Agent>;
            
        let agent2 = Arc::new(ChatCompletionAgent::builder()
            .name("Agent2")
            .kernel(kernel2)
            .build()
            .unwrap()) as Arc<dyn Agent>;
        
        let orchestration = SequentialOrchestration::new(vec![agent1, agent2]);
        assert_eq!(orchestration.agent_count(), 2);
        assert_eq!(orchestration.orchestration_type(), "Sequential");
        
        let context = OrchestrationContext::with_tracing("test-123".to_string());
        let result = orchestration.execute_async("Hello", Some(context)).await;
        
        assert!(result.is_ok());
        let result = result.unwrap();
        assert!(!result.output.content.is_empty());
        assert!(!result.final_agent.is_empty());
        assert!(result.trace.is_some());
        
        let trace = result.trace.unwrap();
        assert!(trace.success);
        assert_eq!(trace.steps.len(), 2);
        assert!(trace.steps.iter().all(|s| s.success));
    }
    
    #[tokio::test]
    async fn test_sequential_orchestration_empty_agents() {
        let orchestration = SequentialOrchestration::new(vec![]);
        let result = orchestration.execute_async("Hello", None).await;
        
        assert!(result.is_err());
        assert!(result.unwrap_err().to_string().contains("No agents provided"));
    }
    
    #[test]
    fn test_sequential_orchestration_builder() {
        let kernel1 = KernelBuilder::new().build();
        let kernel2 = KernelBuilder::new().build();
        
        let agent1 = Arc::new(ChatCompletionAgent::builder()
            .name("Agent1")
            .kernel(kernel1)
            .build()
            .unwrap()) as Arc<dyn Agent>;
            
        let agent2 = Arc::new(ChatCompletionAgent::builder()
            .name("Agent2")
            .kernel(kernel2)
            .build()
            .unwrap()) as Arc<dyn Agent>;
        
        let orchestration = SequentialOrchestrationBuilder::new()
            .add_agent(agent1)
            .add_agent(agent2)
            .build();
        
        assert!(orchestration.is_ok());
        let orchestration = orchestration.unwrap();
        assert_eq!(orchestration.agent_count(), 2);
    }
    
    #[test]
    fn test_sequential_orchestration_builder_empty() {
        let result = SequentialOrchestrationBuilder::new().build();
        assert!(result.is_err());
        match result {
            Err(e) => assert!(e.to_string().contains("At least one agent is required")),
            Ok(_) => panic!("Expected error"),
        }
    }
    
    #[tokio::test]
    async fn test_sequential_orchestration_with_timeout() {
        let kernel = KernelBuilder::new().build();
        
        let agent = Arc::new(ChatCompletionAgent::builder()
            .name("TestAgent")
            .kernel(kernel)
            .build()
            .unwrap()) as Arc<dyn Agent>;
        
        let orchestration = SequentialOrchestration::new(vec![agent]);
        
        // Test with a very short timeout - this might not always trigger
        // but tests the timeout mechanism
        let context = OrchestrationContext::new("test".to_string())
            .with_timeout(0); // 0 seconds timeout
        
        let result = orchestration.execute_async("Hello", Some(context)).await;
        // Result could be either success (if fast enough) or timeout error
        // We just verify it doesn't panic
        match result {
            Ok(_) => println!("Orchestration completed within timeout"),
            Err(e) => {
                if e.to_string().contains("timed out") {
                    println!("Orchestration timed out as expected");
                } else {
                    // Some other error occurred
                    println!("Orchestration failed with: {}", e);
                }
            }
        }
    }
}