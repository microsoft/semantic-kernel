//! OpenAI client implementation

use std::collections::HashMap;
use reqwest::Client;
use semantic_kernel::{
    async_trait,
    services::{AIService, ChatCompletionService, EmbeddingService},
    content::{ChatMessage as SKChatMessage, ChatMessageContent, PromptExecutionSettings, AuthorRole},
};

use crate::{
    models::{ChatCompletionRequest, ChatMessage, ChatCompletionResponse, ErrorResponse, EmbeddingRequest, EmbeddingResponse},
    error::{OpenAIError, Result},
    defaults, DEFAULT_BASE_URL,
};

/// OpenAI client for chat completions and embeddings
#[derive(Debug, Clone)]
pub struct OpenAIClient {
    /// HTTP client
    client: Client,
    /// API key
    api_key: String,
    /// Base URL for API requests
    base_url: String,
    /// Default model to use for chat completions
    model: String,
    /// Default model to use for embeddings
    embedding_model: String,
    /// Service attributes
    attributes: HashMap<String, String>,
}

impl OpenAIClient {
    /// Create a new OpenAI client
    pub fn new(api_key: impl Into<String>) -> Result<Self> {
        let api_key = api_key.into();
        if api_key.is_empty() {
            return Err(OpenAIError::MissingApiKey);
        }

        let mut attributes = HashMap::new();
        attributes.insert("provider".to_string(), "openai".to_string());
        attributes.insert("model".to_string(), defaults::CHAT_MODEL.to_string());
        attributes.insert("embedding_model".to_string(), defaults::EMBEDDING_MODEL.to_string());

        Ok(Self {
            client: Client::new(),
            api_key,
            base_url: DEFAULT_BASE_URL.to_string(),
            model: defaults::CHAT_MODEL.to_string(),
            embedding_model: defaults::EMBEDDING_MODEL.to_string(),
            attributes,
        })
    }

    /// Create a new OpenAI client with custom model
    pub fn with_model(api_key: impl Into<String>, model: impl Into<String>) -> Result<Self> {
        let mut client = Self::new(api_key)?;
        let model = model.into();
        client.model = model.clone();
        client.attributes.insert("model".to_string(), model);
        Ok(client)
    }

    /// Create a new OpenAI client with custom embedding model
    pub fn with_embedding_model(api_key: impl Into<String>, embedding_model: impl Into<String>) -> Result<Self> {
        let mut client = Self::new(api_key)?;
        let embedding_model = embedding_model.into();
        client.embedding_model = embedding_model.clone();
        client.attributes.insert("embedding_model".to_string(), embedding_model);
        Ok(client)
    }

    /// Create a new OpenAI client with custom base URL
    pub fn with_base_url(api_key: impl Into<String>, base_url: impl Into<String>) -> Result<Self> {
        let mut client = Self::new(api_key)?;
        client.base_url = base_url.into();
        Ok(client)
    }

    /// Create a new OpenAI client from environment variable
    pub fn from_env() -> Result<Self> {
        // Try to load from .env file
        let _ = dotenv::dotenv();
        
        let api_key = std::env::var("OPENAI_API_KEY")
            .map_err(|_| OpenAIError::MissingApiKey)?;
        Self::new(api_key)
    }

    /// Get the model being used
    pub fn model(&self) -> &str {
        &self.model
    }

    /// Get the embedding model being used
    pub fn embedding_model(&self) -> &str {
        &self.embedding_model
    }

    /// Set the model to use
    pub fn set_model(&mut self, model: impl Into<String>) {
        let model = model.into();
        self.model = model.clone();
        self.attributes.insert("model".to_string(), model);
    }

    /// Set the embedding model to use
    pub fn set_embedding_model(&mut self, embedding_model: impl Into<String>) {
        let embedding_model = embedding_model.into();
        self.embedding_model = embedding_model.clone();
        self.attributes.insert("embedding_model".to_string(), embedding_model);
    }

