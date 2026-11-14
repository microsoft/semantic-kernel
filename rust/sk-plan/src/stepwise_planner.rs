//! Function Calling Stepwise Planner for iterative goal achievement
//! 
//! This planner uses modern LLM function calling to iteratively decide which
//! functions to invoke, allowing for dynamic adaptation based on intermediate results.

use std::collections::HashMap;
use semantic_kernel::Kernel;
use semantic_kernel::content::{ChatHistory, ChatMessage, AuthorRole, PromptExecutionSettings, ToolCall, FunctionCall};
use crate::{Plan, PlanStep, PlanResult, Result, PlanError, ExecutionTrace, TraceEvent, FunctionCallTrace};

/// Configuration for the Function Calling Stepwise Planner
#[derive(Debug, Clone)]
pub struct StepwisePlannerConfig {
    /// Maximum number of steps to execute
    pub max_steps: usize,
    /// Maximum number of iterations before giving up
    pub max_iterations: usize,
    /// Whether to include previous step results in context
    pub include_step_results: bool,
    /// Minimum confidence threshold for function selection
    pub min_confidence: f32,
    /// Custom system instructions
    pub system_instructions: Option<String>,
}

impl Default for StepwisePlannerConfig {
    fn default() -> Self {
        Self {
            max_steps: 15,
            max_iterations: 10,
            include_step_results: true,
            min_confidence: 0.7,
            system_instructions: None,
        }
    }
}

/// Stepwise planner that iteratively calls functions to achieve goals
pub struct FunctionCallingStepwisePlanner {
    config: StepwisePlannerConfig,
}

/// Context maintained during stepwise planning
#[derive(Debug)]
struct PlanningContext {
    goal: String,
    chat_history: ChatHistory,
    step_results: Vec<StepResult>,
    available_functions: Vec<FunctionInfo>,
    current_iteration: usize,
}

/// Result of executing a single step
#[derive(Debug, Clone)]
struct StepResult {
    step_number: usize,
    function_name: String,
    arguments: HashMap<String, String>,
    result: String,
    success: bool,
    error: Option<String>,
}

/// Information about available functions
#[derive(Debug, Clone)]
struct FunctionInfo {
    plugin_name: String,
    function_name: String,
    full_name: String,
    description: String,
    schema: serde_json::Value,
}

impl FunctionCallingStepwisePlanner {
    /// Create a new stepwise planner with default configuration
    pub fn new() -> Self {
        Self {
            config: StepwisePlannerConfig::default(),
        }
    }

    /// Create a new stepwise planner with custom configuration
    pub fn with_config(config: StepwisePlannerConfig) -> Self {
        Self { config }
    }

    /// Execute a goal step by step using function calling
    pub async fn execute_goal(&self, kernel: &Kernel, goal: &str) -> Result<PlanResult> {
        let execution_id = uuid::Uuid::new_v4().to_string();
        let plan_id = uuid::Uuid::new_v4().to_string();
        let start_time = std::time::Instant::now();
        
        let mut trace = ExecutionTrace::new(execution_id.clone(), plan_id.clone());
        
        // Initialize planning context
        let mut context = self.initialize_context(goal, kernel);
        
        trace.add_event(TraceEvent::PlanStarted {
            plan_id: plan_id.clone(),
            description: goal.to_string(),
            step_count: 0, // Unknown at start for stepwise planning
        });

        trace.add_event(TraceEvent::PlanningStarted {
            goal: goal.to_string(),
            available_functions: context.available_functions.iter().map(|f| f.full_name.clone()).collect(),
        });

        // Execute steps iteratively
        let mut final_result = String::new();
        let mut success = true;
        let mut error = None;

        for iteration in 0..self.config.max_iterations {
            context.current_iteration = iteration;
            
            // Check if we should continue
            if context.step_results.len() >= self.config.max_steps {
                tracing::warn!("Maximum steps ({}) reached", self.config.max_steps);
                break;
            }

            // Get next step from LLM
            match self.get_next_step(kernel, &mut context, &mut trace).await {
                Ok(Some(step_result)) => {
                    context.step_results.push(step_result.clone());
                    final_result = step_result.result.clone();
                    
                    if !step_result.success {
                        success = false;
                        error = step_result.error;
                        break;
                    }

                    // Check if the goal is achieved
                    if self.is_goal_achieved(&context, &step_result).await {
                        tracing::info!("Goal achieved after {} steps", context.step_results.len());
                        break;
                    }
                }
                Ok(None) => {
                    // LLM indicated completion
                    tracing::info!("LLM indicated goal completion after {} steps", context.step_results.len());
                    break;
                }
                Err(e) => {
                    success = false;
                    error = Some(e.to_string());
                    break;
                }
            }
        }

        if context.current_iteration >= self.config.max_iterations {
            success = false;
            error = Some(format!("Maximum iterations ({}) reached without achieving goal", self.config.max_iterations));
        }

        trace.add_event(TraceEvent::PlanCompleted {
            success,
            output: final_result.clone(),
            error: error.clone(),
        });

        Ok(PlanResult {
            execution_id,
            success,
            output: final_result,
            error,
            trace,
            execution_time_ms: start_time.elapsed().as_millis() as u64,
        })
    }

