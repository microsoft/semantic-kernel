//! Invoice Processing Workflow Example
//! 
//! Demonstrates the SK Process Framework with a realistic business workflow:
//! 1. AI extraction of invoice data
//! 2. Human approval step  
//! 3. Final processing and calculation

use anyhow::Result;
use async_trait::async_trait;
use semantic_kernel::{Kernel, KernelBuilder};
use sk_process::{
    ProcessEngine, WorkflowProcess, ProcessContext, Process, ProcessStep, StepResult, ProcessResult,
    steps::{AIExtractionStep, HumanApprovalStep, DataTransformStep, ApprovalDecision},
    ProcessEvent
};
use std::sync::Arc;
use tracing::{info, error, warn};
use uuid::Uuid;

/// Helper step to set up initial data in the process context
struct DataSetupStep {
    name: String,
    key: String,
    value: String,
}

impl DataSetupStep {
    fn new(key: impl Into<String>, value: impl Into<String>) -> Self {
        let key_str = key.into();
        Self {
            name: format!("setup_{}", key_str),
            key: key_str,
            value: value.into(),
        }
    }
}

#[async_trait]
impl ProcessStep for DataSetupStep {
    fn name(&self) -> &str {
        &self.name
    }
    
    fn description(&self) -> &str {
        "Set up initial data in process context"
    }
    
