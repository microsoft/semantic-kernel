//! Pre-built process steps for common workflow patterns

use crate::{ProcessContext, ProcessError, ProcessResult, ProcessStep, StepResult};
use async_trait::async_trait;
use semantic_kernel::Kernel;
use serde::{Deserialize, Serialize};
use tracing::{info, debug, warn};

/// Step that uses AI to extract information from text
#[derive(Debug, Clone)]
pub struct AIExtractionStep {
    name: String,
    description: String,
    prompt_template: String,
    input_key: String,
    output_key: String,
}

impl AIExtractionStep {
    /// Create a new AI extraction step
    pub fn new(
        name: impl Into<String>,
        description: impl Into<String>,
        prompt_template: impl Into<String>,
        input_key: impl Into<String>,
        output_key: impl Into<String>,
    ) -> Self {
        Self {
            name: name.into(),
            description: description.into(),
            prompt_template: prompt_template.into(),
            input_key: input_key.into(),
            output_key: output_key.into(),
        }
    }
    
    /// Create an invoice extraction step
    pub fn invoice_extraction() -> Self {
        Self::new(
            "invoice_extraction",
            "Extract structured data from invoice text using AI",
            r#"Extract the following information from this invoice text and return it as JSON:
- vendor_name: The name of the vendor/supplier
- invoice_number: The invoice number
- total_amount: The total amount due
- due_date: The due date (if mentioned)
- line_items: Array of items with description and amount

Invoice text:
{{input_text}}

Return only valid JSON without any markdown formatting or additional text."#,
            "invoice_text",
            "extracted_data"
        )
    }
}

#[async_trait]
impl ProcessStep for AIExtractionStep {
    fn name(&self) -> &str {
        &self.name
    }
    
    fn description(&self) -> &str {
        &self.description
    }
    
    async fn execute(
        &self,
        context: &mut ProcessContext,
        kernel: &Kernel,
    ) -> ProcessResult<StepResult> {
        debug!("Executing AI extraction step: {}", self.name);
        
        // Get input text from context
        let input_text: String = context
            .get_state(&self.input_key)?
            .ok_or_else(|| ProcessError::StateError(
                format!("Input key '{}' not found in context", self.input_key)
            ))?;
        
        // Prepare prompt by substituting variables
        let prompt = self.prompt_template.replace("{{input_text}}", &input_text);
        
        // Execute AI prompt
        match kernel.invoke_prompt_async(&prompt).await {
            Ok(response) => {
                debug!("AI extraction completed successfully");
                
                // Try to parse as JSON to validate the response
                match serde_json::from_str::<serde_json::Value>(&response) {
                    Ok(json_value) => {
                        // Store the extracted data in context
                        context.set_state(&self.output_key, json_value)?;
                        
                        info!("Successfully extracted data from input using AI");
                        Ok(StepResult::success())
                    }
                    Err(_) => {
                        // If not valid JSON, store as string and warn
                        warn!("AI response was not valid JSON, storing as string");
                        context.set_state(&self.output_key, response)?;
                        Ok(StepResult::success())
                    }
                }
            }
            Err(e) => {
                warn!("AI extraction failed: {}", e);
                Err(ProcessError::StepExecutionFailed(
                    format!("AI extraction failed: {}", e)
                ))
            }
        }
    }
    
    fn validate(&self) -> ProcessResult<()> {
        if self.prompt_template.is_empty() {
            return Err(ProcessError::ValidationFailed(
                "Prompt template cannot be empty".to_string()
            ));
        }
        
        if self.input_key.is_empty() || self.output_key.is_empty() {
            return Err(ProcessError::ValidationFailed(
                "Input and output keys cannot be empty".to_string()
            ));
        }
        
        Ok(())
    }
}

/// Data structure for human approval decisions
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApprovalDecision {
    pub approved: bool,
    pub comments: Option<String>,
    pub modified_data: Option<serde_json::Value>,
    pub approver: String,
    pub timestamp: chrono::DateTime<chrono::Utc>,
}

