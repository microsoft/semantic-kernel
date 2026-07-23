//! Agent Chat Example - Customer Service with Handoff
//!
//! This example demonstrates two agents working together to handle a customer request.
//! The customer service agent initially handles the request and can hand off to a
//! technical support agent when needed.

use anyhow::Result;
use semantic_kernel::KernelBuilder;
use sk_agent::{
    orchestration::{HandoffOrchestration, Orchestration},
    orchestration::handoff::{HandoffConfig, HandoffRule},
    chat_completion_agent::{CustomerServiceAgent, TechnicalSupportAgent},
    Agent,
};
use std::sync::Arc;
use tracing::{info, error};

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize logging
    tracing_subscriber::fmt::init();
    
    info!("Starting Agent Chat Example - Customer Service with Handoff");
    
    // Create kernels for each agent
    let cs_kernel = KernelBuilder::new().build();
    let tech_kernel = KernelBuilder::new().build();
    
    // Create specialized agents
    let customer_service = Arc::new(CustomerServiceAgent::new(cs_kernel)?) as Arc<dyn Agent>;
    let technical_support = Arc::new(TechnicalSupportAgent::new(tech_kernel)?) as Arc<dyn Agent>;
    
    info!("Created agents: {} and {}", 
          customer_service.name().unwrap_or("Unknown"),
          technical_support.name().unwrap_or("Unknown"));
    
    // Configure handoff rules
    let handoff_config = HandoffConfig::new("Customer Service Agent")
        .add_rule(HandoffRule::new(
            "Customer Service Agent",
            "Technical Support Agent",
            "TECHNICAL"
        ).with_description("technical issues, troubleshooting, or configuration problems"))
        .with_max_handoffs(3)
        .with_handoff_instructions(true);
    
    // Create handoff orchestration
    let orchestration = HandoffOrchestration::new(
        vec![customer_service, technical_support],
        handoff_config,
    )?;
    
    info!("Configured handoff orchestration with {} agents", 
          orchestration.agents().len());
    
    // Test scenarios
    let scenarios = vec![
        "Hello, I'm having trouble with my account login",
        "My application keeps crashing when I try to upload files",
        "I need help setting up my firewall configuration",
        "Can you help me understand my billing statement?",
        "My software won't start after the latest update",
    ];
    
    for (i, scenario) in scenarios.iter().enumerate() {
        info!("\n=== Scenario {} ===", i + 1);
        info!("Customer: {}", scenario);
        
        match orchestration.execute_async(scenario, None).await {
            Ok(result) => {
                info!("Final Agent: {}", result.final_agent);
                info!("Response: {}", result.output.content);
                
                if let Some(trace) = result.trace {
                    info!("Execution trace:");
                    for (step_idx, step) in trace.steps.iter().enumerate() {
                        info!("  Step {}: {} -> {}", 
                              step_idx + 1,
                              step.agent_name.as_deref().unwrap_or(&step.agent_id),
                              if step.success { "SUCCESS" } else { "FAILED" });
                        if step.output.contains("HANDOFF") {
                            info!("    Handoff: {}", step.output);
                        }
                    }
                    info!("  Total time: {}ms", trace.total_time_ms);
                }
            }
            Err(e) => {
                error!("Failed to process scenario {}: {}", i + 1, e);
            }
        }
        
        // Add delay between scenarios
        tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;
    }
    
    info!("\nAgent Chat Example completed successfully!");
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use sk_agent::orchestration::{OrchestrationContext, handoff::{HandoffConfig, HandoffRule}};
    
    #[tokio::test]
    async fn test_agent_handoff_scenarios() {
        // Create agents
        let cs_kernel = KernelBuilder::new().build();
        let tech_kernel = KernelBuilder::new().build();
        
        let customer_service = Arc::new(CustomerServiceAgent::new(cs_kernel).unwrap()) as Arc<dyn Agent>;
        let technical_support = Arc::new(TechnicalSupportAgent::new(tech_kernel).unwrap()) as Arc<dyn Agent>;
        
        // Configure handoff
        let config = HandoffConfig::new("Customer Service Agent")
            .add_rule(HandoffRule::new(
                "Customer Service Agent",
                "Technical Support Agent",
                "TECHNICAL"
            ));
            
        let orchestration = HandoffOrchestration::new(
            vec![customer_service, technical_support],
            config,
        ).unwrap();
        
        // Test basic functionality
        let context = OrchestrationContext::with_tracing("test-handoff".to_string());
        let result = orchestration.execute_async(
            "I need help with a technical issue", 
            Some(context)
        ).await;
        
        assert!(result.is_ok());
        let result = result.unwrap();
        assert!(!result.output.content.is_empty());
        assert!(result.trace.is_some());
    }
    
    #[tokio::test]
    async fn test_agent_creation() {
        let kernel1 = KernelBuilder::new().build();
        let kernel2 = KernelBuilder::new().build();
        
        let cs_agent = CustomerServiceAgent::new(kernel1);
        assert!(cs_agent.is_ok());
        
        let tech_agent = TechnicalSupportAgent::new(kernel2);
        assert!(tech_agent.is_ok());
        
        let cs = cs_agent.unwrap();
        assert_eq!(cs.name(), Some("Customer Service Agent"));
        
        let tech = tech_agent.unwrap();
        assert_eq!(tech.name(), Some("Technical Support Agent"));
    }
}