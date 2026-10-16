//! Semantic Kernel for Rust
//! 
//! A Rust port of Microsoft's Semantic Kernel, providing AI orchestration capabilities,
//! LLM integration, and a plugin system for building AI applications.

pub mod kernel;
pub mod services;
pub mod content;

#[cfg(feature = "mock")]
pub mod mock;

pub use kernel::{Kernel, KernelBuilder};
pub use services::{ServiceProvider, EmbeddingService, ChatCompletionService, AIService};
pub use content::{ChatHistory, ChatMessage, ChatMessageContent, AuthorRole, PromptExecutionSettings, ToolCall, FunctionCall};

/// Result type for semantic kernel operations
pub type Result<T> = std::result::Result<T, Box<dyn std::error::Error + Send + Sync>>;

/// Async trait re-export for convenience
pub use async_trait::async_trait;

/// Procedural macros for plugin and function definition
pub use sk_macros::{sk_plugin, sk_function};
