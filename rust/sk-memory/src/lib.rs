//! Memory storage abstraction and implementations for Semantic Kernel
//!
//! This crate provides memory storage capabilities for semantic embeddings,
//! including traits for memory store operations and implementations for
//! in-memory storage and vector databases like Qdrant.

pub mod memory_store;
pub mod memory_record;
pub mod in_memory_store;
pub mod embedding_flow;

#[cfg(feature = "qdrant")]
pub mod qdrant_store;

pub use memory_store::{MemoryStore, SearchResult};
pub use memory_record::{MemoryRecord, MemoryRecordMetadata};
pub use in_memory_store::InMemoryMemoryStore;
pub use embedding_flow::EmbeddingFlow;

#[cfg(feature = "qdrant")]
pub use qdrant_store::QdrantMemoryStore;

/// Result type for memory store operations
pub type Result<T> = std::result::Result<T, Box<dyn std::error::Error + Send + Sync>>;

/// Re-export common dependencies
pub use semantic_kernel::async_trait;