    /// Send a chat completion request
    pub async fn chat_completion(&self, request: ChatCompletionRequest) -> Result<ChatCompletionResponse> {
        let url = format!("{}/chat/completions", self.base_url);
        
        let response = self.client
            .post(&url)
            .header("Authorization", format!("Bearer {}", self.api_key))
            .header("Content-Type", "application/json")
            .json(&request)
            .send()
            .await?;

        if response.status().is_success() {
            let completion: ChatCompletionResponse = response.json().await?;
            Ok(completion)
        } else {
            let status = response.status();
            // Try to parse error response
            match response.json::<ErrorResponse>().await {
                Ok(error_response) => {
                    Err(OpenAIError::ApiError {
                        code: error_response.error.code.unwrap_or_else(|| status.to_string()),
                        message: error_response.error.message,
                    })
                },
                Err(_) => {
                    Err(OpenAIError::Other(format!("HTTP error: {}", status)))
                }
            }
        }
    }

    /// Send an embedding request
    pub async fn embeddings(&self, request: EmbeddingRequest) -> Result<EmbeddingResponse> {
        let url = format!("{}/embeddings", self.base_url);
        
        let response = self.client
            .post(&url)
            .header("Authorization", format!("Bearer {}", self.api_key))
            .header("Content-Type", "application/json")
            .json(&request)
            .send()
            .await?;

        if response.status().is_success() {
            let embedding_response: EmbeddingResponse = response.json().await?;
            Ok(embedding_response)
        } else {
            let status = response.status();
            // Try to parse error response
            match response.json::<ErrorResponse>().await {
                Ok(error_response) => {
                    Err(OpenAIError::ApiError {
                        code: error_response.error.code.unwrap_or_else(|| status.to_string()),
                        message: error_response.error.message,
                    })
                },
                Err(_) => {
                    Err(OpenAIError::Other(format!("HTTP error: {}", status)))
                }
            }
        }
    }

    /// Convert Semantic Kernel ChatMessage to OpenAI ChatMessage
    pub fn convert_sk_message_to_openai(message: &SKChatMessage) -> ChatMessage {
        let role = match message.role {
            AuthorRole::System => "system",
            AuthorRole::User => "user", 
            AuthorRole::Assistant => "assistant",
            AuthorRole::Tool => "tool",
        };

        ChatMessage {
            role: role.to_string(),
            content: message.content.clone(),
            name: None,
        }
    }

    /// Convert OpenAI ChatMessage to Semantic Kernel ChatMessageContent
    pub fn convert_openai_message_to_sk(message: &ChatMessage, model_id: Option<String>) -> ChatMessageContent {
        let role = match message.role.as_str() {
            "system" => AuthorRole::System,
            "user" => AuthorRole::User,
            "assistant" => AuthorRole::Assistant,
            "tool" => AuthorRole::Tool,
            _ => AuthorRole::Assistant, // Default fallback
        };

        let mut content = ChatMessageContent::new(role, &message.content);
        if let Some(model) = model_id {
            content = content.with_model_id(model);
        }
        content.with_metadata("provider", "openai")
    }
}

#[async_trait]
impl AIService for OpenAIClient {
    fn attributes(&self) -> &HashMap<String, String> {
        &self.attributes
    }

    fn service_type(&self) -> &'static str {
        "ChatCompletion,Embedding"
    }
}

#[async_trait]
impl ChatCompletionService for OpenAIClient {
    async fn get_chat_message_content(
        &self,
        messages: &[SKChatMessage],
        execution_settings: Option<&PromptExecutionSettings>,
    ) -> semantic_kernel::Result<ChatMessageContent> {
        // Convert SK messages to OpenAI format
        let openai_messages: Vec<ChatMessage> = messages
            .iter()
            .map(Self::convert_sk_message_to_openai)
            .collect();

        // Determine model to use
        let model = execution_settings
            .and_then(|s| s.model_id.as_ref())
            .unwrap_or(&self.model);

        // Build request
        let mut request = ChatCompletionRequest::new(model, openai_messages);

        // Apply execution settings
        if let Some(settings) = execution_settings {
            if let Some(max_tokens) = settings.max_tokens {
                request = request.with_max_tokens(max_tokens);
            }
            if let Some(temperature) = settings.temperature {
                request = request.with_temperature(temperature);
            }
            if let Some(top_p) = settings.top_p {
                request = request.with_top_p(top_p);
            }
        }

        // Send request and handle response
        let response = self.chat_completion(request).await
            .map_err(|e| Box::new(e) as Box<dyn std::error::Error + Send + Sync>)?;
        
        // Extract first choice (OpenAI typically returns one choice unless n > 1)
        let choice = response.choices.into_iter().next()
            .ok_or_else(|| Box::new(OpenAIError::Other("No choices returned by OpenAI".to_string())) as Box<dyn std::error::Error + Send + Sync>)?;

        // Convert back to SK format
        let mut content = Self::convert_openai_message_to_sk(&choice.message, Some(response.model));
        
        // Add metadata about the response
        if let Some(reason) = choice.finish_reason {
            content = content.with_metadata("finish_reason", reason);
        }
        content = content.with_metadata("response_id", response.id);

        Ok(content)
    }
    
