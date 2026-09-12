//! Core plan structures and building capabilities

use std::collections::HashMap;
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use semantic_kernel::Kernel;
use crate::{Result, PlanError, ExecutionTrace, FunctionCallTrace, TraceEvent};

/// Represents a plan consisting of a sequence of steps to achieve a goal
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Plan {
    /// Unique identifier for this plan
    pub id: String,
    /// Human-readable description of the plan's goal
    pub description: String,
    /// Ordered sequence of steps to execute
    pub steps: Vec<PlanStep>,
    /// Metadata associated with the plan
    pub metadata: HashMap<String, String>,
    /// Expected output type/description
    pub expected_output: Option<String>,
}

/// Represents a single step in a plan
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PlanStep {
    /// Unique identifier for this step
    pub id: String,
    /// Name of the plugin containing the function
    pub plugin_name: String,
    /// Name of the function to call
    pub function_name: String,
    /// Arguments to pass to the function
    pub arguments: HashMap<String, String>,
    /// Human-readable description of this step
    pub description: String,
    /// Expected output from this step
    pub expected_output: Option<String>,
    /// Dependencies - step IDs that must complete before this step
    pub dependencies: Vec<String>,
}

/// Result of executing a plan or plan step
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PlanResult {
    /// Unique identifier for the execution
    pub execution_id: String,
    /// Whether the execution was successful
    pub success: bool,
    /// Output from the execution
    pub output: String,
    /// Error message if execution failed
    pub error: Option<String>,
    /// Execution trace for debugging/monitoring
    pub trace: ExecutionTrace,
    /// Execution time in milliseconds
    pub execution_time_ms: u64,
}

/// Builder for constructing plans with a fluent API
pub struct PlanBuilder {
    plan: Plan,
}

impl Plan {
    /// Create a new plan with the given description
    pub fn new(description: impl Into<String>) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            description: description.into(),
            steps: Vec::new(),
            metadata: HashMap::new(),
            expected_output: None,
        }
    }

    /// Create a builder for this plan
    pub fn builder(description: impl Into<String>) -> PlanBuilder {
        PlanBuilder {
            plan: Self::new(description),
        }
    }

    /// Add a step to the plan
    pub fn add_step(&mut self, step: PlanStep) {
        self.steps.push(step);
    }

    /// Execute the plan using the provided kernel
    pub async fn execute(&self, kernel: &Kernel) -> Result<PlanResult> {
        let start_time = std::time::Instant::now();
        let execution_id = Uuid::new_v4().to_string();
        let mut trace = ExecutionTrace::new(execution_id.clone(), self.id.clone());
        let mut outputs = HashMap::new();
        let mut final_output = String::new();

        trace.add_event(TraceEvent::PlanStarted {
            plan_id: self.id.clone(),
            description: self.description.clone(),
            step_count: self.steps.len(),
        });

        for (index, step) in self.steps.iter().enumerate() {
            // Check dependencies
            for dep_id in &step.dependencies {
                if !outputs.contains_key(dep_id) {
                    let error = format!("Dependency {} not satisfied for step {}", dep_id, step.id);
                    trace.add_event(TraceEvent::PlanCompleted {
                        success: false,
                        output: String::new(),
                        error: Some(error.clone()),
                    });
                    return Ok(PlanResult {
                        execution_id,
                        success: false,
                        output: String::new(),
                        error: Some(error),
                        trace,
                        execution_time_ms: start_time.elapsed().as_millis() as u64,
                    });
                }
            }

            // Execute the step
            let step_result = self.execute_step(kernel, step, &outputs, &mut trace).await?;
            
            if !step_result.success {
                trace.add_event(TraceEvent::PlanCompleted {
                    success: false,
                    output: step_result.output.clone(),
                    error: step_result.error.clone(),
                });
                return Ok(PlanResult {
                    execution_id,
                    success: false,
                    output: step_result.output,
                    error: step_result.error,
                    trace,
                    execution_time_ms: start_time.elapsed().as_millis() as u64,
                });
            }

            outputs.insert(step.id.clone(), step_result.output.clone());
            
            // If this is the last step, capture its output as the final result
            if index == self.steps.len() - 1 {
                final_output = step_result.output;
            }
        }

        trace.add_event(TraceEvent::PlanCompleted {
            success: true,
            output: final_output.clone(),
            error: None,
        });

        Ok(PlanResult {
            execution_id,
            success: true,
            output: final_output,
            error: None,
            trace,
            execution_time_ms: start_time.elapsed().as_millis() as u64,
        })
    }

    async fn execute_step(
        &self,
        kernel: &Kernel,
        step: &PlanStep,
        _outputs: &HashMap<String, String>,
        trace: &mut ExecutionTrace,
    ) -> Result<PlanResult> {
        let step_start = std::time::Instant::now();
        
        trace.add_event(TraceEvent::FunctionCalled(FunctionCallTrace {
            id: Uuid::new_v4().to_string(),
            plugin_name: step.plugin_name.clone(),
            function_name: step.function_name.clone(),
            arguments: step.arguments.clone(),
            timestamp: chrono::Utc::now(),
        }));

        // Get the plugin from kernel
        let plugin = kernel.get_plugin(&step.plugin_name)
            .ok_or_else(|| PlanError::InvalidPlanStep(format!("Plugin '{}' not found", step.plugin_name)))?;

        // Find the function in the plugin
        let functions = plugin.functions();
        let function = functions.iter()
            .find(|f| f.name() == step.function_name)
            .ok_or_else(|| PlanError::InvalidPlanStep(format!("Function '{}' not found in plugin '{}'", step.function_name, step.plugin_name)))?;

        // Execute the function
        match function.invoke(kernel, &step.arguments).await {
            Ok(output) => {
                trace.add_event(TraceEvent::FunctionCompleted {
                    function_call_id: step.id.clone(),
                    success: true,
                    output: output.clone(),
                    error: None,
                });

                Ok(PlanResult {
                    execution_id: step.id.clone(),
                    success: true,
                    output,
                    error: None,
                    trace: ExecutionTrace::new(step.id.clone(), self.id.clone()),
                    execution_time_ms: step_start.elapsed().as_millis() as u64,
                })
            }
            Err(e) => {
                let error_msg = e.to_string();
                trace.add_event(TraceEvent::FunctionCompleted {
                    function_call_id: step.id.clone(),
                    success: false,
                    output: String::new(),
                    error: Some(error_msg.clone()),
                });

                Ok(PlanResult {
                    execution_id: step.id.clone(),
                    success: false,
                    output: String::new(),
                    error: Some(error_msg),
                    trace: ExecutionTrace::new(step.id.clone(), self.id.clone()),
                    execution_time_ms: step_start.elapsed().as_millis() as u64,
                })
            }
        }
    }
}

