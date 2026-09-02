//! Step 00: Basic Processes
//! 
//! This example demonstrates the creation of the simplest process with multiple steps.
//! It shows:
//! - Creating a process with sequential steps  
//! - Process state management and context passing
//! - Step execution lifecycle
//! - Error handling and process flow control
//! - Basic process orchestration patterns
//! 
//! A process is a sequence of steps that can be orchestrated to achieve a goal.
//! Each step can modify the process state and control execution flow.

use anyhow::Result;
use semantic_kernel::{Kernel, KernelBuilder};
use sk_process::{
    ProcessStep, ProcessContext, ProcessResult, StepResult, ProcessEngine, 
    WorkflowProcess
};
use async_trait::async_trait;
use std::sync::Arc;

/// A simple start step that begins the process
#[derive(Debug, Clone)]
pub struct StartStep;

#[async_trait]
impl ProcessStep for StartStep {
    fn name(&self) -> &str {
        "StartStep"
    }
    
    fn description(&self) -> &str {
        "The initial step that starts the process"
    }

    async fn execute(
        &self,
        context: &mut ProcessContext,
        _kernel: &Kernel,
    ) -> ProcessResult<StepResult> {
        println!("Step 1 - Start");
        println!("Process ID: {}", context.process_id);
        
        // Set some initial state
        context.set_state("step_count", 1)?;
        context.set_state("started", true)?;
        
        Ok(StepResult::success())
    }
}

/// A step that does some work
#[derive(Debug, Clone)]
pub struct DoSomeWorkStep;

#[async_trait]
impl ProcessStep for DoSomeWorkStep {
    fn name(&self) -> &str {
        "DoSomeWorkStep"
    }
    
    fn description(&self) -> &str {
        "A step that performs some work"
    }

    async fn execute(
        &self,
        context: &mut ProcessContext,
        _kernel: &Kernel,
    ) -> ProcessResult<StepResult> {
        println!("Step 2 - Doing Some Work...");
        
        // Update state
        let step_count: i32 = context.get_state("step_count")?.unwrap_or(0);
        context.set_state("step_count", step_count + 1)?;
        context.set_state("work_done", true)?;
        
        Ok(StepResult::success())
    }
}

/// A step that does more work
#[derive(Debug, Clone)]
pub struct DoMoreWorkStep;

#[async_trait]
impl ProcessStep for DoMoreWorkStep {
    fn name(&self) -> &str {
        "DoMoreWorkStep"
    }
    
    fn description(&self) -> &str {
        "A step that performs additional work"
    }

    async fn execute(
        &self,
        context: &mut ProcessContext,
        _kernel: &Kernel,
    ) -> ProcessResult<StepResult> {
        println!("Step 3 - Doing More Work...");
        
        // Update state
        let step_count: i32 = context.get_state("step_count")?.unwrap_or(0);
        context.set_state("step_count", step_count + 1)?;
        context.set_state("more_work_done", true)?;
        
        Ok(StepResult::success())
    }
}

/// The final step in the process
#[derive(Debug, Clone)]
pub struct LastStep;

#[async_trait]
impl ProcessStep for LastStep {
    fn name(&self) -> &str {
        "LastStep"
    }
    
    fn description(&self) -> &str {
        "The final step that completes the process"
    }