impl ApprovalDecision {
    /// Create a new approval decision
    pub fn new(approved: bool, approver: impl Into<String>) -> Self {
        Self {
            approved,
            comments: None,
            modified_data: None,
            approver: approver.into(),
            timestamp: chrono::Utc::now(),
        }
    }
    
    /// Add comments to the decision
    pub fn with_comments(mut self, comments: impl Into<String>) -> Self {
        self.comments = Some(comments.into());
        self
    }
    
    /// Add modified data to the decision
    pub fn with_modified_data(mut self, data: serde_json::Value) -> Self {
        self.modified_data = Some(data);
        self
    }
}

/// Step that requires human approval before proceeding
#[derive(Debug, Clone)]
pub struct HumanApprovalStep {
    name: String,
    description: String,
    data_key: String,
    approval_key: String,
    auto_approve: bool,
    approval_timeout_seconds: Option<u64>,
}

impl HumanApprovalStep {
    /// Create a new human approval step
    pub fn new(
        name: impl Into<String>,
        description: impl Into<String>,
        data_key: impl Into<String>,
        approval_key: impl Into<String>,
    ) -> Self {
        Self {
            name: name.into(),
            description: description.into(),
            data_key: data_key.into(),
            approval_key: approval_key.into(),
            auto_approve: false,
            approval_timeout_seconds: None,
        }
    }
    
    /// Create an invoice approval step
    pub fn invoice_approval() -> Self {
        Self::new(
            "invoice_approval",
            "Human approval required for invoice processing",
            "extracted_data",
            "approval_decision"
        )
    }
    
    /// Enable auto-approval for testing
    pub fn with_auto_approve(mut self, auto_approve: bool) -> Self {
        self.auto_approve = auto_approve;
        self
    }
    
    /// Set approval timeout
    pub fn with_timeout(mut self, timeout_seconds: u64) -> Self {
        self.approval_timeout_seconds = Some(timeout_seconds);
        self
    }
}

#[async_trait]
impl ProcessStep for HumanApprovalStep {
    fn name(&self) -> &str {
        &self.name
    }
    
    fn description(&self) -> &str {
        &self.description
    }
    
    async fn execute(
        &self,
        context: &mut ProcessContext,
        _kernel: &Kernel,
    ) -> ProcessResult<StepResult> {
        debug!("Executing human approval step: {}", self.name);
        
        // Get the data to be approved
        let data_to_approve: serde_json::Value = context
            .get_state(&self.data_key)?
            .ok_or_else(|| ProcessError::StateError(
                format!("Data key '{}' not found in context", self.data_key)
            ))?;
        
        info!("Human approval required for data: {}", serde_json::to_string_pretty(&data_to_approve).unwrap_or_else(|_| "Invalid JSON".to_string()));
        
        // Check if approval decision is already provided (for resume scenarios)
        if let Ok(Some(decision)) = context.get_state::<ApprovalDecision>(&self.approval_key) {
            info!("Found existing approval decision: approved={}", decision.approved);
            
            if decision.approved {
                // If there's modified data, update the original data
                if let Some(modified_data) = &decision.modified_data {
                    context.set_state(&self.data_key, modified_data.clone())?;
                    info!("Applied modified data from approval decision");
                }
                
                return Ok(StepResult::success());
            } else {
                return Ok(StepResult::failure("Request was rejected by approver"));
            }
        }
        
        // Auto-approve for testing scenarios
        if self.auto_approve {
            let decision = ApprovalDecision::new(true, "auto-approver")
                .with_comments("Auto-approved for testing");
            
            context.set_state(&self.approval_key, decision)?;
            info!("Auto-approved request for testing");
            return Ok(StepResult::success());
        }
        
        // In a real implementation, this would:
        // 1. Send notification to approvers (email, Slack, etc.)
        // 2. Create a pending approval record in a database
        // 3. Provide a web interface for approval
        // 4. Pause the process until approval is received
        
        info!("Process paused pending human approval");
        info!("Approval required for: {}", self.description);
        info!("Data to approve: {}", serde_json::to_string_pretty(&data_to_approve).unwrap_or_else(|_| "Invalid JSON".to_string()));
        
        // Store the request details for the approval system
        let approval_request = serde_json::json!({
            "process_id": context.process_id,
            "step_name": self.name,
            "description": self.description,
            "data": data_to_approve,
            "requested_at": chrono::Utc::now(),
            "timeout_seconds": self.approval_timeout_seconds
        });
        
        context.set_state("pending_approval_request", approval_request)?;
        
        // Pause the process to wait for human approval
        Ok(StepResult::success_with_pause())
    }
    
