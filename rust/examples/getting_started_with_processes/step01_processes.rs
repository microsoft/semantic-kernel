//! Step 01: Process Builder Patterns
//! 
//! This example demonstrates advanced process construction patterns and dynamic
//! process building capabilities. It shows:
//! - Process builder pattern with fluent API
//! - Dynamic step addition based on conditions  
//! - Process composition and step reusability
//! - Advanced state management patterns
//! - Process validation and optimization

use anyhow::Result;
use semantic_kernel::{Kernel, KernelBuilder};
use sk_process::{
    ProcessStep, ProcessContext, ProcessResult, StepResult, ProcessEngine, 
    WorkflowProcess
};
use async_trait::async_trait;
use std::sync::Arc;

/// A configurable step that can be customized via builder pattern
#[derive(Debug, Clone)]
pub struct ConfigurableStep {
    name: String,
    description: String,
    operation: String,
    sleep_duration: Option<u64>,
    should_fail: bool,
    output_data: Option<String>,
}

impl ConfigurableStep {
    /// Create a new configurable step with builder pattern
    pub fn builder(name: impl Into<String>) -> ConfigurableStepBuilder {
        ConfigurableStepBuilder {
            name: name.into(),
            description: "A configurable step".to_string(),
            operation: "default".to_string(),
            sleep_duration: None,
            should_fail: false,
            output_data: None,
        }
    }
}

pub struct ConfigurableStepBuilder {
    name: String,
    description: String,
    operation: String,
    sleep_duration: Option<u64>,
    should_fail: bool,
    output_data: Option<String>,
}

impl ConfigurableStepBuilder {
    pub fn description(mut self, desc: impl Into<String>) -> Self {
        self.description = desc.into();
        self
    }
    
    pub fn operation(mut self, op: impl Into<String>) -> Self {
        self.operation = op.into();
        self
    }
    
    pub fn with_delay(mut self, millis: u64) -> Self {
        self.sleep_duration = Some(millis);
        self
    }
    
    pub fn should_fail(mut self) -> Self {
        self.should_fail = true;
        self
    }
    
    pub fn with_output(mut self, data: impl Into<String>) -> Self {
        self.output_data = Some(data.into());
        self
    }
    
    pub fn build(self) -> ConfigurableStep {
        ConfigurableStep {
            name: self.name,
            description: self.description,
            operation: self.operation,
            sleep_duration: self.sleep_duration,
            should_fail: self.should_fail,
            output_data: self.output_data,
        }
    }
}

#[async_trait]
impl ProcessStep for ConfigurableStep {
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
        println!("🔄 Executing {}: {}", self.name, self.operation);
        
        // Add delay if configured
        if let Some(duration) = self.sleep_duration {
            println!("   ⏱️  Waiting {}ms...", duration);
            tokio::time::sleep(tokio::time::Duration::from_millis(duration)).await;
        }
        
        // Check if step should fail
        if self.should_fail {
            println!("   ❌ Step {} failed as configured", self.name);
            return Ok(StepResult::failure(format!("Configured failure in {}", self.name)));
        }
        
        // Update context with step result
        context.set_state(&format!("{}_executed", self.name), true)?;
        context.set_state(&format!("{}_operation", self.name), &self.operation)?;
        
        if let Some(output) = &self.output_data {
            context.set_state(&format!("{}_output", self.name), output)?;
            println!("   📤 Output: {}", output);
        }
        
        println!("   ✅ Step {} completed successfully", self.name);
        
        Ok(StepResult::success())
    }
}

/// A conditional step that executes different logic based on context
#[derive(Debug, Clone)]
pub struct ConditionalExecutionStep {
    name: String,
    condition_key: String,
    true_operation: String,
    false_operation: String,
}

impl ConditionalExecutionStep {
    pub fn new(
        name: impl Into<String>, 
        condition_key: impl Into<String>,
        true_op: impl Into<String>,
        false_op: impl Into<String>
    ) -> Self {
        Self {
            name: name.into(),
            condition_key: condition_key.into(),
            true_operation: true_op.into(),
            false_operation: false_op.into(),
        }
    }
}

#[async_trait]
impl ProcessStep for ConditionalExecutionStep {
    fn name(&self) -> &str {
        &self.name
    }
    
    fn description(&self) -> &str {
        "A step that executes conditionally based on context state"
    }