    /// Create a plan representation of the executed steps
    pub async fn create_plan(&self, kernel: &Kernel, goal: &str) -> Result<Plan> {
        // Execute the goal to get the steps
        let result = self.execute_goal(kernel, goal).await?;
        
        // Convert the execution trace to a plan
        let mut plan = Plan::new(format!("Stepwise plan for: {}", goal));
        
        let function_calls = result.trace.get_function_calls();
        for (index, call_trace) in function_calls.iter().enumerate() {
            let step = PlanStep::new(
                call_trace.plugin_name.clone(),
                call_trace.function_name.clone(),
                format!("Step {}: Call {}", index + 1, call_trace.full_function_name()),
            ).with_arguments(call_trace.arguments.clone());
            
            plan.add_step(step);
        }
        
        Ok(plan)
    }

    fn initialize_context(&self, goal: &str, kernel: &Kernel) -> PlanningContext {
        let mut chat_history = ChatHistory::new();
        
        // Add system message
        let system_message = self.create_system_message(goal);
        chat_history.add_system_message(&system_message);
        
        // Get available functions
        let available_functions = self.get_available_functions(kernel);
        
        PlanningContext {
            goal: goal.to_string(),
            chat_history,
            step_results: Vec::new(),
            available_functions,
            current_iteration: 0,
        }
    }

    async fn get_next_step(
        &self,
        kernel: &Kernel,
        context: &mut PlanningContext,
        trace: &mut ExecutionTrace,
    ) -> Result<Option<StepResult>> {
        // Get chat completion service
        let chat_service = kernel.services().get_chat_completion_service()
            .ok_or_else(|| PlanError::PlanningFailed("No chat completion service available".to_string()))?;

        // Add user message with current state
        let user_message = self.create_step_message(context);
        context.chat_history.add_user_message(&user_message);

        // Set up execution settings with function calling
        let mut execution_settings = PromptExecutionSettings::default();
        execution_settings.tool_choice = Some("auto".to_string());
        execution_settings.tools = Some(self.create_function_tools(&context.available_functions));

        // Get response from LLM
        let response = chat_service
            .get_chat_message_content(&context.chat_history.messages, Some(&execution_settings))
            .await
            .map_err(|e| PlanError::PlanningFailed(format!("Failed to get next step: {}", e)))?;

        // Add assistant response to chat history
        context.chat_history.add_assistant_message(&response.content);

        // Process the response
        if let Some(tool_calls) = &response.tool_calls {
            if let Some(tool_call) = tool_calls.first() {
                return self.execute_tool_call(kernel, context, tool_call, trace).await.map(Some);
            }
        }

        // Check if LLM indicated completion
        if response.content.to_lowercase().contains("goal achieved") 
            || response.content.to_lowercase().contains("task completed")
            || response.content.to_lowercase().contains("finished") {
            return Ok(None);
        }

        // If no function call was made, consider it an error
        Err(PlanError::PlanningFailed("LLM did not provide a function call or completion signal".to_string()))
    }

