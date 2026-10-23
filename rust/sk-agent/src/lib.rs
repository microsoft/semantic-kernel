//! Agent Framework for Semantic Kernel Rust
//!
//! This crate provides multi-step agents with orchestration patterns, mirroring
//! the Microsoft Semantic Kernel .NET Agent Framework. It enables building AI
//! applications with multiple autonomous agents that can collaborate, hand off
//! tasks, and make decisions using integrated planners.
//!
//! ## Features
//!
//! - **Agent Abstractions**: Core `Agent` trait with identity and communication protocols
//! - **Agent Threads**: Conversation state management with `AgentThread`
//! - **Chat Completion Agents**: LLM-powered agents using `ChatCompletionAgent`
//! - **Orchestration Patterns**: Sequential and handoff orchestration for multi-agent workflows
//! - **Planner Integration**: Autonomous decision making using SK planners
//! - **Thread Safety**: Full async/await support with concurrent agent execution
//!
//! ## Example
//!
//! ```rust,no_run
//! use sk_agent::{Agent, ChatCompletionAgent, AgentThread};
//! use semantic_kernel::{Kernel, KernelBuilder};
//!
//! #[tokio::main]
//! async fn main() -> Result<(), Box<dyn std::error::Error>> {
//!     // Create kernel with chat completion service
//!     let kernel = KernelBuilder::new().build();
//!     
//!     // Create a chat completion agent
//!     let agent = ChatCompletionAgent::builder()
//!         .name("Assistant")
//!         .description("A helpful AI assistant")
//!         .instructions("You are a helpful assistant.")
//!         .kernel(kernel)
//!         .build()?;
//!     
//!     // Create a conversation thread
//!     let mut thread = AgentThread::new();
//!     
//!     // Invoke the agent
//!     let response = agent.invoke_async(&mut thread, "Hello, how can you help me?").await?;
//!     println!("Agent: {}", response.content);
//!     
//!     Ok(())
//! }
//! ```

pub mod agent;
pub mod thread;
pub mod chat;
pub mod channel;
pub mod orchestration;
pub mod chat_completion_agent;
pub mod errors;

#[cfg(test)]
mod concurrency_tests;

pub use agent::Agent;
pub use thread::AgentThread;
pub use chat::AgentChat;
pub use channel::AgentChannel;
pub use chat_completion_agent::ChatCompletionAgent;
pub use orchestration::{SequentialOrchestration, HandoffOrchestration};
pub use errors::{AgentError, Result};

/// Re-export commonly used types from semantic_kernel
pub use semantic_kernel::{
    ChatHistory, ChatMessage, ChatMessageContent, AuthorRole,
    Kernel, KernelBuilder, Result as SKResult
};

/// Re-export async trait for convenience
pub use async_trait::async_trait;
