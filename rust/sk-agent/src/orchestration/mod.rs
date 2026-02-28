//! Agent orchestration patterns

use crate::agent::Agent;
use crate::errors::Result;
use crate::thread::AgentThread;
use async_trait::async_trait;
use semantic_kernel::ChatMessageContent;
use std::collections::HashMap;
use std::sync::Arc;

pub mod sequential;
pub mod handoff;

pub use sequential::SequentialOrchestration;
pub use handoff::HandoffOrchestration;

/// Base trait for agent orchestration patterns.
/// 
/// Orchestrations define how multiple agents collaborate to process
/// requests and generate responses. Different patterns include
/// sequential processing, handoff-based routing, and concurrent execution.
#[async_trait]
pub trait Orchestration: Send + Sync {
    /// Gets the agents participating in this orchestration.
    fn agents(&self) -> &[Arc<dyn Agent>];
    
    /// Processes an input message through the orchestrated agents.
    ///
    /// # Arguments
    /// * `input` - The input message to process
    /// * `context` - Optional context for the orchestration
    ///
    /// # Returns
    /// The final result from the orchestration
    async fn execute_async(
        &self,
        input: &str,
        context: Option<OrchestrationContext>,
    ) -> Result<OrchestrationResult>;
    
    /// Gets the orchestration type identifier.
    fn orchestration_type(&self) -> &str;
}

/// Context information for orchestration execution.
#[derive(Debug, Clone)]
pub struct OrchestrationContext {
    /// Unique identifier for this execution
    pub execution_id: String,
    /// Additional metadata
    pub metadata: HashMap<String, String>,
    /// Maximum execution time in seconds
    pub timeout_seconds: Option<u32>,
    /// Whether to trace execution steps
    pub trace_enabled: bool,
}

impl OrchestrationContext {
    /// Creates a new orchestration context.
    pub fn new(execution_id: String) -> Self {
        Self {
            execution_id,
            metadata: HashMap::new(),
            timeout_seconds: None,
            trace_enabled: false,
        }
    }
    
    /// Creates a context with tracing enabled.
    pub fn with_tracing(execution_id: String) -> Self {
        Self {
            execution_id,
            metadata: HashMap::new(),
            timeout_seconds: None,
            trace_enabled: true,
        }
    }
    
    /// Sets a timeout for the orchestration.
    pub fn with_timeout(mut self, timeout_seconds: u32) -> Self {
        self.timeout_seconds = Some(timeout_seconds);
        self
    }
    
    /// Adds metadata to the context.
    pub fn with_metadata(mut self, key: String, value: String) -> Self {
        self.metadata.insert(key, value);
        self
    }
}

impl Default for OrchestrationContext {
    fn default() -> Self {
        Self::new(uuid::Uuid::new_v4().to_string())
    }
}

/// Result of an orchestration execution.
#[derive(Debug, Clone)]
pub struct OrchestrationResult {
    /// The final output message
    pub output: ChatMessageContent,
    /// Which agent produced the final output
    pub final_agent: String,
    /// Execution trace if enabled
    pub trace: Option<OrchestrationTrace>,
    /// Execution metadata
    pub metadata: HashMap<String, String>,
}

impl OrchestrationResult {
    /// Creates a new orchestration result.
    pub fn new(output: ChatMessageContent, final_agent: String) -> Self {
        Self {
            output,
            final_agent,
            trace: None,
            metadata: HashMap::new(),
        }
    }
    
    /// Creates a result with tracing information.
    pub fn with_trace(
        output: ChatMessageContent,
        final_agent: String,
        trace: OrchestrationTrace,
    ) -> Self {
        Self {
            output,
            final_agent,
            trace: Some(trace),
            metadata: HashMap::new(),
        }
    }
    
    /// Adds metadata to the result.
    pub fn with_metadata(mut self, key: String, value: String) -> Self {
        self.metadata.insert(key, value);
        self
    }
}

/// Execution trace for orchestration debugging.
#[derive(Debug, Clone)]
pub struct OrchestrationTrace {
    /// Execution steps in order
    pub steps: Vec<OrchestrationStep>,
    /// Total execution time in milliseconds
    pub total_time_ms: u64,
    /// Whether execution completed successfully
    pub success: bool,
}

impl OrchestrationTrace {
    /// Creates a new empty trace.
    pub fn new() -> Self {
        Self {
            steps: Vec::new(),
            total_time_ms: 0,
            success: false,
        }
    }
    
    /// Adds a step to the trace.
    pub fn add_step(&mut self, step: OrchestrationStep) {
        self.steps.push(step);
    }
    
    /// Marks the trace as completed successfully.
    pub fn complete_success(&mut self, total_time_ms: u64) {
        self.total_time_ms = total_time_ms;
        self.success = true;
    }
    