    async fn execute_tool_call(
        &self,
        kernel: &Kernel,
        context: &PlanningContext,
        tool_call: &ToolCall,
        trace: &mut ExecutionTrace,
    ) -> Result<StepResult> {
        let function_name = &tool_call.function.name;
        
        // Find the function info
        let function_info = context.available_functions
            .iter()
            .find(|f| f.full_name == *function_name)
            .ok_or_else(|| PlanError::InvalidPlanStep(format!("Function {} not found", function_name)))?;

        // Parse arguments from tool call
        let arguments = self.parse_tool_call_arguments(&tool_call.function)?;

        // Create function call trace
        let call_trace = FunctionCallTrace::new(
            function_info.plugin_name.clone(),
            function_info.function_name.clone(),
            arguments.clone(),
        );

        trace.add_event(TraceEvent::FunctionCalled(call_trace.clone()));

        // Get plugin and function
        let plugin = kernel.get_plugin(&function_info.plugin_name)
            .ok_or_else(|| PlanError::InvalidPlanStep(format!("Plugin {} not found", function_info.plugin_name)))?;

        let functions = plugin.functions();
        let function = functions.iter()
            .find(|f| f.name() == function_info.function_name)
            .ok_or_else(|| PlanError::InvalidPlanStep(format!("Function {} not found", function_info.function_name)))?;

        // Execute the function
        let step_number = context.step_results.len() + 1;
        match function.invoke(kernel, &arguments).await {
            Ok(result) => {
                trace.add_event(TraceEvent::FunctionCompleted {
                    function_call_id: call_trace.id.clone(),
                    success: true,
                    output: result.clone(),
                    error: None,
                });

                Ok(StepResult {
                    step_number,
                    function_name: function_name.clone(),
                    arguments,
                    result,
                    success: true,
                    error: None,
                })
            }
            Err(e) => {
                let error_msg = e.to_string();
                trace.add_event(TraceEvent::FunctionCompleted {
                    function_call_id: call_trace.id.clone(),
                    success: false,
                    output: String::new(),
                    error: Some(error_msg.clone()),
                });

                Ok(StepResult {
                    step_number,
                    function_name: function_name.clone(),
                    arguments,
                    result: String::new(),
                    success: false,
                    error: Some(error_msg),
                })
            }
        }
    }

    fn parse_tool_call_arguments(&self, function_call: &FunctionCall) -> Result<HashMap<String, String>> {
        let mut arguments = HashMap::new();
        
        if let Some(args) = &function_call.arguments {
            if let Ok(parsed_args) = serde_json::from_str::<serde_json::Value>(args) {
                if let Some(obj) = parsed_args.as_object() {
                    for (key, value) in obj {
                        arguments.insert(key.clone(), value.to_string());
                    }
                }
            }
        }
        
        Ok(arguments)
    }

    async fn is_goal_achieved(&self, context: &PlanningContext, last_result: &StepResult) -> bool {
        // Simple heuristic: if the last result contains success indicators
        let result_lower = last_result.result.to_lowercase();
        result_lower.contains("completed") 
            || result_lower.contains("finished")
            || result_lower.contains("success")
            || context.step_results.len() >= self.config.max_steps
    }

    fn create_system_message(&self, goal: &str) -> String {
        let custom_instructions = self.config.system_instructions
            .as_deref()
            .unwrap_or("You are a helpful assistant that can achieve goals by calling functions step by step.");

        format!(
            r#"{custom_instructions}

Your task is to achieve this goal: {goal}

You have access to various functions that you can call to help accomplish this goal. 
For each step:
1. Analyze the current situation and what has been accomplished so far
2. Determine the next logical step toward the goal
3. Call the appropriate function to take that step
4. Wait for the result before deciding the next step

When you believe the goal has been achieved or cannot be achieved, respond with a clear statement indicating completion or failure.

Be methodical and only take one step at a time. Use the function calling capabilities to execute actions.
"#,
            custom_instructions = custom_instructions,
            goal = goal
        )
    }

