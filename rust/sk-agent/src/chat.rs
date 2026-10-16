//! Agent chat abstractions

use crate::agent::Agent;
use crate::errors::{AgentError, Result};
use async_trait::async_trait;
use std::sync::Arc;

/// Provides a point of interaction for one or more agents.
/// 
/// AgentChat instances manage multi-agent conversations and don't support
/// concurrent invocation. They will return an error if concurrent activity
/// is attempted for any public method.
#[async_trait]
pub trait AgentChat: Send + Sync {
    /// Gets the agents participating in the chat.
    fn agents(&self) -> &[Arc<dyn Agent>];
    
    /// Gets a value that indicates whether a chat operation is active.
    fn is_active(&self) -> bool;
    
    /// Adds a message to the chat and processes it through the agents.
    async fn add_chat_message(&mut self, message: &str) -> Result<Vec<String>>;
}

/// A simple implementation of AgentChat for basic multi-agent conversations.
pub struct SimpleAgentChat {
    agents: Vec<Arc<dyn Agent>>,
    is_active: bool,
}

impl SimpleAgentChat {
    /// Creates a new simple agent chat with the given agents.
    pub fn new(agents: Vec<Arc<dyn Agent>>) -> Self {
        Self {
            agents,
            is_active: false,
        }
    }
}

#[async_trait]
impl AgentChat for SimpleAgentChat {
    fn agents(&self) -> &[Arc<dyn Agent>] {
        &self.agents
    }
    
    fn is_active(&self) -> bool {
        self.is_active
    }
    
    async fn add_chat_message(&mut self, message: &str) -> Result<Vec<String>> {
        if self.is_active {
            return Err(AgentError::ConcurrentAccess(
                "Chat is already active".to_string()
            ));
        }
        
        self.is_active = true;
        
        // Simple implementation: each agent processes the message
        let mut responses = Vec::new();
        for agent in &self.agents {
            let mut thread = agent.create_thread();
            let response = agent.invoke_async(&mut thread, message).await?;
            responses.push(response.content);
        }
        
        self.is_active = false;
        Ok(responses)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::chat_completion_agent::ChatCompletionAgent;
    use semantic_kernel::KernelBuilder;

    #[tokio::test]
    async fn test_simple_agent_chat() {
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
        
        let mut chat = SimpleAgentChat::new(vec![agent1, agent2]);
        assert_eq!(chat.agents().len(), 2);
        assert!(!chat.is_active());
        
        let responses = chat.add_chat_message("Hello").await.unwrap();
        assert_eq!(responses.len(), 2);
        assert!(!chat.is_active());
    }
}