    async fn get_streaming_chat_message_contents(
        &self,
        messages: &[SKChatMessage],
        execution_settings: Option<&PromptExecutionSettings>,
    ) -> semantic_kernel::Result<Box<dyn futures::Stream<Item = semantic_kernel::Result<semantic_kernel::content::StreamingChatMessageContent>> + Send + Unpin>> {
        use futures::stream::{self, StreamExt};
        use semantic_kernel::content::StreamingChatMessageContent;
        
        // Convert SK messages to OpenAI format
        let openai_messages: Vec<ChatMessage> = messages
            .iter()
            .map(Self::convert_sk_message_to_openai)
            .collect();
            
        // Determine model to use
        let model = execution_settings
            .and_then(|s| s.model_id.as_ref())
            .unwrap_or(&self.model);
            
        // Build request with streaming enabled
        let mut request = ChatCompletionRequest::new(model, openai_messages);
        request.stream = Some(true);
        
        // Apply execution settings
        if let Some(settings) = execution_settings {
            if let Some(max_tokens) = settings.max_tokens {
                request = request.with_max_tokens(max_tokens);
            }
            if let Some(temperature) = settings.temperature {
                request = request.with_temperature(temperature);
            }
            if let Some(top_p) = settings.top_p {
                request = request.with_top_p(top_p);
            }
        }
        
        // For now, return a simple implementation that simulates streaming
        // In a real implementation, this would use Server-Sent Events (SSE)
        let response = self.chat_completion(request).await
            .map_err(|e| Box::new(e) as Box<dyn std::error::Error + Send + Sync>)?;
            
        // Convert the single response to a stream of chunks
        let chunks = if let Some(choice) = response.choices.into_iter().next() {
            let content = choice.message.content;
            let role = match choice.message.role.as_str() {
                "assistant" => semantic_kernel::content::AuthorRole::Assistant,
                "user" => semantic_kernel::content::AuthorRole::User,
                "system" => semantic_kernel::content::AuthorRole::System,
                _ => semantic_kernel::content::AuthorRole::Assistant,
            };
            
            // Split content into chunks to simulate streaming
            let mut chunks = Vec::new();
            
            // First chunk with role
            chunks.push(Ok(StreamingChatMessageContent::new(None).with_role(role)));
            
            // Content chunks (split into words for demonstration)
            for word in content.split_whitespace() {
                chunks.push(Ok(StreamingChatMessageContent::new(Some(format!("{} ", word)))));
            }
            
            // Final chunk
            if let Some(reason) = choice.finish_reason {
                chunks.push(Ok(StreamingChatMessageContent::new(None).final_chunk(reason)));
            }
            
            chunks
        } else {
            vec![Err("No response from OpenAI".into())]
        };
        
        // Convert to stream
        let stream = stream::iter(chunks);
        Ok(Box::new(stream))
    }
}