    async fn execute(
        &self,
        context: &mut ProcessContext,
        _kernel: &Kernel,
    ) -> ProcessResult<StepResult> {
        println!("Step 4 - Last Step - Process Complete!");
        
        // Final state update
        let step_count: i32 = context.get_state("step_count")?.unwrap_or(0);
        context.set_state("step_count", step_count + 1)?;
        context.set_state("completed", true)?;
        
        // Print final state
        println!("Final state:");
        println!("  Steps executed: {}", step_count + 1);
        println!("  Work done: {:?}", context.get_state::<bool>("work_done")?);
        println!("  More work done: {:?}", context.get_state::<bool>("more_work_done")?);
        
        Ok(StepResult::success())
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize environment and logging
    dotenv::dotenv().ok();
    tracing_subscriber::fmt::init();

    println!("🤖 Semantic Kernel Rust - Step 00: Basic Processes");
    println!("==================================================\n");

    // Example 1: Simple sequential process
    println!("Example 1: Simple Sequential Process");
    println!("===================================");
    
    simple_sequential_process().await?;

    // Example 2: Process with error handling
    println!("\nExample 2: Process with Error Handling");
    println!("=====================================");
    
    process_with_error_handling().await?;

    // Example 3: Process with conditional flow
    println!("\nExample 3: Process with Conditional Logic");
    println!("========================================");
    
    process_with_conditional_flow().await?;

    println!("\n✅ Step00 Basic Processes example completed!");

    Ok(())
}

/// Demonstrate a simple sequential process
async fn simple_sequential_process() -> Result<()> {
    // Create a kernel (can be basic since we're not using AI in this example)
    let kernel = KernelBuilder::new().build();
    
    // Create process engine
    let process_engine = ProcessEngine::new();
    
    // Create a workflow process with steps
    let process = Arc::new(
        WorkflowProcess::new("SimpleProcess", "A simple sequential process")
            .add_step(Arc::new(StartStep))
            .add_step(Arc::new(DoSomeWorkStep))
            .add_step(Arc::new(DoMoreWorkStep))
            .add_step(Arc::new(LastStep))
    );
    
    // Execute the process
    let result = process_engine.execute_process(process, &kernel).await?;
    
    println!("✅ Process '{}' completed successfully!", result.process_id);
    println!("Final state keys: {:?}", result.state.keys().collect::<Vec<_>>());
    
    Ok(())
}

/// Demonstrate a process with error handling
async fn process_with_error_handling() -> Result<()> {
    #[derive(Debug, Clone)]
    pub struct ErrorProneStep {
        name: String,
        should_fail: bool,
    }
    
    #[async_trait]
    impl ProcessStep for ErrorProneStep {
        fn name(&self) -> &str {
            &self.name
        }
        
        fn description(&self) -> &str {
            "A step that might fail"
        }
        
        async fn execute(
            &self,
            context: &mut ProcessContext,
            _kernel: &Kernel,
        ) -> ProcessResult<StepResult> {
            println!("🔄 Executing step: {}", self.name);
            
            if self.should_fail {
                println!("❌ Step {} encountered an error!", self.name);
                return Ok(StepResult {
                    success: false,
                    output: None,
                    error: Some(format!("Simulated error in {}", self.name)),
                    pause_process: false,
                });
            }
            
            context.set_state(&format!("{}_completed", self.name), true)?;
            println!("✅ Step {} completed successfully", self.name);
            
            Ok(StepResult::success())
        }
    }
    
    let kernel = KernelBuilder::new().build();
    let process_engine = ProcessEngine::new();
    
    // Create a process with one failing step
    let process = Arc::new(
        WorkflowProcess::new("ErrorHandlingProcess", "Process demonstrating error handling")
            .add_step(Arc::new(ErrorProneStep { 
                name: "Step1".to_string(), 
                should_fail: false 
            }))
            .add_step(Arc::new(ErrorProneStep { 
                name: "Step2".to_string(), 
                should_fail: true  // This step will fail
            }))
            .add_step(Arc::new(ErrorProneStep { 
                name: "Step3".to_string(), 
                should_fail: false 
            }))
    );
    
    // Execute the process and handle errors
    match process_engine.execute_process(process, &kernel).await {
        Ok(result) => {
            println!("✅ Process completed: {}", result.process_id);
        }
        Err(e) => {
            println!("❌ Process failed with error: {}", e);
            println!("This demonstrates how process errors are handled gracefully");
        }
    }
    
    Ok(())
}

/// Demonstrate process with conditional logic
async fn process_with_conditional_flow() -> Result<()> {
    #[derive(Debug, Clone)]
    pub struct ConditionalStep {
        name: String,
        condition_key: String,
    }
    
    #[async_trait]
    impl ProcessStep for ConditionalStep {
        fn name(&self) -> &str {
            &self.name
        }
        
        fn description(&self) -> &str {
            "A step that makes conditional decisions"
        }
        
        async fn execute(
            &self,
            context: &mut ProcessContext,
            _kernel: &Kernel,
        ) -> ProcessResult<StepResult> {
            println!("🔄 Executing conditional step: {}", self.name);
            
            // Get current step count to make decisions
            let step_count: i32 = context.get_state("step_count")?.unwrap_or(0);
            
            match self.name.as_str() {
                "DecisionStep" => {
                    context.set_state("step_count", step_count + 1)?;
                    
                    // Make a decision based on some condition
                    let should_continue = step_count < 2;
                    context.set_state("should_continue", should_continue)?;
                    
                    println!("🤔 Decision: {} (step_count: {})", 
                        if should_continue { "Continue processing" } else { "Stop processing" }, 
                        step_count + 1
                    );
                }
                "ProcessingStep" => {
                    let should_continue: bool = context.get_state("should_continue")?.unwrap_or(false);
                    
                    if should_continue {
                        println!("✅ Processing continues...");
                        context.set_state("processing_done", true)?;
                    } else {
                        println!("⏹️  Processing skipped based on condition");
                        context.set_state("processing_skipped", true)?;
                    }
                }
                "FinalStep" => {
                    let processing_done: bool = context.get_state("processing_done")?.unwrap_or(false);
                    let processing_skipped: bool = context.get_state("processing_skipped")?.unwrap_or(false);
                    
                    println!("🏁 Final step - Summary:");
                    println!("   Processing done: {}", processing_done);
                    println!("   Processing skipped: {}", processing_skipped);
                }
                _ => {}
            }
            
            Ok(StepResult::success())
        }
    }
    
    let kernel = KernelBuilder::new().build();
    let process_engine = ProcessEngine::new();
    
    // Run the process multiple times to see different outcomes
    for iteration in 1..=3 {
        println!("\n--- Iteration {} ---", iteration);
        
        let process = Arc::new(
            WorkflowProcess::new(
                &format!("ConditionalProcess_{}", iteration), 
                "Process demonstrating conditional logic"
            )
            .add_step(Arc::new(ConditionalStep { 
                name: "DecisionStep".to_string(),
                condition_key: "should_continue".to_string(),
            }))
            .add_step(Arc::new(ConditionalStep { 
                name: "ProcessingStep".to_string(),
                condition_key: "should_continue".to_string(),
            }))
            .add_step(Arc::new(ConditionalStep { 
                name: "FinalStep".to_string(),
                condition_key: "should_continue".to_string(),
            }))
        );
        
        let result = process_engine.execute_process(process, &kernel).await?;
        println!("Process {} completed with {} state entries", 
            result.process_id, 
            result.state.len()
        );
    }
    
    Ok(())
}