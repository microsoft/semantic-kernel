//! OpenAI connector for Semantic Kernel
//! 
//! This crate provides OpenAI API integration for chat completions and embeddings,
//! implementing the Semantic Kernel service traits.

pub mod client;
pub mod models;
pub mod error;

pub use client::OpenAIClient;
pub use error::{OpenAIError, Result};

/// Default OpenAI API base URL
pub const DEFAULT_BASE_URL: &str = "https://api.openai.com/v1";

/// Default models
pub mod defaults {
    pub const CHAT_MODEL: &str = "gpt-3.5-turbo";
    pub const EMBEDDING_MODEL: &str = "text-embedding-ada-002";
}
