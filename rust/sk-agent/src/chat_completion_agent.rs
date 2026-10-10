//! Chat completion agent implementation

use crate::agent::{Agent, AgentBuilder, AgentProperties};
use crate::channel::{AgentChannel, ChatCompletionChannel};
use crate::errors::{AgentError, Result};
use crate::thread::AgentThread;
use async_trait::async_trait;
use semantic_kernel::{
    ChatMessageContent, Kernel, AuthorRole,
    PromptExecutionSettings
};
use std::sync::Arc;

/// A chat completion agent that uses LLM services for conversation.
/// 
/// This agent leverages chat completion services (like OpenAI GPT) to
/// generate responses. It manages conversation context and can be
/// configured with custom instructions and behavior.
pub struct ChatCompletionAgent {
    properties: AgentProperties,
    kernel: Arc<Kernel>,
    channel: Arc<dyn AgentChannel>,
    model_id: String,
    execution_settings: PromptExecutionSettings,
}

impl ChatCompletionAgent {
    /// Creates a new builder for configuring a chat completion agent.
    pub fn builder() -> ChatCompletionAgentBuilder {
        ChatCompletionAgentBuilder::new()
    }
    
    /// Gets the model ID used by this agent.
    pub fn model_id(&self) -> &str {
        &self.model_id
    }
    
    /// Gets the execution settings for this agent.
    pub fn execution_settings(&self) -> &PromptExecutionSettings {
        &self.execution_settings
    }
}

#[async_trait]
impl Agent for ChatCompletionAgent {
    fn id(&self) -> &str {
        &self.properties.id
    }
    
    fn name(&self) -> Option<&str> {
        self.properties.name.as_deref()
    }
    
    fn description(&self) -> Option<&str> {
        self.properties.description.as_deref()
    }
    
    fn instructions(&self) -> Option<&str> {
        self.properties.instructions.as_deref()
    }
    
    fn kernel(&self) -> &Kernel {
        &self.kernel
    }
    
    fn channel(&self) -> Arc<dyn AgentChannel> {
        self.channel.clone()
    }
    
    async fn invoke_async(
        &self,
        thread: &mut AgentThread,
        message: &str,
    ) -> Result<ChatMessageContent> {
        // Create input message
        let input = ChatMessageContent::new(AuthorRole::User, message.to_string());
        
        // Use the channel to process the message
        let response = self.channel
            .invoke_async(thread, &input, self.instructions())
            .await?;
        
        Ok(response)
    }
    
    async fn invoke_streaming_async(
        &self,
        thread: &mut AgentThread,
        message: &str,
    ) -> Result<Vec<ChatMessageContent>> {
        // Create input message
        let input = ChatMessageContent::new(AuthorRole::User, message.to_string());
        
        // Use the channel to process the message with streaming
        let responses = self.channel
            .invoke_streaming_async(thread, &input, self.instructions())
            .await?;
        
        Ok(responses)
    }
}

/// Builder for creating ChatCompletionAgent instances.
pub struct ChatCompletionAgentBuilder {
    base_builder: AgentBuilder,
    kernel: Option<Kernel>,
    model_id: Option<String>,
    execution_settings: Option<PromptExecutionSettings>,
}

impl ChatCompletionAgentBuilder {
    /// Creates a new builder.
    pub fn new() -> Self {
        Self {
            base_builder: AgentBuilder::new(),
            kernel: None,
            model_id: None,
            execution_settings: None,
        }
    }
    
    /// Sets the agent ID.
    pub fn id(mut self, id: impl Into<String>) -> Self {
        self.base_builder = self.base_builder.id(id);
        self
    }
    
    /// Sets the agent name.
    pub fn name(mut self, name: impl Into<String>) -> Self {
        self.base_builder = self.base_builder.name(name);
        self
    }
    
    /// Sets the agent description.
    pub fn description(mut self, description: impl Into<String>) -> Self {
        self.base_builder = self.base_builder.description(description);
        self
    }
    
    /// Sets the agent instructions.
    pub fn instructions(mut self, instructions: impl Into<String>) -> Self {
        self.base_builder = self.base_builder.instructions(instructions);
        self
    }
    
    /// Sets the kernel to use.
    pub fn kernel(mut self, kernel: Kernel) -> Self {
        self.kernel = Some(kernel);
        self
    }
    
    /// Sets the model ID.
    pub fn model_id(mut self, model_id: impl Into<String>) -> Self {
        self.model_id = Some(model_id.into());
        self
    }
    
    /// Sets the execution settings.
    pub fn execution_settings(mut self, settings: PromptExecutionSettings) -> Self {
        self.execution_settings = Some(settings);
        self
    }
    
    /// Builds the ChatCompletionAgent.
    pub fn build(self) -> Result<ChatCompletionAgent> {
        let kernel = self.kernel
            .ok_or_else(|| AgentError::Configuration("Kernel is required".to_string()))?;
        
        let model_id = self.model_id
            .unwrap_or_else(|| "gpt-4".to_string());
        
        let execution_settings = self.execution_settings
            .unwrap_or_default();
        
        let properties = AgentProperties::from_builder(&self.base_builder);
        
        // Create the channel - share the kernel with the channel
        let kernel_arc = Arc::new(kernel);
        let channel = Arc::new(ChatCompletionChannel::new(
            model_id.clone(),
            "chat_completion",
            kernel_arc.clone()
        ));
        
        Ok(ChatCompletionAgent {
            properties,
            kernel: kernel_arc,
            channel,
            model_id,
            execution_settings,
        })
    }
}

impl Default for ChatCompletionAgentBuilder {
    fn default() -> Self {
        Self::new()
    }
}

/// A specialized agent for customer service scenarios.
pub struct CustomerServiceAgent {
    inner: ChatCompletionAgent,
}