    async fn execute(
        &self,
        context: &mut ProcessContext,
        _kernel: &Kernel,
    ) -> ProcessResult<StepResult> {
        // Get the condition value - could be boolean or string
        let condition = if let Ok(Some(bool_val)) = context.get_state::<bool>(&self.condition_key) {
            bool_val
        } else if let Ok(Some(string_val)) = context.get_state::<String>(&self.condition_key) {
            // For strings, consider "full" as true, others as false
            string_val == "full"
        } else {
            false
        };
        
        let operation = if condition {
            &self.true_operation
        } else {
            &self.false_operation
        };
        
        println!("🤔 Conditional step {}: condition '{}' = {} -> executing '{}'", 
            self.name, self.condition_key, condition, operation);
        
        context.set_state(&format!("{}_condition", self.name), condition)?;
        context.set_state(&format!("{}_operation", self.name), operation)?;
        
        Ok(StepResult::success())
    }
}

/// A process builder that demonstrates fluent API construction
pub struct ProcessBuilder {
    name: String,
    description: String,
    steps: Vec<Arc<dyn ProcessStep>>,
}

impl ProcessBuilder {
    pub fn new(name: impl Into<String>, description: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            description: description.into(),
            steps: Vec::new(),
        }
    }
    
    pub fn add_step(mut self, step: Arc<dyn ProcessStep>) -> Self {
        self.steps.push(step);
        self
    }
    
    pub fn add_configurable_step<F>(self, name: &str, builder_fn: F) -> Self 
    where
        F: FnOnce(ConfigurableStepBuilder) -> ConfigurableStepBuilder,
    {
        let step = builder_fn(ConfigurableStep::builder(name)).build();
        self.add_step(Arc::new(step))
    }
    
    pub fn add_conditional_step(
        self, 
        name: &str, 
        condition_key: &str,
        true_op: &str,
        false_op: &str
    ) -> Self {
        let step = ConditionalExecutionStep::new(name, condition_key, true_op, false_op);
        self.add_step(Arc::new(step))
    }
    
    pub fn add_steps_conditionally<F>(mut self, condition: bool, steps_fn: F) -> Self
    where
        F: FnOnce(ProcessBuilder) -> ProcessBuilder,
    {
        if condition {
            let temp_builder = ProcessBuilder::new("temp", "temp");
            let temp_builder = steps_fn(temp_builder);
            for step in temp_builder.steps {
                self.steps.push(step);
            }
        }
        self
    }
    
    pub fn build(self) -> WorkflowProcess {
        let mut process = WorkflowProcess::new(&self.name, &self.description);
        for step in self.steps {
            process = process.add_step(step);
        }
        process
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize environment and logging
    dotenv::dotenv().ok();
    tracing_subscriber::fmt::init();

    println!("🤖 Semantic Kernel Rust - Step 01: Process Builder Patterns");
    println!("============================================================\n");

    // Example 1: Basic fluent builder pattern
    println!("Example 1: Basic Fluent Builder Pattern");
    println!("======================================");
    
    basic_builder_pattern().await?;

    // Example 2: Dynamic process construction
    println!("\nExample 2: Dynamic Process Construction");
    println!("=====================================");
    
    dynamic_process_construction().await?;

    // Example 3: Complex conditional workflows
    println!("\nExample 3: Complex Conditional Workflows");
    println!("=======================================");
    
    complex_conditional_workflows().await?;

    println!("\n✅ Step01 Process Builder Patterns example completed!");

    Ok(())
}

/// Demonstrate basic fluent builder pattern for process construction
async fn basic_builder_pattern() -> Result<()> {
    let kernel = KernelBuilder::new().build();
    let process_engine = ProcessEngine::new();
    
    // Build a process using fluent API
    let process = Arc::new(
        ProcessBuilder::new("DataProcessingWorkflow", "A workflow for processing data")
            .add_configurable_step("Initialize", |builder| {
                builder
                    .description("Initialize the data processing system")
                    .operation("system_init")
                    .with_output("System initialized")
            })
            .add_configurable_step("LoadData", |builder| {
                builder
                    .description("Load data from source")
                    .operation("data_load")
                    .with_delay(100)
                    .with_output("Data loaded: 1000 records")
            })
            .add_configurable_step("ProcessData", |builder| {
                builder
                    .description("Process the loaded data")
                    .operation("data_process")
                    .with_delay(200)
                    .with_output("Data processed: 1000 records transformed")
            })
            .add_configurable_step("SaveResults", |builder| {
                builder
                    .description("Save processing results")
                    .operation("data_save")
                    .with_output("Results saved to database")
            })
            .build()
    );
    
    let result = process_engine.execute_process(process, &kernel).await?;
    
    println!("✅ Fluent builder process completed successfully!");
    println!("   Process ID: {}", result.process_id);
    println!("   State keys: {:?}", result.state.keys().collect::<Vec<_>>());
    
    Ok(())
}