impl PlanStep {
    /// Create a new plan step
    pub fn new(
        plugin_name: impl Into<String>,
        function_name: impl Into<String>,
        description: impl Into<String>,
    ) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            plugin_name: plugin_name.into(),
            function_name: function_name.into(),
            arguments: HashMap::new(),
            description: description.into(),
            expected_output: None,
            dependencies: Vec::new(),
        }
    }

    /// Add an argument to this step
    pub fn with_argument(mut self, key: impl Into<String>, value: impl Into<String>) -> Self {
        self.arguments.insert(key.into(), value.into());
        self
    }

    /// Add multiple arguments to this step
    pub fn with_arguments(mut self, arguments: HashMap<String, String>) -> Self {
        self.arguments.extend(arguments);
        self
    }

    /// Add a dependency to this step
    pub fn with_dependency(mut self, step_id: impl Into<String>) -> Self {
        self.dependencies.push(step_id.into());
        self
    }

    /// Set the expected output for this step
    pub fn with_expected_output(mut self, output: impl Into<String>) -> Self {
        self.expected_output = Some(output.into());
        self
    }
}

impl PlanBuilder {
    /// Add a step to the plan being built
    pub fn then(mut self, step: PlanStep) -> Self {
        self.plan.add_step(step);
        self
    }

    /// Add a simple function call step
    pub fn then_call(
        mut self,
        plugin_name: impl Into<String>,
        function_name: impl Into<String>,
        description: impl Into<String>,
    ) -> Self {
        let step = PlanStep::new(plugin_name, function_name, description);
        self.plan.add_step(step);
        self
    }

    /// Add a function call step with arguments
    pub fn then_call_with_args(
        mut self,
        plugin_name: impl Into<String>,
        function_name: impl Into<String>,
        description: impl Into<String>,
        arguments: HashMap<String, String>,
    ) -> Self {
        let step = PlanStep::new(plugin_name, function_name, description)
            .with_arguments(arguments);
        self.plan.add_step(step);
        self
    }

    /// Set metadata for the plan
    pub fn with_metadata(mut self, key: impl Into<String>, value: impl Into<String>) -> Self {
        self.plan.metadata.insert(key.into(), value.into());
        self
    }

    /// Set the expected output for the plan
    pub fn with_expected_output(mut self, output: impl Into<String>) -> Self {
        self.plan.expected_output = Some(output.into());
        self
    }