    fn validate(&self) -> ProcessResult<()> {
        if self.data_key.is_empty() || self.approval_key.is_empty() {
            return Err(ProcessError::ValidationFailed(
                "Data key and approval key cannot be empty".to_string()
            ));
        }
        Ok(())
    }
}

/// Step that simulates a simple data transformation
#[derive(Debug)]
pub struct DataTransformStep {
    name: String,
    description: String,
    input_key: String,
    output_key: String,
    transformation: fn(&serde_json::Value) -> Result<serde_json::Value, String>,
}

impl Clone for DataTransformStep {
    fn clone(&self) -> Self {
        Self {
            name: self.name.clone(),
            description: self.description.clone(),
            input_key: self.input_key.clone(),
            output_key: self.output_key.clone(),
            transformation: self.transformation,
        }
    }
}

impl DataTransformStep {
    /// Create a new data transformation step
    pub fn new(
        name: impl Into<String>,
        description: impl Into<String>,
        input_key: impl Into<String>,
        output_key: impl Into<String>,
        transformation: fn(&serde_json::Value) -> Result<serde_json::Value, String>,
    ) -> Self {
        Self {
            name: name.into(),
            description: description.into(),
            input_key: input_key.into(),
            output_key: output_key.into(),
            transformation,
        }
    }
    
    /// Create a step that calculates invoice totals
    pub fn calculate_invoice_totals() -> Self {
        Self::new(
            "calculate_totals",
            "Calculate invoice totals and apply business rules",
            "extracted_data",
            "processed_invoice",
            |data| {
                let mut result = data.clone();
                
                // Add calculated fields
                if let Some(obj) = result.as_object_mut() {
                    obj.insert("processing_date".to_string(), 
                              serde_json::Value::String(chrono::Utc::now().to_rfc3339()));
                    obj.insert("status".to_string(), 
                              serde_json::Value::String("approved".to_string()));
                    
                    // Calculate tax if not present
                    if let Some(total) = obj.get("total_amount").and_then(|v| v.as_str()) {
                        if let Ok(amount) = total.parse::<f64>() {
                            let tax = amount * 0.1; // 10% tax
                            obj.insert("calculated_tax".to_string(), 
                                      serde_json::Value::Number(serde_json::Number::from_f64(tax).unwrap_or_else(|| serde_json::Number::from(0))));
                        }
                    }
                }
                
                Ok(result)
            }
        )
    }
}

#[async_trait]
impl ProcessStep for DataTransformStep {
    fn name(&self) -> &str {
        &self.name
    }
    
    fn description(&self) -> &str {
        &self.description
    }
    
    async fn execute(
        &self,
        context: &mut ProcessContext,
        _kernel: &Kernel,
    ) -> ProcessResult<StepResult> {
        debug!("Executing data transformation step: {}", self.name);
        
        // Get input data
        let input_data: serde_json::Value = context
            .get_state(&self.input_key)?
            .ok_or_else(|| ProcessError::StateError(
                format!("Input key '{}' not found in context", self.input_key)
            ))?;
        
        // Apply transformation
        match (self.transformation)(&input_data) {
            Ok(output_data) => {
                context.set_state(&self.output_key, output_data)?;
                info!("Data transformation completed successfully");
                Ok(StepResult::success())
            }
            Err(e) => {
                warn!("Data transformation failed: {}", e);
                Err(ProcessError::StepExecutionFailed(
                    format!("Data transformation failed: {}", e)
                ))
            }
        }
    }
    
