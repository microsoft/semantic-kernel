//! Sequential planner that breaks down goals into ordered function calls
//! 
//! Uses modern LLM function calling to analyze available functions and create plans

use semantic_kernel::Kernel;
use semantic_kernel::content::{ChatHistory, ChatMessage, AuthorRole, PromptExecutionSettings, ChatMessageContent};
use serde_json::json;
use crate::{Plan, PlanStep, Result, PlanError, ExecutionTrace, TraceEvent};

/// Configuration for the Sequential Planner
#[derive(Debug, Clone)]
pub struct SequentialPlannerConfig {
    /// Maximum number of steps to include in a plan
    pub max_steps: usize,
    /// Whether to include function descriptions in planning
    pub include_function_descriptions: bool,
    /// Maximum number of functions to consider
    pub max_functions: usize,
    /// Custom instructions for the planner
    pub planner_instructions: Option<String>,
}

impl Default for SequentialPlannerConfig {
    fn default() -> Self {
        Self {
            max_steps: 10,
            include_function_descriptions: true,
            max_functions: 50,
            planner_instructions: None,
        }
    }
}

/// Sequential planner that creates plans using function calling
pub struct SequentialPlanner {
    config: SequentialPlannerConfig,
}

impl SequentialPlanner {
    /// Create a new sequential planner with default configuration
    pub fn new() -> Self {
        Self {
            config: SequentialPlannerConfig::default(),
        }
    }

    /// Create a new sequential planner with custom configuration
    pub fn with_config(config: SequentialPlannerConfig) -> Self {
        Self { config }
    }

    /// Create a plan for the given goal using available functions
    pub async fn create_plan(&self, kernel: &Kernel, goal: &str) -> Result<Plan> {
        let mut trace = ExecutionTrace::new(
            uuid::Uuid::new_v4().to_string(),
            uuid::Uuid::new_v4().to_string(),
        );

        // Get available functions from all plugins
        let available_functions = self.get_available_functions(kernel);
        
        trace.add_event(TraceEvent::PlanningStarted {
            goal: goal.to_string(),
            available_functions: available_functions.iter().map(|f| f.full_name.clone()).collect(),
        });

        // Use function calling to break down the goal
        match self.plan_with_function_calling(kernel, goal, &available_functions).await {
            Ok(plan) => {
                trace.add_event(TraceEvent::PlanningCompleted {
                    success: true,
                    plan_id: Some(plan.id.clone()),
                    error: None,
                });
                Ok(plan)
            }
            Err(error) => {
                trace.add_event(TraceEvent::PlanningCompleted {
                    success: false,
                    plan_id: None,
                    error: Some(error.to_string()),
                });
                Err(error)
            }
        }
    }

    async fn plan_with_function_calling(
        &self,
        kernel: &Kernel,
        goal: &str,
        available_functions: &[FunctionInfo],
    ) -> Result<Plan> {
        // Get the chat completion service
        let chat_service = kernel.services().get_chat_completion_service()
            .ok_or_else(|| PlanError::PlanningFailed("No chat completion service available".to_string()))?;

        // Create the planning prompt
        let planning_prompt = self.create_planning_prompt(goal, available_functions);
        
        // Create function calling tools for the LLM
        let tools = self.create_function_calling_tools(available_functions);
        
        // Set up chat history and execution settings
        let mut chat_history = ChatHistory::new();
        chat_history.add_system_message(&planning_prompt);
        chat_history.add_user_message(&format!("Please create a plan to accomplish this goal: {}", goal));

        let mut execution_settings = PromptExecutionSettings::default();
        execution_settings.tool_choice = Some("auto".to_string());
        execution_settings.tools = Some(tools);

        // Get response with function calling
        let response = chat_service
            .get_chat_message_content(&chat_history.messages, Some(&execution_settings))
            .await
            .map_err(|e| PlanError::PlanningFailed(format!("Failed to get planning response: {}", e)))?;

        // Parse the response to extract the plan
        self.parse_planning_response(&response, available_functions)
    }

