//! Process execution engine with OpenTelemetry tracing support

use crate::{Process, ProcessContext, ProcessError, ProcessResult};
use opentelemetry::{global, trace::Tracer, KeyValue};
use semantic_kernel::Kernel;
use std::sync::Arc;
use tracing::{info, error, debug};
use uuid::Uuid;

/// Engine for executing business processes
pub struct ProcessEngine {
    event_log: Arc<crate::EventLog>,
}

impl ProcessEngine {
    /// Create a new process engine
    pub fn new() -> Self {
        let event_log = Arc::new(crate::EventLog::new());
        
        Self {
            event_log,
        }
    }
    
    /// Execute a process with the given kernel
    pub async fn execute_process(
        &self,
        process: Arc<dyn Process>,
        kernel: &Kernel,
    ) -> ProcessResult<ProcessContext> {
        let process_id = Uuid::new_v4();
        let mut context = ProcessContext::new(process_id);
        
        // Validate the process before execution
        process.validate()?;
        
        // Start OpenTelemetry span for the entire process
        let tracer = global::tracer("sk-process");
        let _span = tracer
            .span_builder(format!("process.{}", process.name()))
            .with_attributes(vec![
                KeyValue::new("process.id", process_id.to_string()),
                KeyValue::new("process.name", process.name().to_string()),
                KeyValue::new("process.steps.count", process.steps().len() as i64),
            ])
            .start(&tracer);
        
        info!("Starting process execution: {} ({})", process.name(), process_id);
        
        // Log process start event
        self.event_log.log_event(crate::ProcessEvent::ProcessStarted {
            process_id,
            process_name: process.name().to_string(),
            timestamp: chrono::Utc::now(),
        }).await;
        
        let steps = process.steps();
        
        for (step_index, step) in steps.iter().enumerate() {
            context.current_step = step_index;
            
            // Create span for this step
            let _step_span = tracer
                .span_builder(format!("step.{}", step.name()))
                .with_attributes(vec![
                    KeyValue::new("step.name", step.name().to_string()),
                    KeyValue::new("step.index", step_index as i64),
                    KeyValue::new("process.id", process_id.to_string()),
                ])
                .start(&tracer);
            
            debug!("Executing step {}: {}", step_index, step.name());
            
            // Log step start event
            self.event_log.log_event(crate::ProcessEvent::StepStarted {
                process_id,
                step_name: step.name().to_string(),
                step_index,
                timestamp: chrono::Utc::now(),
            }).await;
            
            // Execute the step
            match step.execute(&mut context, kernel).await {
                Ok(result) => {
                    debug!("Step {} completed successfully", step.name());
                    
                    // Log step completion event
                    self.event_log.log_event(crate::ProcessEvent::StepCompleted {
                        process_id,
                        step_name: step.name().to_string(),
                        step_index,
                        success: result.success,
                        output: result.output.clone(),
                        timestamp: chrono::Utc::now(),
                    }).await;
                    
                    if !result.success {
                        let error_msg = result.error.unwrap_or_else(|| "Unknown error".to_string());
                        error!("Step {} failed: {}", step.name(), error_msg);
                        
                        // Log process failure
                        self.event_log.log_event(crate::ProcessEvent::ProcessFailed {
                            process_id,
                            error: error_msg.clone(),
                            timestamp: chrono::Utc::now(),
                        }).await;
                        
                        return Err(ProcessError::StepExecutionFailed(
                            format!("Step '{}' failed: {}", step.name(), error_msg)
                        ));
                    }
                    
                    if result.pause_process {
                        info!("Process paused after step: {}", step.name());
                        
                        // Log process pause
                        self.event_log.log_event(crate::ProcessEvent::ProcessPaused {
                            process_id,
                            step_name: step.name().to_string(),
                            timestamp: chrono::Utc::now(),
                        }).await;
                        
                        break;
                    }
                }
                Err(e) => {
                    error!("Step {} execution failed: {}", step.name(), e);
                    
                    // Log step failure
                    self.event_log.log_event(crate::ProcessEvent::StepCompleted {
                        process_id,
                        step_name: step.name().to_string(),
                        step_index,
                        success: false,
                        output: None,
                        timestamp: chrono::Utc::now(),
                    }).await;
                    
                    // Log process failure
                    self.event_log.log_event(crate::ProcessEvent::ProcessFailed {
                        process_id,
                        error: e.to_string(),
                        timestamp: chrono::Utc::now(),
                    }).await;
                    
                    return Err(e);
                }
            }
        }
        
        // If we completed all steps without pausing, mark as completed
        if context.current_step + 1 >= steps.len() {
            info!("Process completed successfully: {}", process.name());
            
            // Log process completion
            self.event_log.log_event(crate::ProcessEvent::ProcessCompleted {
                process_id,
                timestamp: chrono::Utc::now(),
            }).await;
        }
        
        Ok(context)
    }
    
