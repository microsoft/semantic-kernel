//! OpenAI API data models

use serde::{Deserialize, Serialize};

/// Request to the chat completions API
#[derive(Debug, Clone, Serialize)]
pub struct ChatCompletionRequest {
    /// Model to use for completion
    pub model: String,
    /// Messages in the conversation
    pub messages: Vec<ChatMessage>,
    /// Maximum number of tokens to generate
    #[serde(skip_serializing_if = "Option::is_none")]
    pub max_tokens: Option<u32>,
    /// Temperature for randomness (0.0 - 2.0)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub temperature: Option<f32>,
    /// Top-p sampling parameter
    #[serde(skip_serializing_if = "Option::is_none")]
    pub top_p: Option<f32>,
    /// Number of completions to generate
    #[serde(skip_serializing_if = "Option::is_none")]
    pub n: Option<u32>,
    /// Whether to stream the response
    #[serde(skip_serializing_if = "Option::is_none")]
    pub stream: Option<bool>,
    /// Stop sequences
    #[serde(skip_serializing_if = "Option::is_none")]
    pub stop: Option<Vec<String>>,
    /// Presence penalty
    #[serde(skip_serializing_if = "Option::is_none")]
    pub presence_penalty: Option<f32>,
    /// Frequency penalty
    #[serde(skip_serializing_if = "Option::is_none")]
    pub frequency_penalty: Option<f32>,
    /// User identifier for monitoring
    #[serde(skip_serializing_if = "Option::is_none")]
    pub user: Option<String>,
}

/// Chat message in OpenAI format
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatMessage {
    /// Role of the message author
    pub role: String,
    /// Content of the message
    pub content: String,
    /// Optional name of the author
    #[serde(skip_serializing_if = "Option::is_none")]
    pub name: Option<String>,
}

/// Response from the chat completions API
#[derive(Debug, Clone, Deserialize)]
pub struct ChatCompletionResponse {
    /// Unique identifier for the completion
    pub id: String,
    /// Object type (should be "chat.completion")
    pub object: String,
    /// Unix timestamp when the completion was created
    pub created: u64,
    /// Model used for the completion
    pub model: String,
    /// List of completion choices
    pub choices: Vec<ChatChoice>,
    /// Token usage statistics
    pub usage: Option<TokenUsage>,
}

/// A completion choice
#[derive(Debug, Clone, Deserialize)]
pub struct ChatChoice {
    /// Index of this choice
    pub index: u32,
    /// The completion message
    pub message: ChatMessage,
    /// Reason the completion finished
    pub finish_reason: Option<String>,
}

/// Token usage statistics
#[derive(Debug, Clone, Deserialize)]
pub struct TokenUsage {
    /// Number of tokens in the prompt
    pub prompt_tokens: u32,
    /// Number of tokens in the completion
    pub completion_tokens: u32,
    /// Total number of tokens used
    pub total_tokens: u32,
}

/// Error response from OpenAI API
#[derive(Debug, Clone, Deserialize)]
pub struct ErrorResponse {
    /// Error details
    pub error: ApiError,
}

/// API error details
#[derive(Debug, Clone, Deserialize)]
pub struct ApiError {
    /// Error message
    pub message: String,
    /// Error type
    #[serde(rename = "type")]
    pub error_type: Option<String>,
    /// Error code
    pub code: Option<String>,
}

impl ChatMessage {
    /// Create a system message
    pub fn system(content: impl Into<String>) -> Self {
        Self {
            role: "system".to_string(),
            content: content.into(),
            name: None,
        }
    }

    /// Create a user message
    pub fn user(content: impl Into<String>) -> Self {
        Self {
            role: "user".to_string(),
            content: content.into(),
            name: None,
        }
    }

    /// Create an assistant message
    pub fn assistant(content: impl Into<String>) -> Self {
        Self {
            role: "assistant".to_string(),
            content: content.into(),
            name: None,
        }
    }
}

impl ChatCompletionRequest {
    /// Create a new chat completion request
    pub fn new(model: impl Into<String>, messages: Vec<ChatMessage>) -> Self {
        Self {
            model: model.into(),
            messages,
            max_tokens: None,
            temperature: None,
            top_p: None,
            n: None,
            stream: None,
            stop: None,
            presence_penalty: None,
            frequency_penalty: None,
            user: None,
        }
    }

    /// Set max tokens
    pub fn with_max_tokens(mut self, max_tokens: u32) -> Self {
        self.max_tokens = Some(max_tokens);
        self
    }

    /// Set temperature
    pub fn with_temperature(mut self, temperature: f32) -> Self {
        self.temperature = Some(temperature);
        self
    }

    /// Set top-p
    pub fn with_top_p(mut self, top_p: f32) -> Self {
        self.top_p = Some(top_p);
        self
    }
}

/// Request to the embeddings API
#[derive(Debug, Clone, Serialize)]
pub struct EmbeddingRequest {
    /// Model to use for embeddings
    pub model: String,
    /// Input text(s) to embed
    pub input: Vec<String>,
    /// User identifier for monitoring
    #[serde(skip_serializing_if = "Option::is_none")]
    pub user: Option<String>,
}

/// Response from the embeddings API
#[derive(Debug, Clone, Deserialize)]
pub struct EmbeddingResponse {
    /// Object type (should be "list")
    pub object: String,
    /// List of embedding data
    pub data: Vec<EmbeddingData>,
    /// Model used for the embeddings
    pub model: String,
    /// Token usage statistics
    pub usage: EmbeddingUsage,
}

/// Individual embedding data
#[derive(Debug, Clone, Deserialize)]
pub struct EmbeddingData {
    /// Object type (should be "embedding")
    pub object: String,
    /// The embedding vector
    pub embedding: Vec<f32>,
    /// Index of this embedding
    pub index: u32,
}

/// Token usage for embeddings
#[derive(Debug, Clone, Deserialize)]
pub struct EmbeddingUsage {
    /// Number of tokens in the prompt
    pub prompt_tokens: u32,
    /// Total number of tokens used
    pub total_tokens: u32,
}

impl EmbeddingRequest {
    /// Create a new embedding request
    pub fn new(model: impl Into<String>, input: Vec<String>) -> Self {
        Self {
            model: model.into(),
            input,
            user: None,
        }
    }

    /// Set user identifier
    pub fn with_user(mut self, user: impl Into<String>) -> Self {
        self.user = Some(user.into());
        self
    }
}