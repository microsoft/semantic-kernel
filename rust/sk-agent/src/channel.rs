//! Agent communication channel abstractions

use crate::errors::Result;
use crate::thread::AgentThread;
use async_trait::async_trait;
use semantic_kernel::{ChatMessageContent, Kernel};
use std::sync::Arc;

/// Defines the communication protocol for agents.
/// 
/// Each agent must specify how it communicates via an `AgentChannel`.
/// The channel manages the formatting and transmission of messages
/// between agents and the underlying AI services.
#[async_trait]
pub trait AgentChannel: Send + Sync {
    /// Gets the unique identifier for this channel type.
    fn channel_type(&self) -> &str;
    
    /// Processes an input message and generates a response.
    ///
    /// # Arguments
    /// * `thread` - The conversation thread for context
    /// * `input` - The input message to process
    /// * `instructions` - Optional agent instructions
    ///
    /// # Returns
    /// The response message from the channel
    async fn invoke_async(
        &self,
        thread: &mut AgentThread,
        input: &ChatMessageContent,
        instructions: Option<&str>,
    ) -> Result<ChatMessageContent>;
    
    /// Processes an input message and generates a streaming response.
    ///
    /// # Arguments
    /// * `thread` - The conversation thread for context
    /// * `input` - The input message to process
    /// * `instructions` - Optional agent instructions
    ///
    /// # Returns
    /// A stream of response chunks
    async fn invoke_streaming_async(
        &self,
        thread: &mut AgentThread,
        input: &ChatMessageContent,
        instructions: Option<&str>,
    ) -> Result<Vec<ChatMessageContent>> {
        // Default implementation calls non-streaming version
        let response = self.invoke_async(thread, input, instructions).await?;
        Ok(vec![response])
    }
    
    /// Creates a hash identifier for this channel configuration.
    /// 
    /// This is used to identify compatible channels for agent grouping.
    fn get_hash(&self) -> String;
}

/// A channel that uses chat completion services for communication.
pub struct ChatCompletionChannel {
    model_id: String,
    service_type: String,
    kernel: Arc<Kernel>,
}

impl ChatCompletionChannel {
    /// Creates a new chat completion channel.
    pub fn new(model_id: impl Into<String>, service_type: impl Into<String>, kernel: Arc<Kernel>) -> Self {
        Self {
            model_id: model_id.into(),
            service_type: service_type.into(),
            kernel,
        }
    }
}

#[async_trait]
impl AgentChannel for ChatCompletionChannel {
    fn channel_type(&self) -> &str {
        "ChatCompletion"
    }
    
    async fn invoke_async(
        &self,
        thread: &mut AgentThread,
        input: &ChatMessageContent,
        instructions: Option<&str>,
    ) -> Result<ChatMessageContent> {
        // Get the chat history from the thread
        let mut history = thread.get_chat_history().clone();
        
        // Add system message with instructions if provided
        if let Some(instr) = instructions {
            use semantic_kernel::{ChatMessage, AuthorRole};
            let system_message = ChatMessage::system(instr);
            history.add_message(system_message);
        }
        
        // Add the input message
        use semantic_kernel::{ChatMessage, AuthorRole};
        let user_message = ChatMessage::user(&input.content);
        history.add_message(user_message);
        
        // Update thread history
        thread.add_message(input.clone())?;
        
        // Use kernel to get real chat completion response
        let response = self.kernel.invoke_chat_async(&history, None).await
            .map_err(|e| crate::errors::AgentError::Kernel(format!("Kernel invocation failed: {}", e)))?;
        
        // Add response to thread
        thread.add_message(response.clone())?;
        
        Ok(response)
    }
    
    fn get_hash(&self) -> String {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};
        
        let mut hasher = DefaultHasher::new();
        self.model_id.hash(&mut hasher);
        self.service_type.hash(&mut hasher);
        format!("{:x}", hasher.finish())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::thread::AgentThread;
    use semantic_kernel::{ChatMessageContent, KernelBuilder, mock::MockChatCompletionService};

    #[tokio::test]
    async fn test_chat_completion_channel() {
        // Create a mock kernel for testing
        let kernel = Arc::new(KernelBuilder::new()
            .add_chat_completion_service(MockChatCompletionService::echo())
            .build());
            
        let channel = ChatCompletionChannel::new("gpt-4", "openai", kernel);
        assert_eq!(channel.channel_type(), "ChatCompletion");
        
        let mut thread = AgentThread::new();
        let input = ChatMessageContent::new(semantic_kernel::AuthorRole::User, "Hello, world!");
        
        let result = channel.invoke_async(&mut thread, &input, Some("Be helpful")).await;
        assert!(result.is_ok());
        
        let response = result.unwrap();
        // With mock service, it will echo the input
        assert!(response.content.contains("Hello, world!"));
        
        // Check that messages were added to thread
        assert_eq!(thread.get_chat_history().messages.len(), 2); // input + response
    }
    
    #[test]
    fn test_channel_hash() {
        // Create mock kernels for testing
        let kernel = Arc::new(KernelBuilder::new()
            .add_chat_completion_service(MockChatCompletionService::echo())
            .build());
            
        let channel1 = ChatCompletionChannel::new("gpt-4", "openai", kernel.clone());
        let channel2 = ChatCompletionChannel::new("gpt-4", "openai", kernel.clone());
        let channel3 = ChatCompletionChannel::new("gpt-3.5", "openai", kernel);
        
        assert_eq!(channel1.get_hash(), channel2.get_hash());
        assert_ne!(channel1.get_hash(), channel3.get_hash());
    }
}