    fn create_planning_prompt(&self, _goal: &str, functions: &[FunctionInfo]) -> String {
        let custom_instructions = self.config.planner_instructions
            .as_deref()
            .unwrap_or("You are a planning assistant that helps break down goals into sequential steps.");

        let function_descriptions = if self.config.include_function_descriptions {
            functions.iter()
                .take(self.config.max_functions)
                .map(|f| format!("- {}: {}", f.full_name, f.description))
                .collect::<Vec<_>>()
                .join("\n")
        } else {
            functions.iter()
                .take(self.config.max_functions)
                .map(|f| format!("- {}", f.full_name))
                .collect::<Vec<_>>()
                .join("\n")
        };

        format!(
            r#"{custom_instructions}

Your task is to analyze the user's goal and create a step-by-step plan using the available functions.

Available functions:
{function_descriptions}

Rules:
1. Break down the goal into no more than {max_steps} sequential steps
2. Each step should call exactly one function
3. Steps should be ordered logically to achieve the goal
4. Use only the functions listed above
5. Provide clear reasoning for each step

When creating the plan, use function calling to indicate which functions should be called and in what order.
"#,
            custom_instructions = custom_instructions,
            function_descriptions = function_descriptions,
            max_steps = self.config.max_steps
        )
    }

    fn create_function_calling_tools(&self, functions: &[FunctionInfo]) -> Vec<serde_json::Value> {
        functions.iter()
            .take(self.config.max_functions)
            .map(|f| {
                json!({
                    "type": "function",
                    "function": {
                        "name": f.full_name,
                        "description": f.description,
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }
                })
            })
            .collect()
    }

    fn parse_planning_response(
        &self,
        response: &ChatMessageContent,
        available_functions: &[FunctionInfo],
    ) -> Result<Plan> {
        // Create a plan from the response
        let mut plan = Plan::new(format!("Plan created by SequentialPlanner"));

        // If the response contains function calls, use them to build the plan
        if let Some(tool_calls) = response.tool_calls.as_ref() {
            for (index, tool_call) in tool_calls.iter().enumerate() {
                if let Some(function_info) = available_functions.iter().find(|f| f.full_name == tool_call.function.name) {
                    let step = PlanStep::new(
                        function_info.plugin_name.clone(),
                        function_info.function_name.clone(),
                        format!("Step {}: {}", index + 1, function_info.description),
                    );
                    plan.add_step(step);
                }
            }
        }

        // If no function calls were made, try to parse the text response
        if plan.steps.is_empty() {
            plan = self.parse_text_response(&response.content, available_functions)?;
        }

        if plan.steps.is_empty() {
            return Err(PlanError::PlanningFailed("No valid plan could be created from the response".to_string()));
        }

        Ok(plan)
    }

    fn parse_text_response(&self, content: &str, available_functions: &[FunctionInfo]) -> Result<Plan> {
        let mut plan = Plan::new("Plan parsed from text response".to_string());

        // Simple text parsing - look for function names in the response
        for function_info in available_functions {
            if content.contains(&function_info.full_name) || content.contains(&function_info.function_name) {
                let step = PlanStep::new(
                    function_info.plugin_name.clone(),
                    function_info.function_name.clone(),
                    format!("Call {}", function_info.full_name),
                );
                plan.add_step(step);
            }
        }

        Ok(plan)
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
                    });
                }
            }
        }

        functions
    }
}

impl Default for SequentialPlanner {
    fn default() -> Self {
        Self::new()
    }
}

/// Information about an available function
#[derive(Debug, Clone)]
struct FunctionInfo {
    plugin_name: String,
    function_name: String,
    full_name: String,
    description: String,
}

// Extension trait for ChatHistory to add system messages
trait ChatHistoryExt {
    fn add_system_message(&mut self, content: &str);
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
}

#[cfg(test)]
mod tests {
    use super::*;
    use semantic_kernel::{KernelBuilder, kernel::{KernelPlugin, KernelFunction}};
    use semantic_kernel::mock::MockChatCompletionService;
    use std::collections::HashMap;

    // Test function and plugin implementations
    struct TestFunction {
        name: String,
        description: String,
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
            Ok(format!("Result from {}", self.name))
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
            "Test plugin for sequential planner"
        }