    fn validate(&self) -> ProcessResult<()> {
        if self.input_key.is_empty() || self.output_key.is_empty() {
            return Err(ProcessError::ValidationFailed(
                "Input and output keys cannot be empty".to_string()
            ));
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use semantic_kernel::KernelBuilder;
    use uuid::Uuid;
    
    #[tokio::test]
    async fn test_ai_extraction_step() {
        let kernel = KernelBuilder::new().build();
        let mut context = ProcessContext::new(Uuid::new_v4());
        
        // Set up input data
        context.set_state("invoice_text", "Invoice #12345 from ACME Corp for $100.00").unwrap();
        
        let step = AIExtractionStep::new(
            "test_extraction",
            "Test AI extraction",
            "Please extract: {{input_text}}",
            "invoice_text",
            "extracted_data"
        );
        
        let result = step.execute(&mut context, &kernel).await;
        assert!(result.is_ok());
        
        // Check that output was stored
        let extracted: Option<String> = context.get_state("extracted_data").unwrap();
        assert!(extracted.is_some());
    }
    
    #[tokio::test]
    async fn test_human_approval_step_auto_approve() {
        let kernel = KernelBuilder::new().build();
        let mut context = ProcessContext::new(Uuid::new_v4());
        
        // Set up data to approve
        let data = serde_json::json!({
            "vendor": "ACME Corp",
            "amount": 100.0
        });
        context.set_state("test_data", data).unwrap();
        
        let step = HumanApprovalStep::new(
            "test_approval",
            "Test approval",
            "test_data",
            "approval_result"
        ).with_auto_approve(true);
        
        let result = step.execute(&mut context, &kernel).await;
        assert!(result.is_ok());
        
        // Check that approval decision was stored
        let decision: Option<ApprovalDecision> = context.get_state("approval_result").unwrap();
        assert!(decision.is_some());
        assert!(decision.unwrap().approved);
    }
    
    #[tokio::test]
    async fn test_human_approval_step_pause() {
        let kernel = KernelBuilder::new().build();
        let mut context = ProcessContext::new(Uuid::new_v4());
        
        // Set up data to approve
        let data = serde_json::json!({
            "vendor": "ACME Corp",
            "amount": 100.0
        });
        context.set_state("test_data", data).unwrap();
        
        let step = HumanApprovalStep::new(
            "test_approval",
            "Test approval",
            "test_data",
            "approval_result"
        ); // No auto-approve
        
        let result = step.execute(&mut context, &kernel).await;
        assert!(result.is_ok());
        
        let step_result = result.unwrap();
        assert!(step_result.pause_process); // Should pause for human approval
        
        // Check that pending approval request was stored
        let request: Option<serde_json::Value> = context.get_state("pending_approval_request").unwrap();
        assert!(request.is_some());
    }
    
    #[tokio::test]
    async fn test_data_transform_step() {
        let kernel = KernelBuilder::new().build();
        let mut context = ProcessContext::new(Uuid::new_v4());
        
        // Set up input data
        let input_data = serde_json::json!({
            "total_amount": "100.00",
            "vendor": "ACME Corp"
        });
        context.set_state("extracted_data", input_data).unwrap();
        
        let step = DataTransformStep::calculate_invoice_totals();
        
        let result = step.execute(&mut context, &kernel).await;
        assert!(result.is_ok());
        
        // Check that output was processed
        let output: Option<serde_json::Value> = context.get_state("processed_invoice").unwrap();
        assert!(output.is_some());
        
        let output_data = output.unwrap();
        assert!(output_data.get("processing_date").is_some());
        assert!(output_data.get("status").is_some());
        assert!(output_data.get("calculated_tax").is_some());
    }
    
    #[test]
    fn test_approval_decision() {
        let decision = ApprovalDecision::new(true, "test_user")
            .with_comments("Looks good")
            .with_modified_data(serde_json::json!({"modified": true}));
        
        assert!(decision.approved);
        assert_eq!(decision.approver, "test_user");
        assert_eq!(decision.comments, Some("Looks good".to_string()));
        assert!(decision.modified_data.is_some());
    }
}