#[async_trait]
impl EmbeddingService for OpenAIClient {
    async fn generate_embeddings(
        &self,
        texts: &[String],
    ) -> semantic_kernel::Result<Vec<Vec<f32>>> {
        // Build embedding request
        let request = EmbeddingRequest::new(&self.embedding_model, texts.to_vec());

        // Send request and handle response
        let response = self.embeddings(request).await
            .map_err(|e| Box::new(e) as Box<dyn std::error::Error + Send + Sync>)?;
        
        // Extract embeddings in order
        let mut embeddings = vec![vec![]; texts.len()];
        for embedding_data in response.data {
            if let Some(index) = usize::try_from(embedding_data.index).ok() {
                if index < embeddings.len() {
                    embeddings[index] = embedding_data.embedding;
                }
            }
        }

        Ok(embeddings)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use semantic_kernel::content::{ChatMessage as SKChatMessage, AuthorRole};

    #[test]
    fn test_client_creation() {
        let client = OpenAIClient::new("test-key").unwrap();
        assert_eq!(client.model(), defaults::CHAT_MODEL);
        assert_eq!(client.attributes().get("provider").unwrap(), "openai");
    }

    #[test]
    fn test_client_creation_with_model() {
        let client = OpenAIClient::with_model("test-key", "gpt-4").unwrap();
        assert_eq!(client.model(), "gpt-4");
        assert_eq!(client.attributes().get("model").unwrap(), "gpt-4");
    }

    #[test]
    fn test_empty_api_key_fails() {
        let result = OpenAIClient::new("");
        assert!(matches!(result, Err(OpenAIError::MissingApiKey)));
    }

    #[test]
    fn test_sk_to_openai_message_conversion() {
        let sk_message = SKChatMessage::user("Hello, world!");
        let openai_message = OpenAIClient::convert_sk_message_to_openai(&sk_message);
        
        assert_eq!(openai_message.role, "user");
        assert_eq!(openai_message.content, "Hello, world!");
        assert!(openai_message.name.is_none());
    }

    #[test]
    fn test_openai_to_sk_message_conversion() {
        let openai_message = ChatMessage::assistant("Hello there!");
        let sk_content = OpenAIClient::convert_openai_message_to_sk(&openai_message, Some("gpt-3.5-turbo".to_string()));
        
        assert_eq!(sk_content.role, AuthorRole::Assistant);
        assert_eq!(sk_content.content, "Hello there!");
        assert_eq!(sk_content.model_id.unwrap(), "gpt-3.5-turbo");
        assert_eq!(sk_content.metadata.get("provider").unwrap(), "openai");
    }

    #[test]
    fn test_chat_completion_request_serialization() {
        use crate::models::{ChatCompletionRequest, ChatMessage};
        
        let messages = vec![
            ChatMessage::system("You are a helpful assistant."),
            ChatMessage::user("Hello!"),
        ];
        
        let request = ChatCompletionRequest::new("gpt-3.5-turbo", messages)
            .with_max_tokens(100)
            .with_temperature(0.7);
        
        let json = serde_json::to_string(&request).unwrap();
        assert!(json.contains("gpt-3.5-turbo"));
        assert!(json.contains("You are a helpful assistant"));
        assert!(json.contains("Hello!"));
        assert!(json.contains("max_tokens"));
        assert!(json.contains("temperature"));
    }

    #[test]
    fn test_chat_completion_response_deserialization() {
        let json = r#"
        {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1677652288,
            "model": "gpt-3.5-turbo",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello! How can I help you today?"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 9,
                "completion_tokens": 12,
                "total_tokens": 21
            }
        }
        "#;
        
        let response: crate::models::ChatCompletionResponse = serde_json::from_str(json).unwrap();
        assert_eq!(response.id, "chatcmpl-123");
        assert_eq!(response.model, "gpt-3.5-turbo");
        assert_eq!(response.choices.len(), 1);
        assert_eq!(response.choices[0].message.content, "Hello! How can I help you today?");
        assert_eq!(response.choices[0].message.role, "assistant");
        assert_eq!(response.usage.as_ref().unwrap().total_tokens, 21);
    }

    #[test]
    fn test_message_role_conversions() {
        // Test all SK roles convert to OpenAI roles correctly
        let test_cases = vec![
            (AuthorRole::System, "system"),
            (AuthorRole::User, "user"),
            (AuthorRole::Assistant, "assistant"),
            (AuthorRole::Tool, "tool"),
        ];
        
        for (sk_role, expected_openai_role) in test_cases {
            let sk_message = SKChatMessage {
                role: sk_role,
                content: "test".to_string(),
                name: None,
                tool_call_id: None,
                tool_calls: None,
            };
            let openai_message = OpenAIClient::convert_sk_message_to_openai(&sk_message);
            assert_eq!(openai_message.role, expected_openai_role);
        }
    }
}