    fn create_step_message(&self, context: &PlanningContext) -> String {
        let mut message = format!("Goal: {}\n\n", context.goal);
        
        if context.step_results.is_empty() {
            message.push_str("This is the first step. What should I do to start working toward this goal?");
        } else {
            message.push_str("Previous steps taken:\n");
            for (i, result) in context.step_results.iter().enumerate() {
                let default_error = "Error".to_string();
                let result_text = if result.success { 
                    &result.result 
                } else { 
                    result.error.as_ref().unwrap_or(&default_error)
                };
                message.push_str(&format!(
                    "{}. Called {} with result: {}\n",
                    i + 1,
                    result.function_name,
                    result_text
                ));
            }
            message.push_str("\nWhat should be the next step?");
        }
        
        message
    }

    fn create_function_tools(&self, functions: &[FunctionInfo]) -> Vec<serde_json::Value> {
        functions.iter()
            .map(|f| f.schema.clone())
            .collect()
    }

    fn get_available_functions(&self, kernel: &Kernel) -> Vec<FunctionInfo> {
        let mut functions = Vec::new();

        // In a real implementation, this would iterate through all registered plugins
        // For this demo, we'll check the known plugin names that might be registered
        let plugin_names = [
            "TodoPlugin.create_todo", 
            "TodoPlugin.list_todos", 
            "TodoPlugin.complete_todo",
            "TestPlugin", 
            "MathPlugin", 
            "TextPlugin"
        ];

        for plugin_name in &plugin_names {
            if let Some(plugin) = kernel.get_plugin(plugin_name) {
                for function in plugin.functions() {
                    functions.push(FunctionInfo {
                        plugin_name: plugin.name().to_string(),
                        function_name: function.name().to_string(),
                        full_name: format!("{}.{}", plugin.name(), function.name()),
                        description: function.description().to_string(),
                        schema: function.get_json_schema(),
                    });
                }
            }
        }

        functions
    }
}

impl Default for FunctionCallingStepwisePlanner {
    fn default() -> Self {
        Self::new()
    }
}

// Extension trait for ChatHistory
trait ChatHistoryExt {
    fn add_system_message(&mut self, content: &str);
    fn add_assistant_message(&mut self, content: &str);
}

impl ChatHistoryExt for ChatHistory {
    fn add_system_message(&mut self, content: &str) {
        self.messages.push(ChatMessage {
            role: AuthorRole::System,
            content: content.to_string(),
            name: None,
            tool_call_id: None,
            tool_calls: None,
        });
    }