impl CustomerServiceAgent {
    /// Creates a new customer service agent.
    pub fn new(kernel: Kernel) -> Result<Self> {
        let inner = ChatCompletionAgent::builder()
            .name("Customer Service Agent")
            .description("A helpful customer service assistant")
            .instructions(
                "You are a professional customer service representative. \
                 Be helpful, polite, and try to resolve customer issues. \
                 If you cannot help with something, politely explain and \
                 suggest contacting a human representative."
            )
            .kernel(kernel)
            .build()?;
        
        Ok(Self { inner })
    }
}

#[async_trait]
impl Agent for CustomerServiceAgent {
    fn id(&self) -> &str {
        self.inner.id()
    }
    
    fn name(&self) -> Option<&str> {
        self.inner.name()
    }
    
    fn description(&self) -> Option<&str> {
        self.inner.description()
    }
    
    fn instructions(&self) -> Option<&str> {
        self.inner.instructions()
    }
    
    fn kernel(&self) -> &Kernel {
        self.inner.kernel()
    }
    
    fn channel(&self) -> Arc<dyn AgentChannel> {
        self.inner.channel()
    }
    
    async fn invoke_async(
        &self,
        thread: &mut AgentThread,
        message: &str,
    ) -> Result<ChatMessageContent> {
        self.inner.invoke_async(thread, message).await
    }
    
    async fn invoke_streaming_async(
        &self,
        thread: &mut AgentThread,
        message: &str,
    ) -> Result<Vec<ChatMessageContent>> {
        self.inner.invoke_streaming_async(thread, message).await
    }
}

/// A specialized agent for technical support scenarios.
pub struct TechnicalSupportAgent {
    inner: ChatCompletionAgent,
}

impl TechnicalSupportAgent {
    /// Creates a new technical support agent.
    pub fn new(kernel: Kernel) -> Result<Self> {
        let inner = ChatCompletionAgent::builder()
            .name("Technical Support Agent")
            .description("A knowledgeable technical support specialist")
            .instructions(
                "You are a technical support specialist. Help users with \
                 technical problems by providing clear, step-by-step solutions. \
                 Ask clarifying questions when needed and always prioritize \
                 user safety. If a problem is too complex, recommend escalation \
                 to a senior technician."
            )
            .kernel(kernel)
            .build()?;
        
        Ok(Self { inner })
    }
}

#[async_trait]
impl Agent for TechnicalSupportAgent {
    fn id(&self) -> &str {
        self.inner.id()
    }
    
    fn name(&self) -> Option<&str> {
        self.inner.name()
    }
    
    fn description(&self) -> Option<&str> {
        self.inner.description()
    }
    
    fn instructions(&self) -> Option<&str> {
        self.inner.instructions()
    }
    
    fn kernel(&self) -> &Kernel {
        self.inner.kernel()
    }
    
    fn channel(&self) -> Arc<dyn AgentChannel> {
        self.inner.channel()
    }
    
    async fn invoke_async(
        &self,
        thread: &mut AgentThread,
        message: &str,
    ) -> Result<ChatMessageContent> {
        self.inner.invoke_async(thread, message).await
    }
    
    async fn invoke_streaming_async(
        &self,
        thread: &mut AgentThread,
        message: &str,
    ) -> Result<Vec<ChatMessageContent>> {
        self.inner.invoke_streaming_async(thread, message).await
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use semantic_kernel::KernelBuilder;

    #[test]
    fn test_chat_completion_agent_builder() {
        let kernel = KernelBuilder::new().build();
        
        let agent = ChatCompletionAgent::builder()
            .name("Test Agent")
            .description("A test agent")
            .instructions("Be helpful")
            .model_id("gpt-4")
            .kernel(kernel)
            .build();
        
        assert!(agent.is_ok());
        let agent = agent.unwrap();
        assert_eq!(agent.name(), Some("Test Agent"));
        assert_eq!(agent.description(), Some("A test agent"));
        assert_eq!(agent.instructions(), Some("Be helpful"));
        assert_eq!(agent.model_id(), "gpt-4");
    }
    
    #[test]
    fn test_chat_completion_agent_builder_missing_kernel() {
        let result = ChatCompletionAgent::builder()
            .name("Test Agent")
            .build();
        
        assert!(result.is_err());
        match result {
            Err(e) => assert!(e.to_string().contains("Kernel is required")),
            Ok(_) => panic!("Expected error"),
        }
    }
    
    #[tokio::test]
    async fn test_chat_completion_agent_invoke() {
        let kernel = KernelBuilder::new().build();
        let agent = ChatCompletionAgent::builder()
            .name("Test Agent")
            .kernel(kernel)
            .build()
            .unwrap();
        
        let mut thread = AgentThread::new();
        let result = agent.invoke_async(&mut thread, "Hello").await;
        
        assert!(result.is_ok());
        let response = result.unwrap();
        assert!(!response.content.is_empty());
    }
    
    #[test]
    fn test_customer_service_agent() {
        let kernel = KernelBuilder::new().build();
        let agent = CustomerServiceAgent::new(kernel);
        
        assert!(agent.is_ok());
        let agent = agent.unwrap();
        assert_eq!(agent.name(), Some("Customer Service Agent"));
        assert!(agent.instructions().unwrap().contains("customer service"));
    }
    
    #[test]
    fn test_technical_support_agent() {
        let kernel = KernelBuilder::new().build();
        let agent = TechnicalSupportAgent::new(kernel);
        
        assert!(agent.is_ok());
        let agent = agent.unwrap();
        assert_eq!(agent.name(), Some("Technical Support Agent"));
        assert!(agent.instructions().unwrap().contains("technical support"));
    }
}