/// Demonstrate dynamic process construction based on runtime conditions
async fn dynamic_process_construction() -> Result<()> {
    let kernel = KernelBuilder::new().build();
    let process_engine = ProcessEngine::new();
    
    // Simulate different runtime conditions
    let configurations = vec![
        ("development", true, false),
        ("staging", true, true),
        ("production", false, true),
    ];
    
    for (env, enable_debugging, enable_monitoring) in configurations {
        println!("\n--- Building process for environment: {} ---", env);
        
        let process = Arc::new(
            ProcessBuilder::new(
                format!("DeploymentProcess_{}", env),
                format!("Deployment process for {} environment", env)
            )
            .add_configurable_step("PrepareDeployment", |builder| {
                builder
                    .description("Prepare deployment artifacts")
                    .operation("prepare")
                    .with_output(format!("Artifacts prepared for {}", env))
            })
            .add_steps_conditionally(enable_debugging, |builder| {
                builder.add_configurable_step("EnableDebugMode", |step_builder| {
                    step_builder
                        .description("Enable debug logging")
                        .operation("debug_enable")
                        .with_output("Debug mode enabled")
                })
            })
            .add_configurable_step("Deploy", |builder| {
                builder
                    .description("Deploy to target environment")
                    .operation("deploy")
                    .with_delay(if env == "production" { 500 } else { 100 })
                    .with_output(format!("Deployed to {}", env))
            })
            .add_steps_conditionally(enable_monitoring, |builder| {
                builder.add_configurable_step("SetupMonitoring", |step_builder| {
                    step_builder
                        .description("Setup monitoring and alerts")
                        .operation("monitoring_setup")
                        .with_output("Monitoring configured")
                })
            })
            .add_configurable_step("Verify", |builder| {
                builder
                    .description("Verify deployment success")
                    .operation("verify")
                    .with_output("Deployment verified")
            })
            .build()
        );
        
        let result = process_engine.execute_process(process, &kernel).await?;
        println!("   ✅ {} process completed with {} steps", env, result.state.len());
    }
    
    Ok(())
}

/// Demonstrate complex conditional workflows with interdependent steps
async fn complex_conditional_workflows() -> Result<()> {
    let kernel = KernelBuilder::new().build();
    let process_engine = ProcessEngine::new();
    
    // Build a complex workflow with multiple decision points
    let process = Arc::new(
        ProcessBuilder::new("QualityAssuranceWorkflow", "Comprehensive QA process")
            .add_configurable_step("InitializeQA", |builder| {
                builder
                    .description("Initialize QA environment")
                    .operation("qa_init")
                    .with_output("QA environment ready")
            })
            .add_configurable_step("SetTestSuite", |builder| {
                builder
                    .description("Determine test suite based on change scope")
                    .operation("determine_tests")
                    .with_output("full") // Could be "smoke", "regression", or "full"
            })
            .add_conditional_step(
                "ExecuteTestSuite",
                "SetTestSuite_output",
                "Running full test suite (2000+ tests)",
                "Running smoke tests (50 tests)"
            )
            .add_configurable_step("AnalyzeResults", |builder| {
                builder
                    .description("Analyze test results")
                    .operation("analyze")
                    .with_delay(150)
                    .with_output("95% pass rate")
            })
            .add_configurable_step("GenerateReport", |builder| {
                builder
                    .description("Generate QA report")
                    .operation("report")
                    .with_output("QA report generated with 95% pass rate")
            })
            .build()
    );
    
    let result = process_engine.execute_process(process, &kernel).await?;
    
    println!("✅ Complex conditional workflow completed!");
    println!("   Final state summary:");
    for (key, _value) in &result.state {
        if key.contains("_output") {
            let output: Option<String> = result.get_state(key)?;
            if let Some(output) = output {
                println!("     {}: {}", key.replace("_output", ""), output);
            }
        }
    }
    
    Ok(())
}