    fn add_assistant_message(&mut self, content: &str) {
        self.messages.push(ChatMessage {
            role: AuthorRole::Assistant,
            content: content.to_string(),
            name: None,
            tool_call_id: None,
            tool_calls: None,
        });
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use semantic_kernel::{KernelBuilder, kernel::{KernelPlugin, KernelFunction}};
    use semantic_kernel::content::FunctionCall;

    // Test implementations
    struct TestFunction {
        name: String,
        description: String,
        result: String,
    }

    #[semantic_kernel::async_trait]
    impl KernelFunction for TestFunction {
        fn name(&self) -> &str {
            &self.name
        }

        fn description(&self) -> &str {
            &self.description
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
        name: String,
        functions: Vec<TestFunction>,
    }

    #[semantic_kernel::async_trait]
    impl KernelPlugin for TestPlugin {
        fn name(&self) -> &str {
            &self.name
        }

        fn description(&self) -> &str {
            "Test plugin for stepwise planner"
        }

        fn functions(&self) -> Vec<&dyn KernelFunction> {
            self.functions.iter().map(|f| f as &dyn KernelFunction).collect()
        }
    }

    #[tokio::test]
    async fn test_stepwise_planner_creation() {
        let planner = FunctionCallingStepwisePlanner::new();
        assert_eq!(planner.config.max_steps, 15);
        assert_eq!(planner.config.max_iterations, 10);
        assert!(planner.config.include_step_results);
    }

    #[tokio::test]
    async fn test_stepwise_planner_with_config() {
        let config = StepwisePlannerConfig {
            max_steps: 5,
            max_iterations: 3,
            include_step_results: false,
            min_confidence: 0.8,
            system_instructions: Some("Custom instructions".to_string()),
        };
        
        let planner = FunctionCallingStepwisePlanner::with_config(config);
        assert_eq!(planner.config.max_steps, 5);
        assert_eq!(planner.config.max_iterations, 3);
        assert!(!planner.config.include_step_results);
        assert_eq!(planner.config.min_confidence, 0.8);
    }

    #[tokio::test]
    async fn test_initialize_context() {
        let kernel = KernelBuilder::new().build();
        let planner = FunctionCallingStepwisePlanner::new();
        
        let context = planner.initialize_context("Test goal", &kernel);
        
        assert_eq!(context.goal, "Test goal");
        assert!(context.step_results.is_empty());
        assert_eq!(context.current_iteration, 0);
        assert!(!context.chat_history.messages.is_empty()); // Should have system message
    }

    #[tokio::test]
    async fn test_create_system_message() {
        let planner = FunctionCallingStepwisePlanner::new();
        let message = planner.create_system_message("Complete a task");
        
        assert!(message.contains("Complete a task"));
        assert!(message.contains("step by step"));
        assert!(message.contains("function calling"));
    }

    #[tokio::test]
    async fn test_create_step_message_first_step() {
        let planner = FunctionCallingStepwisePlanner::new();
        let kernel = KernelBuilder::new().build();
        let context = planner.initialize_context("Test goal", &kernel);
        
        let message = planner.create_step_message(&context);
        
        assert!(message.contains("Test goal"));
        assert!(message.contains("first step"));
    }

    #[tokio::test]
    async fn test_create_step_message_with_previous_steps() {
        let planner = FunctionCallingStepwisePlanner::new();
        let kernel = KernelBuilder::new().build();
        let mut context = planner.initialize_context("Test goal", &kernel);
        
        context.step_results.push(StepResult {
            step_number: 1,
            function_name: "test_function".to_string(),
            arguments: HashMap::new(),
            result: "success".to_string(),
            success: true,
            error: None,
        });
        
        let message = planner.create_step_message(&context);
        
        assert!(message.contains("Test goal"));
        assert!(message.contains("Previous steps taken"));
        assert!(message.contains("test_function"));
        assert!(message.contains("success"));
    }

    #[tokio::test]
    async fn test_execute_goal_without_chat_service() {
        let kernel = KernelBuilder::new().build();
        let planner = FunctionCallingStepwisePlanner::new();

        let result = planner.execute_goal(&kernel, "Test goal").await;
        assert!(result.is_ok());
        let result = result.unwrap();
        assert!(!result.success);
        assert!(result.error.is_some());
        assert!(result.error.unwrap().contains("No chat completion service available"));
    }

    #[tokio::test]
    async fn test_parse_tool_call_arguments() {
        let planner = FunctionCallingStepwisePlanner::new();
        
        let function_call = FunctionCall {
            name: "test_function".to_string(),
            arguments: Some(r#"{"arg1": "value1", "arg2": "value2"}"#.to_string()),
        };
        
        let arguments = planner.parse_tool_call_arguments(&function_call).unwrap();
        
        assert_eq!(arguments.len(), 2);
        assert_eq!(arguments.get("arg1"), Some(&"\"value1\"".to_string()));
        assert_eq!(arguments.get("arg2"), Some(&"\"value2\"".to_string()));
    }

    #[tokio::test]
    async fn test_is_goal_achieved() {
        let planner = FunctionCallingStepwisePlanner::new();
        let kernel = KernelBuilder::new().build();
        let context = planner.initialize_context("Test goal", &kernel);
        
        let successful_result = StepResult {
            step_number: 1,
            function_name: "test".to_string(),
            arguments: HashMap::new(),
            result: "Task completed successfully".to_string(),
            success: true,
            error: None,
        };
        
        assert!(planner.is_goal_achieved(&context, &successful_result).await);
        
        let incomplete_result = StepResult {
            step_number: 1,
            function_name: "test".to_string(),
            arguments: HashMap::new(),
            result: "Still working".to_string(),
            success: true,
            error: None,
        };
        
        assert!(!planner.is_goal_achieved(&context, &incomplete_result).await);
    }
}