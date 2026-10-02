//! Planning capabilities for Semantic Kernel Rust
//! 
//! This crate provides planners that can break down natural language goals
//! into sequences of function calls using modern LLM function calling capabilities.
//! 
//! ## Features
//! 
//! - **SequentialPlanner**: Breaks down complex goals into sequential function calls
//! - **FunctionCallingStepwisePlanner**: Iterative planning using LLM function calling  
//! - **Plan DSL**: Fluent API for constructing and chaining plan steps
//! - **JSON Trace Format**: Compatible with .NET Semantic Kernel trace format

pub mod plan;
pub mod sequential_planner;
pub mod stepwise_planner;
pub mod trace;

pub use plan::{Plan, PlanStep, PlanResult, PlanBuilder};
pub use sequential_planner::SequentialPlanner;
pub use stepwise_planner::FunctionCallingStepwisePlanner;
pub use trace::{ExecutionTrace, FunctionCallTrace, TraceEvent};

/// Result type for planning operations
pub type Result<T> = std::result::Result<T, PlanError>;

/// Errors that can occur during planning
#[derive(Debug, thiserror::Error)]
pub enum PlanError {
    #[error("Planning failed: {0}")]
    PlanningFailed(String),
    
    #[error("Function execution failed: {0}")]
    FunctionExecutionFailed(String),
    
    #[error("Invalid plan step: {0}")]
    InvalidPlanStep(String),
    
    #[error("Kernel error: {0}")]
    KernelError(String),
    
    #[error("Serialization error: {0}")]
    SerializationError(#[from] serde_json::Error),
}
