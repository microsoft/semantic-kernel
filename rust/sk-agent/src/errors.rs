//! Error types for the Agent Framework

use thiserror::Error;

/// Result type for agent operations
pub type Result<T> = std::result::Result<T, AgentError>;

/// Errors that can occur during agent operations
#[derive(Debug, Error)]
pub enum AgentError {
    /// Agent configuration error
    #[error("Agent configuration error: {0}")]
    Configuration(String),
    
    /// Agent execution error
    #[error("Agent execution failed: {0}")]
    Execution(String),
    
    /// Agent thread error
    #[error("Agent thread error: {0}")]
    Thread(String),
    
    /// Agent chat error
    #[error("Agent chat error: {0}")]
    Chat(String),
    
    /// Orchestration error
    #[error("Orchestration error: {0}")]
    Orchestration(String),
    
    /// Handoff error
    #[error("Handoff error: {0}")]
    Handoff(String),
    
    /// Agent not found
    #[error("Agent not found: {0}")]
    AgentNotFound(String),
    
    /// Invalid agent state
    #[error("Invalid agent state: {0}")]
    InvalidState(String),
    
    /// Concurrent access error
    #[error("Concurrent access error: {0}")]
    ConcurrentAccess(String),
    
    /// Kernel error
    #[error("Kernel error: {0}")]
    Kernel(String),
    
    /// Serialization error
    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),
    
    /// Generic error
    #[error("Agent error: {0}")]
    Generic(String),
}

impl From<Box<dyn std::error::Error + Send + Sync>> for AgentError {
    fn from(error: Box<dyn std::error::Error + Send + Sync>) -> Self {
        AgentError::Kernel(error.to_string())
    }
}