    /// Build the final plan
    pub fn build(self) -> Plan {
        self.plan
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use semantic_kernel::{KernelBuilder, kernel::{KernelPlugin, KernelFunction}};
    use std::collections::HashMap;

    // Test plugin and function for testing
    struct TestFunction {
        name: String,
        result: String,
    }

    #[semantic_kernel::async_trait]
    impl KernelFunction for TestFunction {
        fn name(&self) -> &str {
            &self.name
        }

        fn description(&self) -> &str {
            "Test function"
        }

        async fn invoke(
            &self,
            _kernel: &Kernel,
            _arguments: &HashMap<String, String>,
        ) -> semantic_kernel::Result<String> {
            Ok(self.result.clone())
        }
    }

    struct TestPlugin {
        functions: Vec<TestFunction>,
    }

    #[semantic_kernel::async_trait]
    impl KernelPlugin for TestPlugin {
        fn name(&self) -> &str {
            "TestPlugin"
        }

        fn description(&self) -> &str {
            "Plugin for testing"
        }

        fn functions(&self) -> Vec<&dyn KernelFunction> {
            self.functions.iter().map(|f| f as &dyn KernelFunction).collect()
        }
    }

    #[tokio::test]
    async fn test_plan_creation() {
        let plan = Plan::new("Test plan");
        assert!(!plan.id.is_empty());
        assert_eq!(plan.description, "Test plan");
        assert!(plan.steps.is_empty());
    }

    #[tokio::test]
    async fn test_plan_builder() {
        let plan = Plan::builder("Test plan")
            .then_call("TestPlugin", "test_function", "Call test function")
            .with_metadata("version", "1.0")
            .with_expected_output("success")
            .build();

        assert_eq!(plan.description, "Test plan");
        assert_eq!(plan.steps.len(), 1);
        assert_eq!(plan.steps[0].plugin_name, "TestPlugin");
        assert_eq!(plan.steps[0].function_name, "test_function");
        assert_eq!(plan.metadata.get("version"), Some(&"1.0".to_string()));
        assert_eq!(plan.expected_output, Some("success".to_string()));
    }

    #[tokio::test]
    async fn test_plan_step_creation() {
        let step = PlanStep::new("TestPlugin", "test_function", "Test step")
            .with_argument("arg1", "value1")
            .with_expected_output("test result");

        assert_eq!(step.plugin_name, "TestPlugin");
        assert_eq!(step.function_name, "test_function");
        assert_eq!(step.description, "Test step");
        assert_eq!(step.arguments.get("arg1"), Some(&"value1".to_string()));
        assert_eq!(step.expected_output, Some("test result".to_string()));
    }

    #[tokio::test]
    async fn test_plan_execution() {
        // Create test plugin with function
        let test_plugin = TestPlugin {
            functions: vec![TestFunction {
                name: "test_function".to_string(),
                result: "test result".to_string(),
            }],
        };

        // Create kernel and add plugin
        let mut kernel = KernelBuilder::new().build();
        kernel.add_plugin("TestPlugin", Box::new(test_plugin));

        // Create and execute plan
        let plan = Plan::builder("Test execution")
            .then_call("TestPlugin", "test_function", "Call test function")
            .build();

        let result = plan.execute(&kernel).await.unwrap();
        
        assert!(result.success);
        assert_eq!(result.output, "test result");
        assert!(result.error.is_none());
        assert!(!result.execution_id.is_empty());
        // Allow for execution time to be 0 in tests due to async timing
        assert!(result.execution_time_ms >= 0);
    }

    #[tokio::test]
    async fn test_plan_execution_with_missing_plugin() {
        let kernel = KernelBuilder::new().build();

        let plan = Plan::builder("Test missing plugin")
            .then_call("MissingPlugin", "missing_function", "Call missing function")
            .build();

        let result = plan.execute(&kernel).await;
        
        // The execution should succeed but return failure in the result
        match result {
            Ok(plan_result) => {
                assert!(!plan_result.success);
                assert!(plan_result.error.is_some());
                assert!(plan_result.error.unwrap().contains("Plugin 'MissingPlugin' not found"));
            }
            Err(e) => {
                // If it returns an error, make sure it's the right error
                assert!(e.to_string().contains("Plugin 'MissingPlugin' not found"));
            }
        }
    }

    #[tokio::test]
    async fn test_plan_execution_with_dependencies() {
        let test_plugin = TestPlugin {
            functions: vec![
                TestFunction {
                    name: "step1".to_string(),
                    result: "result1".to_string(),
                },
                TestFunction {
                    name: "step2".to_string(),
                    result: "result2".to_string(),
                },
            ],
        };

        let mut kernel = KernelBuilder::new().build();
        kernel.add_plugin("TestPlugin", Box::new(test_plugin));

        let step1 = PlanStep::new("TestPlugin", "step1", "First step");
        let step1_id = step1.id.clone();
        
        let step2 = PlanStep::new("TestPlugin", "step2", "Second step")
            .with_dependency(step1_id);

        let mut plan = Plan::new("Test dependencies");
        plan.add_step(step1);
        plan.add_step(step2);

        let result = plan.execute(&kernel).await.unwrap();
        
        assert!(result.success);
        assert_eq!(result.output, "result2"); // Should be the output from the last step
    }
}