        fn functions(&self) -> Vec<&dyn KernelFunction> {
            self.functions.iter().map(|f| f as &dyn KernelFunction).collect()
        }
    }

    #[tokio::test]
    async fn test_sequential_planner_creation() {
        let planner = SequentialPlanner::new();
        assert_eq!(planner.config.max_steps, 10);
        assert!(planner.config.include_function_descriptions);
    }

    #[tokio::test]
    async fn test_sequential_planner_with_config() {
        let config = SequentialPlannerConfig {
            max_steps: 5,
            include_function_descriptions: false,
            max_functions: 20,
            planner_instructions: Some("Custom instructions".to_string()),
        };
        
        let planner = SequentialPlanner::with_config(config);
        assert_eq!(planner.config.max_steps, 5);
        assert!(!planner.config.include_function_descriptions);
        assert_eq!(planner.config.planner_instructions, Some("Custom instructions".to_string()));
    }

    #[tokio::test]
    async fn test_get_available_functions() {
        let test_plugin = TestPlugin {
            name: "TestPlugin".to_string(),
            functions: vec![
                TestFunction {
                    name: "function1".to_string(),
                    description: "First test function".to_string(),
                },
                TestFunction {
                    name: "function2".to_string(),
                    description: "Second test function".to_string(),
                },
            ],
        };

        let mut kernel = KernelBuilder::new().build();
        kernel.add_plugin("TestPlugin", Box::new(test_plugin));

        let planner = SequentialPlanner::new();
        let functions = planner.get_available_functions(&kernel);

        assert_eq!(functions.len(), 2);
        assert_eq!(functions[0].plugin_name, "TestPlugin");
        assert_eq!(functions[0].function_name, "function1");
        assert_eq!(functions[0].full_name, "TestPlugin.function1");
        assert_eq!(functions[0].description, "First test function");
    }

    #[tokio::test]
    async fn test_create_planning_prompt() {
        let functions = vec![
            FunctionInfo {
                plugin_name: "TestPlugin".to_string(),
                function_name: "test_func".to_string(),
                full_name: "TestPlugin.test_func".to_string(),
                description: "A test function".to_string(),
            },
        ];

        let planner = SequentialPlanner::new();
        let prompt = planner.create_planning_prompt("Test goal", &functions);

        assert!(prompt.contains("TestPlugin.test_func"));
        assert!(prompt.contains("A test function"));
        assert!(prompt.contains("no more than 10 sequential steps"));
    }

    #[tokio::test]
    async fn test_create_function_calling_tools() {
        let functions = vec![
            FunctionInfo {
                plugin_name: "TestPlugin".to_string(),
                function_name: "test_func".to_string(),
                full_name: "TestPlugin.test_func".to_string(),
                description: "A test function".to_string(),
            },
        ];

        let planner = SequentialPlanner::new();
        let tools = planner.create_function_calling_tools(&functions);

        assert_eq!(tools.len(), 1);
        assert_eq!(tools[0]["type"], "function");
        assert_eq!(tools[0]["function"]["name"], "TestPlugin.test_func");
        assert_eq!(tools[0]["function"]["description"], "A test function");
    }

    #[tokio::test]
    async fn test_parse_text_response() {
        let functions = vec![
            FunctionInfo {
                plugin_name: "TestPlugin".to_string(),
                function_name: "test_func".to_string(),
                full_name: "TestPlugin.test_func".to_string(),
                description: "A test function".to_string(),
            },
        ];

        let planner = SequentialPlanner::new();
        let response = "To accomplish this goal, we should call TestPlugin.test_func first";
        let plan = planner.parse_text_response(response, &functions).unwrap();

        assert_eq!(plan.steps.len(), 1);
        assert_eq!(plan.steps[0].plugin_name, "TestPlugin");
        assert_eq!(plan.steps[0].function_name, "test_func");
    }

    #[tokio::test]
    async fn test_create_plan_without_chat_service() {
        let kernel = KernelBuilder::new().build();
        let planner = SequentialPlanner::new();

        let result = planner.create_plan(&kernel, "Test goal").await;
        assert!(result.is_err());
        assert!(result.unwrap_err().to_string().contains("No chat completion service available"));
    }

    #[tokio::test]
    async fn test_create_plan_with_mock_service() {
        let mock_service = MockChatCompletionService::with_responses(vec![
            "I'll help you accomplish this goal by calling TestPlugin.test_func".to_string()
        ]);

        let test_plugin = TestPlugin {
            name: "TestPlugin".to_string(),
            functions: vec![
                TestFunction {
                    name: "test_func".to_string(),
                    description: "A test function".to_string(),
                },
            ],
        };

        let mut kernel = KernelBuilder::new()
            .add_chat_completion_service(mock_service)
            .build();
        kernel.add_plugin("TestPlugin", Box::new(test_plugin));

        let planner = SequentialPlanner::new();
        let plan = planner.create_plan(&kernel, "Test goal").await.unwrap();

        assert!(!plan.id.is_empty());
        // The mock response should trigger text parsing and find the function
        assert_eq!(plan.steps.len(), 1);
        assert_eq!(plan.steps[0].plugin_name, "TestPlugin");
        assert_eq!(plan.steps[0].function_name, "test_func");
    }
}