    /// Resume a paused process from a specific step
    pub async fn resume_process(
        &self,
        process: Arc<dyn Process>,
        mut context: ProcessContext,
        kernel: &Kernel,
    ) -> ProcessResult<ProcessContext> {
        let process_id = context.process_id;
        
        info!("Resuming process execution: {} ({})", process.name(), process_id);
        
        // Log process resume event
        self.event_log.log_event(crate::ProcessEvent::ProcessResumed {
            process_id,
            step_index: context.current_step,
            timestamp: chrono::Utc::now(),
        }).await;
        
        let steps = process.steps();
        
        // Continue from the current step
        for step_index in context.current_step..steps.len() {
            let step = &steps[step_index];
            context.current_step = step_index;
            
            debug!("Executing step {}: {}", step_index, step.name());
            
            // Log step start event
            self.event_log.log_event(crate::ProcessEvent::StepStarted {
                process_id,
                step_name: step.name().to_string(),
                step_index,
                timestamp: chrono::Utc::now(),
            }).await;
            
            match step.execute(&mut context, kernel).await {
                Ok(result) => {
                    debug!("Step {} completed successfully", step.name());
                    
                    // Log step completion event
                    self.event_log.log_event(crate::ProcessEvent::StepCompleted {
                        process_id,
                        step_name: step.name().to_string(),
                        step_index,
                        success: result.success,
                        output: result.output.clone(),
                        timestamp: chrono::Utc::now(),
                    }).await;
                    
                    if !result.success {
                        let error_msg = result.error.unwrap_or_else(|| "Unknown error".to_string());
                        error!("Step {} failed: {}", step.name(), error_msg);
                        
                        return Err(ProcessError::StepExecutionFailed(
                            format!("Step '{}' failed: {}", step.name(), error_msg)
                        ));
                    }
                    
                    if result.pause_process {
                        info!("Process paused after step: {}", step.name());
                        break;
                    }
                }
                Err(e) => {
                    error!("Step {} execution failed: {}", step.name(), e);
                    return Err(e);
                }
            }
        }
        
        if context.current_step + 1 >= steps.len() {
            info!("Process completed successfully: {}", process.name());
            
            // Log process completion
            self.event_log.log_event(crate::ProcessEvent::ProcessCompleted {
                process_id,
                timestamp: chrono::Utc::now(),
            }).await;
        }
        
        Ok(context)
    }
    
    /// Get the event log for this engine
    pub fn event_log(&self) -> Arc<crate::EventLog> {
        Arc::clone(&self.event_log)
    }
}

impl Default for ProcessEngine {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{ProcessStep, StepResult, WorkflowProcess};
    use async_trait::async_trait;
    
    struct TestStep {
        name: String,
        should_fail: bool,
        should_pause: bool,
    }
    
    impl TestStep {
        fn new(name: impl Into<String>) -> Self {
            Self {
                name: name.into(),
                should_fail: false,
                should_pause: false,
            }
        }
        
        fn with_failure(mut self) -> Self {
            self.should_fail = true;
            self
        }
        
        fn with_pause(mut self) -> Self {
            self.should_pause = true;
            self
        }
    }
    
    #[async_trait]
    impl ProcessStep for TestStep {
        fn name(&self) -> &str {
            &self.name
        }
        
        fn description(&self) -> &str {
            "Test step"
        }
        
        async fn execute(
            &self,
            context: &mut ProcessContext,
            _kernel: &Kernel,
        ) -> ProcessResult<StepResult> {
            if self.should_fail {
                return Ok(StepResult::failure("Test failure"));
            }
            
            if self.should_pause {
                return Ok(StepResult::success_with_pause());
            }
            
            // Set some test data
            context.set_state("test_data", format!("executed_{}", self.name))?;
            
            Ok(StepResult::success())
        }
    }
    
    #[tokio::test]
    async fn test_process_execution_success() {
        let engine = ProcessEngine::new();
        let kernel = semantic_kernel::KernelBuilder::new().build();
        
        let process: Arc<dyn Process> = Arc::new(
            WorkflowProcess::new("test_process", "Test process")
                .add_step(Arc::new(TestStep::new("step1")))
                .add_step(Arc::new(TestStep::new("step2")))
        );
        
        let result = engine.execute_process(process, &kernel).await;
        assert!(result.is_ok());
        
        let context = result.unwrap();
        assert_eq!(context.current_step, 1); // Last executed step index
        
        // Check that state was set
        let step1_data: Option<String> = context.get_state("test_data").unwrap();
        assert_eq!(step1_data, Some("executed_step2".to_string()));
    }
    
    #[tokio::test]
    async fn test_process_execution_failure() {
        let engine = ProcessEngine::new();
        let kernel = semantic_kernel::KernelBuilder::new().build();
        
        let process: Arc<dyn Process> = Arc::new(
            WorkflowProcess::new("failing_process", "Process that fails")
                .add_step(Arc::new(TestStep::new("step1")))
                .add_step(Arc::new(TestStep::new("failing_step").with_failure()))
                .add_step(Arc::new(TestStep::new("step3")))
        );
        
        let result = engine.execute_process(process, &kernel).await;
        assert!(result.is_err());
        
        if let Err(ProcessError::StepExecutionFailed(msg)) = result {
            assert!(msg.contains("failing_step"));
            assert!(msg.contains("Test failure"));
        } else {
            panic!("Expected StepExecutionFailed error");
        }
    }
    
    #[tokio::test]
    async fn test_process_pause_and_resume() {
        let engine = ProcessEngine::new();
        let kernel = semantic_kernel::KernelBuilder::new().build();
        
        let process: Arc<dyn Process> = Arc::new(
            WorkflowProcess::new("pausing_process", "Process that pauses")
                .add_step(Arc::new(TestStep::new("step1")))
                .add_step(Arc::new(TestStep::new("pausing_step").with_pause()))
                .add_step(Arc::new(TestStep::new("step3")))
        );
        
        // Execute process - should pause after step 2
        let result = engine.execute_process(process.clone(), &kernel).await;
        assert!(result.is_ok());
        
        let mut context = result.unwrap();
        assert_eq!(context.current_step, 1); // Paused at step index 1 (pausing_step)
        
        // Resume the process
        context.current_step += 1; // Move to next step
        let result = engine.resume_process(process, context, &kernel).await;
        assert!(result.is_ok());
        
        let final_context = result.unwrap();
        assert_eq!(final_context.current_step, 2); // Completed step 3
    }
}