    /// Marks the trace as failed.
    pub fn complete_failure(&mut self, total_time_ms: u64) {
        self.total_time_ms = total_time_ms;
        self.success = false;
    }
}

impl Default for OrchestrationTrace {
    fn default() -> Self {
        Self::new()
    }
}

/// A single step in an orchestration execution.
#[derive(Debug, Clone)]
pub struct OrchestrationStep {
    /// Agent that executed this step
    pub agent_id: String,
    /// Agent name
    pub agent_name: Option<String>,
    /// Input to the agent
    pub input: String,
    /// Output from the agent
    pub output: String,
    /// Step execution time in milliseconds
    pub time_ms: u64,
    /// Whether the step was successful
    pub success: bool,
    /// Error message if the step failed
    pub error: Option<String>,
}

impl OrchestrationStep {
    /// Creates a new successful step.
    pub fn success(
        agent_id: String,
        agent_name: Option<String>,
        input: String,
        output: String,
        time_ms: u64,
    ) -> Self {
        Self {
            agent_id,
            agent_name,
            input,
            output,
            time_ms,
            success: true,
            error: None,
        }
    }
    
    /// Creates a new failed step.
    pub fn failure(
        agent_id: String,
        agent_name: Option<String>,
        input: String,
        error: String,
        time_ms: u64,
    ) -> Self {
        Self {
            agent_id,
            agent_name,
            input,
            output: String::new(),
            time_ms,
            success: false,
            error: Some(error),
        }
    }
}

/// Shared execution state for orchestrations.
#[derive(Debug)]
pub struct OrchestrationState {
    /// Current input being processed
    pub current_input: String,
    /// Thread for conversation context
    pub thread: AgentThread,
    /// Execution trace
    pub trace: Option<OrchestrationTrace>,
    /// Step counter
    pub step_count: usize,
}

impl OrchestrationState {
    /// Creates a new orchestration state.
    pub fn new(input: String, trace_enabled: bool) -> Self {
        Self {
            current_input: input,
            thread: AgentThread::new(),
            trace: if trace_enabled { Some(OrchestrationTrace::new()) } else { None },
            step_count: 0,
        }
    }
    
    /// Updates the current input.
    pub fn update_input(&mut self, input: String) {
        self.current_input = input;
    }
    
    /// Adds a step to the trace if tracing is enabled.
    pub fn add_trace_step(&mut self, step: OrchestrationStep) {
        if let Some(ref mut trace) = self.trace {
            trace.add_step(step);
        }
        self.step_count += 1;
    }
    
    /// Gets the current step number.
    pub fn current_step(&self) -> usize {
        self.step_count
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_orchestration_context() {
        let context = OrchestrationContext::new("test-123".to_string())
            .with_timeout(60)
            .with_metadata("key".to_string(), "value".to_string());
        
        assert_eq!(context.execution_id, "test-123");
        assert_eq!(context.timeout_seconds, Some(60));
        assert_eq!(context.metadata.get("key"), Some(&"value".to_string()));
        assert!(!context.trace_enabled);
    }
    
    #[test]
    fn test_orchestration_context_with_tracing() {
        let context = OrchestrationContext::with_tracing("test-456".to_string());
        assert!(context.trace_enabled);
    }
    
    #[test]
    fn test_orchestration_result() {
        let output = ChatMessageContent::new(semantic_kernel::AuthorRole::Assistant, "Test output".to_string());
        let result = OrchestrationResult::new(output, "agent-1".to_string())
            .with_metadata("status".to_string(), "success".to_string());
        
        assert_eq!(result.final_agent, "agent-1");
        assert_eq!(result.metadata.get("status"), Some(&"success".to_string()));
        assert!(result.trace.is_none());
    }
    
    #[test]
    fn test_orchestration_trace() {
        let mut trace = OrchestrationTrace::new();
        assert!(!trace.success);
        assert_eq!(trace.steps.len(), 0);
        
        let step = OrchestrationStep::success(
            "agent-1".to_string(),
            Some("Test Agent".to_string()),
            "input".to_string(),
            "output".to_string(),
            100,
        );
        trace.add_step(step);
        
        assert_eq!(trace.steps.len(), 1);
        assert!(trace.steps[0].success);
        
        trace.complete_success(150);
        assert!(trace.success);
        assert_eq!(trace.total_time_ms, 150);
    }
    
    #[test]
    fn test_orchestration_state() {
        let mut state = OrchestrationState::new("test input".to_string(), true);
        assert_eq!(state.current_input, "test input");
        assert!(state.trace.is_some());
        assert_eq!(state.current_step(), 0);
        
        state.update_input("new input".to_string());
        assert_eq!(state.current_input, "new input");
        
        let step = OrchestrationStep::success(
            "agent-1".to_string(),
            None,
            "input".to_string(),
            "output".to_string(),
            50,
        );
        state.add_trace_step(step);
        assert_eq!(state.current_step(), 1);
    }
}