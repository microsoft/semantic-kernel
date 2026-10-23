//! # SK Process Framework
//! 
//! Declarative business workflow support for Semantic Kernel, providing:
//! - Process and Step abstractions for workflow modeling
//! - Event logging and OpenTelemetry tracing for auditability
//! - State management and execution control
//! - Support for AI-driven and human-driven steps

use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Arc;
use uuid::Uuid;
use chrono::{DateTime, Utc};

pub mod engine;
pub mod events;
pub mod steps;

pub use engine::ProcessEngine;
pub use events::{ProcessEvent, EventLog};
pub use steps::{AIExtractionStep, HumanApprovalStep, DataTransformStep, ApprovalDecision};

/// Result type for process operations
pub type ProcessResult<T> = Result<T, ProcessError>;

/// Errors that can occur during process execution
#[derive(thiserror::Error, Debug)]
pub enum ProcessError {
    #[error("Step execution failed: {0}")]
    StepExecutionFailed(String),
    
    #[error("Process validation failed: {0}")]
    ValidationFailed(String),
    
    #[error("State management error: {0}")]
    StateError(String),
    
    #[error("Serialization error: {0}")]
    SerializationError(#[from] serde_json::Error),
    
    #[error("Kernel error: {0}")]
    KernelError(String),
}

/// Represents the current state of a process instance
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ProcessState {
    /// Process is ready to start
    Ready,
    /// Process is currently running
    Running,
    /// Process is paused waiting for external input
    Paused,
    /// Process completed successfully
    Completed,
    /// Process failed with an error
    Failed(String),
}

/// Context passed to process steps during execution
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessContext {
    /// Unique identifier for this process instance
    pub process_id: Uuid,
    /// Current step index in the process
    pub current_step: usize,
    /// Process state data
    pub state: HashMap<String, serde_json::Value>,
    /// Process metadata
    pub metadata: HashMap<String, String>,
    /// Timestamp when the process started
    pub started_at: DateTime<Utc>,
}

impl ProcessContext {
    /// Create a new process context
    pub fn new(process_id: Uuid) -> Self {
        Self {
            process_id,
            current_step: 0,
            state: HashMap::new(),
            metadata: HashMap::new(),
            started_at: Utc::now(),
        }
    }
    
    /// Set a state value
    pub fn set_state<T: Serialize>(&mut self, key: &str, value: T) -> ProcessResult<()> {
        let json_value = serde_json::to_value(value)?;
        self.state.insert(key.to_string(), json_value);
        Ok(())
    }
    
    /// Get a state value
    pub fn get_state<T: for<'de> Deserialize<'de>>(&self, key: &str) -> ProcessResult<Option<T>> {
        if let Some(value) = self.state.get(key) {
            let result = serde_json::from_value(value.clone())?;
            Ok(Some(result))
        } else {
            Ok(None)
        }
    }
}

/// Trait representing an executable step in a process
#[async_trait]
pub trait ProcessStep: Send + Sync {
    /// Get the step name
    fn name(&self) -> &str;
    
    /// Get the step description
    fn description(&self) -> &str;
    
    /// Execute the step with the given context and kernel
    async fn execute(
        &self,
        context: &mut ProcessContext,
        kernel: &semantic_kernel::Kernel,
    ) -> ProcessResult<StepResult>;
    
    /// Validate the step configuration
    fn validate(&self) -> ProcessResult<()> {
        Ok(()) // Default implementation
    }
}

/// Result of executing a process step
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StepResult {
    /// Whether the step completed successfully
    pub success: bool,
    /// Output data from the step
    pub output: Option<serde_json::Value>,
    /// Error message if the step failed
    pub error: Option<String>,
    /// Whether to pause the process after this step
    pub pause_process: bool,
}

impl StepResult {
    /// Create a successful step result
    pub fn success() -> Self {
        Self {
            success: true,
            output: None,
            error: None,
            pause_process: false,
        }
    }
    
    /// Create a successful step result with output
    pub fn success_with_output<T: Serialize>(output: T) -> ProcessResult<Self> {
        Ok(Self {
            success: true,
            output: Some(serde_json::to_value(output)?),
            error: None,
            pause_process: false,
        })
    }
    
    /// Create a successful step result that pauses the process
    pub fn success_with_pause() -> Self {
        Self {
            success: true,
            output: None,
            error: None,
            pause_process: true,
        }
    }
    
    /// Create a failed step result
    pub fn failure(error: impl Into<String>) -> Self {
        Self {
            success: false,
            output: None,
            error: Some(error.into()),
            pause_process: false,
        }
    }
}

/// Trait representing a complete business process
#[async_trait]
pub trait Process: Send + Sync {
    /// Get the process name
    fn name(&self) -> &str;
    
    /// Get the process description  
    fn description(&self) -> &str;
    
    /// Get the steps in this process
    fn steps(&self) -> &[Arc<dyn ProcessStep>];
    
    /// Validate the entire process
    fn validate(&self) -> ProcessResult<()> {
        for step in self.steps() {
            step.validate()?;
        }
        Ok(())
    }
}

/// A concrete implementation of a process
pub struct WorkflowProcess {
    name: String,
    description: String,
    steps: Vec<Arc<dyn ProcessStep>>,
}

impl std::fmt::Debug for WorkflowProcess {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("WorkflowProcess")
            .field("name", &self.name)
            .field("description", &self.description)
            .field("steps_count", &self.steps.len())
            .finish()
    }
}

impl WorkflowProcess {
    /// Create a new workflow process
    pub fn new(name: impl Into<String>, description: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            description: description.into(),
            steps: Vec::new(),
        }
    }
    
    /// Add a step to the process
    pub fn add_step(mut self, step: Arc<dyn ProcessStep>) -> Self {
        self.steps.push(step);
        self
    }
}

#[async_trait]
impl Process for WorkflowProcess {
    fn name(&self) -> &str {
        &self.name
    }
    
    fn description(&self) -> &str {
        &self.description
    }
    
    fn steps(&self) -> &[Arc<dyn ProcessStep>] {
        &self.steps
    }
}
