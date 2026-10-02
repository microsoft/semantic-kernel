//! Account Opening Business Process
//! 
//! This example demonstrates a realistic business process for opening bank accounts.
//! It showcases:
//! - Multi-step business workflow with validation steps
//! - Human approval integration and decision points
//! - Error handling and process recovery
//! - State persistence and audit trail
//! - Integration with external services (simulated)
//! - Business rule enforcement and compliance checks

use anyhow::Result;
use semantic_kernel::{Kernel, KernelBuilder};
use sk_process::{
    ProcessStep, ProcessContext, ProcessResult, StepResult, ProcessEngine, 
    WorkflowProcess, Process
};
use async_trait::async_trait;
use std::sync::Arc;
use serde::{Deserialize, Serialize};

/// Customer information for account opening
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CustomerInfo {
    pub first_name: String,
    pub last_name: String,
    pub email: String,
    pub phone: String,
    pub date_of_birth: String,
    pub address: Address,
    pub social_security_number: String,
    pub employment_status: String,
    pub annual_income: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Address {
    pub street: String,
    pub city: String,
    pub state: String,
    pub zip_code: String,
    pub country: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AccountRequest {
    pub account_type: String, // "checking", "savings", "business"
    pub initial_deposit: f64,
    pub customer_info: CustomerInfo,
    pub request_id: String,
}

/// Step 1: Validate customer information
#[derive(Debug, Clone)]
pub struct ValidateCustomerInfoStep;

#[async_trait]
impl ProcessStep for ValidateCustomerInfoStep {
    fn name(&self) -> &str {
        "ValidateCustomerInfo"
    }
    
    fn description(&self) -> &str {
        "Validate customer information and check for completeness"
    }

    async fn execute(
        &self,
        context: &mut ProcessContext,
        _kernel: &Kernel,
    ) -> ProcessResult<StepResult> {
        println!("🔍 Validating customer information...");
        
        let account_request: AccountRequest = context.get_state("account_request")?.unwrap();
        
        // Simulate validation logic
        let mut validation_errors = Vec::new();
        
        if account_request.customer_info.first_name.is_empty() {
            validation_errors.push("First name is required".to_string());
        }
        
        if account_request.customer_info.last_name.is_empty() {
            validation_errors.push("Last name is required".to_string());
        }
        
        if !account_request.customer_info.email.contains('@') {
            validation_errors.push("Invalid email format".to_string());
        }
        
        if account_request.customer_info.social_security_number.len() != 11 {
            validation_errors.push("Invalid SSN format".to_string());
        }
        
        if account_request.initial_deposit < 25.0 {
            validation_errors.push("Minimum initial deposit is $25.00".to_string());
        }
        
        if validation_errors.is_empty() {
            println!("   ✅ All customer information is valid");
            context.set_state("validation_passed", true)?;
            context.set_state("validation_errors", Vec::<String>::new())?;
            Ok(StepResult::success())
        } else {
            println!("   ❌ Validation failed with {} errors:", validation_errors.len());
            for error in &validation_errors {
                println!("      • {}", error);
            }
            context.set_state("validation_passed", false)?;
            context.set_state("validation_errors", validation_errors)?;
            Ok(StepResult::failure("Customer information validation failed"))
        }
    }
}

/// Step 2: Credit and background check
#[derive(Debug, Clone)]
pub struct CreditCheckStep;

#[async_trait]
impl ProcessStep for CreditCheckStep {
    fn name(&self) -> &str {
        "CreditCheck"
    }
    
    fn description(&self) -> &str {
        "Perform credit and background check on customer"
    }

    async fn execute(
        &self,
        context: &mut ProcessContext,
        _kernel: &Kernel,
    ) -> ProcessResult<StepResult> {
        println!("💳 Performing credit and background check...");
        
        // Simulate credit check delay
        tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;
        
        let account_request: AccountRequest = context.get_state("account_request")?.unwrap();
        
        // Simulate credit score based on income
        let credit_score = if account_request.customer_info.annual_income > 75000.0 {
            750 + (rand::random::<u16>() % 100) // 750-850
        } else if account_request.customer_info.annual_income > 35000.0 {
            650 + (rand::random::<u16>() % 100) // 650-750
        } else {
            550 + (rand::random::<u16>() % 100) // 550-650
        };
        
        println!("   📊 Credit score: {}", credit_score);
        
        let risk_level = if credit_score >= 750 {
            "LOW"
        } else if credit_score >= 650 {
            "MEDIUM"
        } else {
            "HIGH"
        };
        
        println!("   🎯 Risk level: {}", risk_level);
        
        context.set_state("credit_score", credit_score)?;
        context.set_state("risk_level", risk_level)?;
        
        // High risk accounts need manual approval
        let needs_manual_approval = risk_level == "HIGH" || credit_score < 600;
        context.set_state("needs_manual_approval", needs_manual_approval)?;
        
        if needs_manual_approval {
            println!("   ⚠️  Account flagged for manual approval due to risk level");
        } else {
            println!("   ✅ Credit check passed - automatic approval eligible");
        }
        
        Ok(StepResult::success())
    }
}

/// Step 3: Compliance and AML check
#[derive(Debug, Clone)]
pub struct ComplianceCheckStep;

#[async_trait]
impl ProcessStep for ComplianceCheckStep {
    fn name(&self) -> &str {
        "ComplianceCheck"
    }
    
    fn description(&self) -> &str {
        "Perform Anti-Money Laundering (AML) and compliance checks"
    }

    async fn execute(
        &self,
        context: &mut ProcessContext,
        _kernel: &Kernel,
    ) -> ProcessResult<StepResult> {
        println!("🔒 Performing compliance and AML checks...");
        
        // Simulate compliance check delay
        tokio::time::sleep(tokio::time::Duration::from_millis(300)).await;
        
        let account_request: AccountRequest = context.get_state("account_request")?.unwrap();
        
        // Simulate various compliance checks
        let mut compliance_flags = Vec::new();
        
        // Large initial deposit flag
        if account_request.initial_deposit > 10000.0 {
            compliance_flags.push("Large initial deposit (>$10K)".to_string());
        }
        
        // International address flag
        if account_request.customer_info.address.country != "USA" {
            compliance_flags.push("International address".to_string());
        }
        
        // Simulate random additional checks
        if rand::random::<f32>() < 0.1 {
            compliance_flags.push("Additional verification required".to_string());
        }
        
        let compliance_passed = compliance_flags.is_empty();
        
        if compliance_passed {
            println!("   ✅ All compliance checks passed");
        } else {
            println!("   ⚠️  Compliance flags detected:");
            for flag in &compliance_flags {
                println!("      • {}", flag);
            }
        }
        
        context.set_state("compliance_passed", compliance_passed)?;
        context.set_state("compliance_flags", compliance_flags)?;
        
        Ok(StepResult::success())
    }
}

/// Step 4: Manual approval step (simulates human decision)
#[derive(Debug, Clone)]
pub struct ManualApprovalStep;

#[async_trait]
impl ProcessStep for ManualApprovalStep {
    fn name(&self) -> &str {
        "ManualApproval"
    }
    
    fn description(&self) -> &str {
        "Manual approval by bank officer for high-risk accounts"
    }

    async fn execute(
        &self,
        context: &mut ProcessContext,
        _kernel: &Kernel,
    ) -> ProcessResult<StepResult> {
        let needs_manual_approval: bool = context.get_state("needs_manual_approval")?.unwrap_or(false);
        
        if !needs_manual_approval {
            println!("⏩ Skipping manual approval - automatic approval eligible");
            context.set_state("manual_approval_result", "NOT_REQUIRED")?;
            return Ok(StepResult::success());
        }
        
        println!("👤 Manual approval required - reviewing application...");
        
        let credit_score: u16 = context.get_state("credit_score")?.unwrap();
        let compliance_passed: bool = context.get_state("compliance_passed")?.unwrap_or(false);
        let account_request: AccountRequest = context.get_state("account_request")?.unwrap();
        
        // Simulate manual review delay
        tokio::time::sleep(tokio::time::Duration::from_millis(800)).await;
        
        // Simulate approval decision logic
        let approval_decision = if !compliance_passed {
            "REJECTED"
        } else if credit_score < 550 {
            "REJECTED"
        } else if credit_score < 600 && account_request.initial_deposit < 1000.0 {
            "REJECTED"
        } else if credit_score < 650 {
            "APPROVED_WITH_CONDITIONS"
        } else {
            "APPROVED"
        };
        
        println!("   🏛️  Bank officer decision: {}", approval_decision);
        
        let conditions = if approval_decision == "APPROVED_WITH_CONDITIONS" {
            vec![
                "Monthly fee: $15.00".to_string(),
                "Minimum balance: $500.00".to_string(),
                "90-day probationary period".to_string(),
            ]
        } else {
            Vec::new()
        };
        
        if !conditions.is_empty() {
            println!("   📋 Approval conditions:");
            for condition in &conditions {
                println!("      • {}", condition);
            }
        }
        
        context.set_state("manual_approval_result", approval_decision)?;
        context.set_state("approval_conditions", conditions)?;
        
        if approval_decision == "REJECTED" {
            Ok(StepResult::failure("Application rejected by manual review"))
        } else {
            Ok(StepResult::success())
        }
    }
}

/// Step 5: Create account
#[derive(Debug, Clone)]
pub struct CreateAccountStep;

#[async_trait]
impl ProcessStep for CreateAccountStep {
    fn name(&self) -> &str {
        "CreateAccount"
    }
    
    fn description(&self) -> &str {
        "Create the bank account and assign account number"
    }

    async fn execute(
        &self,
        context: &mut ProcessContext,
        _kernel: &Kernel,
    ) -> ProcessResult<StepResult> {
        println!("🏦 Creating bank account...");
        
        let account_request: AccountRequest = context.get_state("account_request")?.unwrap();
        
        // Generate account number
        let account_number = format!("ACC{}{}", 
            chrono::Utc::now().timestamp(),
            rand::random::<u16>() % 10000
        );
        
        println!("   📋 Account type: {}", account_request.account_type);
        println!("   🔢 Account number: {}", account_number);
        println!("   💰 Initial deposit: ${:.2}", account_request.initial_deposit);
        
        context.set_state("account_number", account_number.clone())?;
        context.set_state("account_created", true)?;
        context.set_state("creation_timestamp", chrono::Utc::now().to_rfc3339())?;
        
        println!("   ✅ Account created successfully: {}", account_number);
        
        Ok(StepResult::success())
    }
}

/// Step 6: Send welcome materials
#[derive(Debug, Clone)]
pub struct SendWelcomeMaterialsStep;

#[async_trait]
impl ProcessStep for SendWelcomeMaterialsStep {
    fn name(&self) -> &str {
        "SendWelcomeMaterials"
    }
    
    fn description(&self) -> &str {
        "Send welcome packet and account information to customer"
    }

    async fn execute(
        &self,
        context: &mut ProcessContext,
        _kernel: &Kernel,
    ) -> ProcessResult<StepResult> {
        println!("📧 Sending welcome materials to customer...");
        
        let account_request: AccountRequest = context.get_state("account_request")?.unwrap();
        let _account_number: String = context.get_state("account_number")?.unwrap();
        
        // Simulate sending email
        tokio::time::sleep(tokio::time::Duration::from_millis(200)).await;
        
        println!("   📧 Welcome email sent to: {}", account_request.customer_info.email);
        println!("   📬 Account information packet mailed to: {}, {} {} {}", 
                 account_request.customer_info.address.street,
                 account_request.customer_info.address.city,
                 account_request.customer_info.address.state,
                 account_request.customer_info.address.zip_code);
        
        context.set_state("welcome_materials_sent", true)?;
        context.set_state("notification_timestamp", chrono::Utc::now().to_rfc3339())?;
        
        println!("   ✅ Welcome materials sent successfully");
        
        Ok(StepResult::success())
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize environment and logging
    dotenv::dotenv().ok();
    tracing_subscriber::fmt::init();

    println!("🏦 Semantic Kernel Rust - Account Opening Business Process");
    println!("=========================================================\n");

    // Example 1: Successful account opening
    println!("Example 1: Successful Account Opening (Good Credit)");
    println!("=================================================");
    
    successful_account_opening().await?;

    // Example 2: Account opening requiring manual approval
    println!("\nExample 2: Account Opening with Manual Approval Required");
    println!("=======================================================");
    
    manual_approval_required().await?;

    // Example 3: Failed account opening due to validation errors
    println!("\nExample 3: Failed Account Opening (Validation Errors)");
    println!(" ===================================================");
    
    failed_account_opening().await?;

    println!("\n✅ Account Opening Business Process examples completed!");

    Ok(())
}

/// Example of successful account opening with good credit
async fn successful_account_opening() -> Result<()> {
    let kernel = KernelBuilder::new().build();
    let process_engine = ProcessEngine::new();
    
    // Create sample customer with good credit profile
    let account_request = AccountRequest {
        account_type: "checking".to_string(),
        initial_deposit: 1500.0,
        request_id: uuid::Uuid::new_v4().to_string(),
        customer_info: CustomerInfo {
            first_name: "John".to_string(),
            last_name: "Smith".to_string(),
            email: "john.smith@email.com".to_string(),
            phone: "555-123-4567".to_string(),
            date_of_birth: "1985-03-15".to_string(),
            social_security_number: "123-45-6789".to_string(),
            employment_status: "Full-time".to_string(),
            annual_income: 85000.0,
            address: Address {
                street: "123 Main St".to_string(),
                city: "Anytown".to_string(),
                state: "CA".to_string(),
                zip_code: "12345".to_string(),
                country: "USA".to_string(),
            },
        },
    };
    
    let mut initial_context = sk_process::ProcessContext::new(uuid::Uuid::new_v4());
    initial_context.set_state("account_request", account_request)?;
    
    let process = Arc::new(
        WorkflowProcess::new("AccountOpeningProcess", "Complete account opening workflow")
            .add_step(Arc::new(ValidateCustomerInfoStep))
            .add_step(Arc::new(CreditCheckStep))
            .add_step(Arc::new(ComplianceCheckStep))
            .add_step(Arc::new(ManualApprovalStep))
            .add_step(Arc::new(CreateAccountStep))
            .add_step(Arc::new(SendWelcomeMaterialsStep))
    );
    
    // Set the initial context state
    let mut context = initial_context;
    context = merge_context_with_process_execution(process.clone(), context, &kernel, &process_engine).await?;
    
    if let Some(account_number) = context.get_state::<String>("account_number")? {
        println!("🎉 Account opening completed successfully!");
        println!("   Account Number: {}", account_number);
        println!("   Process completed with {} state entries", context.state.len());
    }
    
    Ok(())
}

/// Example requiring manual approval due to credit risk
async fn manual_approval_required() -> Result<()> {
    let kernel = KernelBuilder::new().build();
    let process_engine = ProcessEngine::new();
    
    // Create sample customer with lower credit profile
    let account_request = AccountRequest {
        account_type: "savings".to_string(),
        initial_deposit: 250.0,
        request_id: uuid::Uuid::new_v4().to_string(),
        customer_info: CustomerInfo {
            first_name: "Jane".to_string(),
            last_name: "Doe".to_string(),
            email: "jane.doe@email.com".to_string(),
            phone: "555-987-6543".to_string(),
            date_of_birth: "1992-08-22".to_string(),
            social_security_number: "987-65-4321".to_string(),
            employment_status: "Part-time".to_string(),
            annual_income: 28000.0,
            address: Address {
                street: "456 Oak Ave".to_string(),
                city: "Other City".to_string(),
                state: "NY".to_string(),
                zip_code: "54321".to_string(),
                country: "USA".to_string(),
            },
        },
    };
    
    let mut initial_context = sk_process::ProcessContext::new(uuid::Uuid::new_v4());
    initial_context.set_state("account_request", account_request)?;
    
    let process = Arc::new(
        WorkflowProcess::new("AccountOpeningProcess", "Account opening with manual approval")
            .add_step(Arc::new(ValidateCustomerInfoStep))
            .add_step(Arc::new(CreditCheckStep))
            .add_step(Arc::new(ComplianceCheckStep))
            .add_step(Arc::new(ManualApprovalStep))
            .add_step(Arc::new(CreateAccountStep))
            .add_step(Arc::new(SendWelcomeMaterialsStep))
    );
    
    let context = merge_context_with_process_execution(process.clone(), initial_context, &kernel, &process_engine).await?;
    
    if let Some(account_number) = context.get_state::<String>("account_number")? {
        println!("🎉 Account opening completed with manual approval!");
        println!("   Account Number: {}", account_number);
        if let Some(conditions) = context.get_state::<Vec<String>>("approval_conditions")? {
            if !conditions.is_empty() {
                println!("   Special Conditions Apply:");
                for condition in conditions {
                    println!("     • {}", condition);
                }
            }
        }
    }
    
    Ok(())
}

/// Example of failed account opening due to validation errors
async fn failed_account_opening() -> Result<()> {
    let kernel = KernelBuilder::new().build();
    let process_engine = ProcessEngine::new();
    
    // Create sample customer with validation issues
    let account_request = AccountRequest {
        account_type: "checking".to_string(),
        initial_deposit: 10.0, // Below minimum
        request_id: uuid::Uuid::new_v4().to_string(),
        customer_info: CustomerInfo {
            first_name: "".to_string(), // Missing first name
            last_name: "Invalid".to_string(),
            email: "invalid-email".to_string(), // Invalid email
            phone: "555-000-0000".to_string(),
            date_of_birth: "1990-01-01".to_string(),
            social_security_number: "123-45".to_string(), // Invalid SSN
            employment_status: "Unemployed".to_string(),
            annual_income: 0.0,
            address: Address {
                street: "789 Pine St".to_string(),
                city: "No City".to_string(),
                state: "XX".to_string(),
                zip_code: "00000".to_string(),
                country: "USA".to_string(),
            },
        },
    };
    
    let mut initial_context = sk_process::ProcessContext::new(uuid::Uuid::new_v4());
    initial_context.set_state("account_request", account_request)?;
    
    let process = Arc::new(
        WorkflowProcess::new("AccountOpeningProcess", "Failed account opening demonstration")
            .add_step(Arc::new(ValidateCustomerInfoStep))
            .add_step(Arc::new(CreditCheckStep))
            .add_step(Arc::new(ComplianceCheckStep))
            .add_step(Arc::new(ManualApprovalStep))
            .add_step(Arc::new(CreateAccountStep))
            .add_step(Arc::new(SendWelcomeMaterialsStep))
    );
    
    match process_engine.execute_process(process, &kernel).await {
        Ok(_) => {
            println!("❌ Unexpected success - process should have failed");
        }
        Err(e) => {
            println!("❌ Account opening failed as expected: {}", e);
            println!("   This demonstrates proper error handling in business processes");
        }
    }
    
    Ok(())
}

/// Helper function to execute process and merge context
async fn merge_context_with_process_execution(
    process: Arc<WorkflowProcess>,
    mut context: sk_process::ProcessContext,
    kernel: &Kernel,
    engine: &ProcessEngine,
) -> Result<sk_process::ProcessContext> {
    // We need to execute the process step by step with our pre-initialized context
    let steps = process.steps();
    
    for (step_index, step) in steps.iter().enumerate() {
        context.current_step = step_index;
        
        match step.execute(&mut context, kernel).await {
            Ok(result) => {
                if !result.success {
                    return Err(anyhow::anyhow!("Step '{}' failed: {}", 
                        step.name(), 
                        result.error.unwrap_or_else(|| "Unknown error".to_string())
                    ));
                }
                
                if result.pause_process {
                    break;
                }
            }
            Err(e) => {
                return Err(anyhow::anyhow!("Step '{}' execution failed: {}", step.name(), e));
            }
        }
    }
    
    Ok(context)
}