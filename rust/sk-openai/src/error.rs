//! Error types for OpenAI connector

use thiserror::Error;

/// Result type for OpenAI operations
pub type Result<T> = std::result::Result<T, OpenAIError>;

/// Errors that can occur when using the OpenAI connector
#[derive(Error, Debug)]
pub enum OpenAIError {
    /// HTTP request failed
    #[error("HTTP request failed: {0}")]
    Http(#[from] reqwest::Error),
    
    /// JSON serialization/deserialization failed
    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),
    
    /// OpenAI API returned an error
    #[error("OpenAI API error: {message} (code: {code})")]
    ApiError {
        code: String,
        message: String,
    },
    
    /// Invalid configuration
    #[error("Configuration error: {0}")]
    Configuration(String),
    
    /// Missing API key
    #[error("OpenAI API key is required but not provided")]
    MissingApiKey,
    
    /// Invalid model
    #[error("Invalid or unsupported model: {0}")]
    InvalidModel(String),
    
    /// Generic error
    #[error("OpenAI error: {0}")]
    Other(String),
}