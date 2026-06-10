//! Core Agent abstraction

use crate::errors::Result;
use crate::thread::AgentThread;
use crate::channel::AgentChannel;
use async_trait::async_trait;
use semantic_kernel::{ChatMessageContent, Kernel};
use std::sync::Arc;
use uuid::Uuid;

/// Base abstraction for all Semantic Kernel agents.
/// 
/// An agent instance may participate in one or more conversations, or `AgentChat`.
/// A conversation may include one or more agents. In addition to identity and 
/// descriptive meta-data, an `Agent` must define its communication protocol, 
/// or `AgentChannel`.
#[async_trait]
pub trait Agent: Send + Sync {
    /// Gets the unique identifier of the agent.
    fn id(&self) -> &str;
    
    /// Gets the name of the agent (optional).
    fn name(&self) -> Option<&str>;
    
    /// Gets the description of the agent (optional).
    fn description(&self) -> Option<&str>;
    
    /// Gets the instructions for the agent (optional).
    fn instructions(&self) -> Option<&str>;
    
    /// Gets the kernel associated with this agent.
    fn kernel(&self) -> &Kernel;
    
    /// Gets the communication channel for this agent.
    fn channel(&self) -> Arc<dyn AgentChannel>;
    
    /// Invokes the agent with a message and returns the response.
    ///
    /// # Arguments
    /// * `thread` - The conversation thread to use for context
    /// * `message` - The input message to process
    ///
    /// # Returns
    /// The agent's response message
    async fn invoke_async(
        &self,
        thread: &mut AgentThread,
        message: &str,
    ) -> Result<ChatMessageContent>;
    
    /// Invokes the agent with a message and returns the response, with streaming support.
    ///
    /// # Arguments
    /// * `thread` - The conversation thread to use for context
    /// * `message` - The input message to process
    ///
    /// # Returns
    /// A stream of response chunks
    async fn invoke_streaming_async(
        &self,
        thread: &mut AgentThread,
        message: &str,
    ) -> Result<Vec<ChatMessageContent>> {
        // Default implementation calls non-streaming version
        let response = self.invoke_async(thread, message).await?;
        Ok(vec![response])
    }
    
    /// Creates a new conversation thread for this agent.
    fn create_thread(&self) -> AgentThread {
        AgentThread::new()
    }
}

/// Builder for creating agents with common properties.
#[derive(Default)]
pub struct AgentBuilder {
    id: Option<String>,
    name: Option<String>,
    description: Option<String>,
    instructions: Option<String>,
}

impl AgentBuilder {
    /// Creates a new agent builder.
    pub fn new() -> Self {
        Self::default()
    }
    
    /// Sets the agent ID.
    pub fn id(mut self, id: impl Into<String>) -> Self {
        self.id = Some(id.into());
        self
    }
    
    /// Sets the agent name.
    pub fn name(mut self, name: impl Into<String>) -> Self {
        self.name = Some(name.into());
        self
    }
    
    /// Sets the agent description.
    pub fn description(mut self, description: impl Into<String>) -> Self {
        self.description = Some(description.into());
        self
    }
    
    /// Sets the agent instructions.
    pub fn instructions(mut self, instructions: impl Into<String>) -> Self {
        self.instructions = Some(instructions.into());
        self
    }
    
    /// Gets the ID, generating one if not set.
    pub fn get_id(&self) -> String {
        self.id.clone().unwrap_or_else(|| Uuid::new_v4().to_string())
    }
    
    /// Gets the name.
    pub fn get_name(&self) -> Option<String> {
        self.name.clone()
    }
    
    /// Gets the description.
    pub fn get_description(&self) -> Option<String> {
        self.description.clone()
    }
    
    /// Gets the instructions.
    pub fn get_instructions(&self) -> Option<String> {
        self.instructions.clone()
    }
}

/// Common agent properties that can be shared across implementations.
#[derive(Debug, Clone)]
pub struct AgentProperties {
    pub id: String,
    pub name: Option<String>,
    pub description: Option<String>,
    pub instructions: Option<String>,
}

impl AgentProperties {
    /// Creates new agent properties from a builder.
    pub fn from_builder(builder: &AgentBuilder) -> Self {
        Self {
            id: builder.get_id(),
            name: builder.get_name(),
            description: builder.get_description(),
            instructions: builder.get_instructions(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_agent_builder() {
        let builder = AgentBuilder::new()
            .name("Test Agent")
            .description("A test agent")
            .instructions("Be helpful");
        
        assert_eq!(builder.get_name(), Some("Test Agent".to_string()));
        assert_eq!(builder.get_description(), Some("A test agent".to_string()));
        assert_eq!(builder.get_instructions(), Some("Be helpful".to_string()));
        
        // ID should be generated if not set
        let id = builder.get_id();
        assert!(!id.is_empty());
        assert!(Uuid::parse_str(&id).is_ok());
    }
    
    #[test]
    fn test_agent_builder_with_id() {
        let builder = AgentBuilder::new()
            .id("custom-id")
            .name("Test Agent");
        
        assert_eq!(builder.get_id(), "custom-id");
        assert_eq!(builder.get_name(), Some("Test Agent".to_string()));
    }
    
    #[test]
    fn test_agent_properties_from_builder() {
        let builder = AgentBuilder::new()
            .name("Test Agent")
            .description("A test agent");
        
        let properties = AgentProperties::from_builder(&builder);
        assert_eq!(properties.name, Some("Test Agent".to_string()));
        assert_eq!(properties.description, Some("A test agent".to_string()));
        assert!(!properties.id.is_empty());
    }
}