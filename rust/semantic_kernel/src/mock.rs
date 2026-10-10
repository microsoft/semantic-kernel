//! Mock LLM service for testing and examples

use std::collections::HashMap;
use crate::async_trait;
use crate::services::{AIService, ChatCompletionService};
use crate::content::{ChatMessage, ChatMessageContent, PromptExecutionSettings, AuthorRole};

/// Mock chat completion service for testing
pub struct MockChatCompletionService {
    attributes: HashMap<String, String>,
    responses: Vec<String>,
    current_index: std::sync::Mutex<usize>,
}

impl Default for MockChatCompletionService {
    fn default() -> Self {
        Self::new()
    }
}

impl MockChatCompletionService {
    /// Create a new mock service with predefined responses
    pub fn new() -> Self {
        let mut attributes = HashMap::new();
        attributes.insert("model".to_string(), "mock-gpt".to_string());
        attributes.insert("provider".to_string(), "mock".to_string());
        
        Self {
            attributes,
            responses: vec![
                "Hello! I'm a mock AI assistant. How can I help you today?".to_string(),
                "That's an interesting question! Let me think about it...".to_string(),
                "I understand what you're asking. Here's my response...".to_string(),
                "Thanks for the conversation! Is there anything else I can help with?".to_string(),
            ],
            current_index: std::sync::Mutex::new(0),
        }
    }

    /// Create a mock service with custom responses
    pub fn with_responses(responses: Vec<String>) -> Self {
        let mut attributes = HashMap::new();
        attributes.insert("model".to_string(), "mock-gpt".to_string());
        attributes.insert("provider".to_string(), "mock".to_string());
        
        Self {
            attributes,
            responses,
            current_index: std::sync::Mutex::new(0),
        }
    }

    /// Create an echo service that echoes the input
    pub fn echo() -> Self {
        Self::with_responses(vec!["Echo: {input}".to_string()])
    }
}

#[async_trait]
impl AIService for MockChatCompletionService {
    fn attributes(&self) -> &HashMap<String, String> {
        &self.attributes
    }

    fn service_type(&self) -> &'static str {
        "ChatCompletion"
    }
}

#[async_trait]
impl ChatCompletionService for MockChatCompletionService {
    async fn get_chat_message_content(
        &self,
        messages: &[ChatMessage],
        _execution_settings: Option<&PromptExecutionSettings>,
    ) -> crate::Result<ChatMessageContent> {
        let mut index_guard = self.current_index.lock().unwrap();
        let response = if self.responses.is_empty() {
            "Mock response".to_string()
        } else if self.responses.len() == 1 && self.responses[0].contains("{input}") {
            // Echo mode
            let last_user_message = messages
                .iter()
                .rev()
                .find(|m| m.role == AuthorRole::User)
                .map(|m| m.content.as_str())
                .unwrap_or("Hello");
            self.responses[0].replace("{input}", last_user_message)
        } else {
            // Cycle through predefined responses
            let response = self.responses[*index_guard % self.responses.len()].clone();
            *index_guard += 1;
            response
        };

        Ok(ChatMessageContent::new(AuthorRole::Assistant, response)
            .with_model_id("mock-gpt")
            .with_metadata("provider", "mock"))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::content::ChatMessage;

    #[tokio::test]
    async fn test_mock_service() {
        let service = MockChatCompletionService::new();
        let messages = vec![ChatMessage::user("Hello")];
        
        let result = service.get_chat_message_content(&messages, None).await.unwrap();
        assert_eq!(result.role, AuthorRole::Assistant);
        assert!(!result.content.is_empty());
    }

    #[tokio::test]
    async fn test_echo_service() {
        let service = MockChatCompletionService::echo();
        let messages = vec![ChatMessage::user("Hello, world!")];
        
        let result = service.get_chat_message_content(&messages, None).await.unwrap();
        assert_eq!(result.content, "Echo: Hello, world!");
    }
}