    async fn execute(
        &self,
        context: &mut ProcessContext,
        _kernel: &Kernel,
    ) -> ProcessResult<StepResult> {
        context.set_state(&self.key, &self.value)?;
        info!("Set up initial data: {} = {}", self.key, self.value.len());
        Ok(StepResult::success())
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        .init();

    info!("Starting Invoice Processing Workflow Demo");

    // Create kernel with basic configuration
    let kernel = KernelBuilder::new().build();

    // Create the process engine
    let engine = ProcessEngine::new();

    // Sample invoice text to process
    let sample_invoice = r#"
INVOICE

ABC Company Ltd.
123 Business Street
City, State 12345

Invoice Number: INV-2024-001
Date: March 15, 2024
Due Date: April 15, 2024

Bill To:
XYZ Corporation  
456 Client Avenue
Town, State 67890

Description                  Quantity    Unit Price    Amount
Consulting Services             40 hrs      $150.00    $6,000.00
Software License                 1 ea       $500.00      $500.00
Training Session                 8 hrs       $75.00      $600.00

Subtotal:                                              $7,100.00
Tax (10%):                                               $710.00
Total:                                                 $7,810.00

Payment Terms: Net 30 days
"#;

    // Build the invoice processing workflow
    let workflow: Arc<dyn Process> = Arc::new(
        WorkflowProcess::new(
            "invoice_processing",
            "Complete invoice processing workflow with AI extraction and human approval"
        )
        .add_step(Arc::new(DataSetupStep::new("invoice_text", sample_invoice)))
        .add_step(Arc::new(AIExtractionStep::invoice_extraction()))
        .add_step(Arc::new(HumanApprovalStep::invoice_approval().with_auto_approve(true))) // Auto-approve for demo
        .add_step(Arc::new(DataTransformStep::calculate_invoice_totals()))
    );

    info!("Created workflow with {} steps", workflow.steps().len());

    // Execute the workflow
    match engine.execute_process(workflow.clone(), &kernel).await {
        Ok(final_context) => {
            info!("✅ Invoice processing workflow completed successfully!");
            
            // Display the results
            display_workflow_results(&final_context).await?;
            
            // Show event log
            display_event_log(&engine).await;
            
        }
        Err(e) => {
            error!("❌ Invoice processing workflow failed: {}", e);
            
            // Still show what events we captured
            display_event_log(&engine).await;
            
            return Err(e.into());
        }
    }

    // Demonstrate pause/resume functionality
    info!("\n🔄 Demonstrating pause/resume functionality...");
    demonstrate_pause_resume(&engine, &kernel).await?;

    Ok(())
}

async fn display_workflow_results(context: &ProcessContext) -> Result<()> {
    info!("\n📊 Workflow Results:");
    info!("Process ID: {}", context.process_id);
    info!("Completed Steps: {}", context.current_step + 1);
    
    // Show extracted data
    if let Ok(Some(extracted_data)) = context.get_state::<serde_json::Value>("extracted_data") {
        info!("\n📝 Extracted Invoice Data:");
        info!("{}", serde_json::to_string_pretty(&extracted_data)?);
    }
    
    // Show approval decision
    if let Ok(Some(approval)) = context.get_state::<ApprovalDecision>("approval_decision") {
        info!("\n✅ Approval Decision:");
        info!("Approved: {}", approval.approved);
        info!("Approver: {}", approval.approver);
        if let Some(comments) = &approval.comments {
            info!("Comments: {}", comments);
        }
    }
    
    // Show final processed data
    if let Ok(Some(processed_data)) = context.get_state::<serde_json::Value>("processed_invoice") {
        info!("\n🎯 Final Processed Invoice:");
        info!("{}", serde_json::to_string_pretty(&processed_data)?);
    }
    
    Ok(())
}

async fn display_event_log(engine: &ProcessEngine) {
    info!("\n📜 Process Event Log:");
    let event_log = engine.event_log();
    let events = event_log.get_all_events();
    
    for event in events {
        let timestamp = event.timestamp().format("%H:%M:%S%.3f");
        match event {
            ProcessEvent::ProcessStarted { process_name, process_id, .. } => {
                info!("[{}] 🚀 Process '{}' started ({})", timestamp, process_name, process_id);
            }
            ProcessEvent::StepStarted { step_name, step_index, .. } => {
                info!("[{}] ▶️  Step {} '{}' started", timestamp, step_index + 1, step_name);
            }
            ProcessEvent::StepCompleted { step_name, success, .. } => {
                if success {
                    info!("[{}] ✅ Step '{}' completed successfully", timestamp, step_name);
                } else {
                    warn!("[{}] ❌ Step '{}' failed", timestamp, step_name);
                }
            }
            ProcessEvent::ProcessPaused { step_name, .. } => {
                info!("[{}] ⏸️  Process paused after step '{}'", timestamp, step_name);
            }
            ProcessEvent::ProcessResumed { step_index, .. } => {
                info!("[{}] ▶️  Process resumed from step {}", timestamp, step_index + 1);
            }
            ProcessEvent::ProcessCompleted { .. } => {
                info!("[{}] 🏁 Process completed successfully", timestamp);
            }
            ProcessEvent::ProcessFailed { error, .. } => {
                error!("[{}] 💥 Process failed: {}", timestamp, error);
            }
        }
    }
    
    info!("\nTotal events logged: {}", event_log.event_count());
}

async fn demonstrate_pause_resume(engine: &ProcessEngine, kernel: &Kernel) -> Result<()> {
    // Simple invoice for testing
    let simple_invoice = r#"
Invoice #TEST-001
From: Test Vendor
Amount: $50.00
Date: Today
"#;

    // Create a workflow that will pause for human approval (no auto-approve)
    let workflow: Arc<dyn Process> = Arc::new(
        WorkflowProcess::new(
            "pausing_invoice_process",
            "Invoice processing that pauses for real human approval"
        )
        .add_step(Arc::new(DataSetupStep::new("invoice_text", simple_invoice)))
        .add_step(Arc::new(AIExtractionStep::invoice_extraction()))
        .add_step(Arc::new(HumanApprovalStep::invoice_approval())) // No auto-approve
        .add_step(Arc::new(DataTransformStep::calculate_invoice_totals()))
    );

    // Simple invoice for testing
    let simple_invoice = r#"
Invoice #TEST-001
From: Test Vendor
Amount: $50.00
Date: Today
"#;

    info!("Executing workflow that will pause for approval...");

    // Execute - should pause at approval step
    match engine.execute_process(workflow.clone(), kernel).await {
        Ok(paused_context) => {
            info!("✅ Process paused as expected");
            
            // In a real application, this is where you'd:
            // 1. Send notifications to approvers
            // 2. Store the context in a database
            // 3. Wait for approval through a web interface or API
            
            // For demo purposes, simulate approval
            info!("Simulating human approval...");
            let mut resume_context = paused_context;
            
            // Simulate an approval decision
            let approval = ApprovalDecision::new(true, "demo_approver")
                .with_comments("Approved for demo purposes");
            
            resume_context.set_state("approval_decision", approval)?;
            
            info!("Resuming process with approval...");
            
            // Resume the process
            match engine.resume_process(workflow, resume_context, kernel).await {
                Ok(final_context) => {
                    info!("✅ Process resumed and completed successfully!");
                    
                    // Show final state
                    if let Ok(Some(processed_data)) = final_context.get_state::<serde_json::Value>("processed_invoice") {
                        info!("Final processed data: {}", serde_json::to_string_pretty(&processed_data)?);
                    }
                }
                Err(e) => {
                    error!("❌ Process resume failed: {}", e);
                    return Err(e.into());
                }
            }
        }
        Err(e) => {
            error!("❌ Process execution failed: {}", e);
            return Err(e.into());
        }
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use sk_process::{ProcessError, ProcessState};

    #[tokio::test]
    async fn test_invoice_workflow_execution() {
        // Initialize tracing for tests
        let _ = tracing_subscriber::fmt().try_init();

        let kernel = KernelBuilder::new().build();
        let engine = ProcessEngine::new();

        // Create a custom workflow that sets up test data
        struct TestInvoiceStep {
            name: String,
        }
        
        impl TestInvoiceStep {
            fn new() -> Self {
                Self {
                    name: "setup_test_data".to_string(),
                }
            }
        }
        
        #[async_trait::async_trait]
        impl ProcessStep for TestInvoiceStep {
            fn name(&self) -> &str {
                &self.name
            }
            
            fn description(&self) -> &str {
                "Set up test invoice data"
            }
            
            async fn execute(
                &self,
                context: &mut ProcessContext,
                _kernel: &Kernel,
            ) -> ProcessResult<StepResult> {
                context.set_state("invoice_text", "Test invoice with amount $100")?;
                Ok(StepResult::success())
            }
        }

        // Create a test workflow with data setup
        let workflow: Arc<dyn Process> = Arc::new(
            WorkflowProcess::new("test_invoice", "Test invoice processing")
                .add_step(Arc::new(TestInvoiceStep::new()))
                .add_step(Arc::new(AIExtractionStep::invoice_extraction()))
                .add_step(Arc::new(HumanApprovalStep::invoice_approval().with_auto_approve(true)))
        );

        let result = engine.execute_process(workflow, &kernel).await;
        assert!(result.is_ok());

        let final_context = result.unwrap();
        
        // Check that extracted data was created
        let extracted: Option<serde_json::Value> = final_context.get_state("extracted_data").unwrap();
        assert!(extracted.is_some());

        // Check that approval was recorded
        let approval: Option<ApprovalDecision> = final_context.get_state("approval_decision").unwrap();
        assert!(approval.is_some());
        assert!(approval.unwrap().approved);
    }

    #[tokio::test]
    async fn test_workflow_validation() {
        let workflow = WorkflowProcess::new("test", "Test workflow")
            .add_step(Arc::new(AIExtractionStep::new("test", "test", "", "input", "output"))); // Empty prompt

        let result = workflow.validate();
        assert!(result.is_err());
        
        if let Err(ProcessError::ValidationFailed(msg)) = result {
            assert!(msg.contains("empty"));
        }
    }

    #[tokio::test]
    async fn test_event_logging() {
        let kernel = KernelBuilder::new().build();
        let engine = ProcessEngine::new();

        let workflow = Arc::new(
            WorkflowProcess::new("event_test", "Test event logging")
                .add_step(Arc::new(AIExtractionStep::invoice_extraction()))
        );

        let mut context = ProcessContext::new(Uuid::new_v4());
        context.set_state("invoice_text", "Test invoice").unwrap();

        let _result = engine.execute_process(workflow, &kernel).await;

        let event_log = engine.event_log();
        let events = event_log.get_all_events();
        
        // Should have at least: ProcessStarted, StepStarted, StepCompleted, ProcessCompleted
        assert!(events.len() >= 4);
        
        // Check event types
        let has_process_started = events.iter().any(|e| matches!(e, ProcessEvent::ProcessStarted { .. }));
        let has_step_started = events.iter().any(|e| matches!(e, ProcessEvent::StepStarted { .. }));
        
        assert!(has_process_started);
        assert!(has_step_started);
    }
}