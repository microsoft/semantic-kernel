//! Todo Planner Example
//! 
//! Demonstrates the Sequential and Stepwise planners in action by
//! converting natural language todo goals into ordered function calls.

use std::collections::HashMap;
use semantic_kernel::{Kernel, KernelBuilder, kernel::{KernelPlugin, KernelFunction}};
use semantic_kernel::mock::MockChatCompletionService;
use sk_plan::{SequentialPlanner, FunctionCallingStepwisePlanner, Plan};

/// A todo plugin that provides functions for managing todos
struct TodoPlugin {
    todos: std::sync::Arc<std::sync::Mutex<Vec<Todo>>>,
}

#[derive(Debug, Clone)]
struct Todo {
    id: usize,
    title: String,
    description: String,
    completed: bool,
    priority: Priority,
}

#[derive(Debug, Clone)]
enum Priority {
    Low,
    Medium,
    High,
}

impl TodoPlugin {
    fn new() -> Self {
        Self {
            todos: std::sync::Arc::new(std::sync::Mutex::new(Vec::new())),
        }
    }
}

/// Helper plugin that wraps a single function
struct SingleFunctionPlugin {
    function: Box<dyn KernelFunction>,
}

impl SingleFunctionPlugin {
    fn new(function: Box<dyn KernelFunction>) -> Self {
        Self { function }
    }
}

#[semantic_kernel::async_trait]
impl KernelPlugin for SingleFunctionPlugin {
    fn name(&self) -> &str {
        self.function.name()
    }

    fn description(&self) -> &str {
        self.function.description()
    }

    fn functions(&self) -> Vec<&dyn KernelFunction> {
        vec![self.function.as_ref()]
    }
}

/// Function implementations for the TodoPlugin
struct CreateTodoFunction {
    todos: std::sync::Arc<std::sync::Mutex<Vec<Todo>>>,
}

#[semantic_kernel::async_trait]
impl KernelFunction for CreateTodoFunction {
    fn name(&self) -> &str {
        "create_todo"
    }

    fn description(&self) -> &str {
        "Create a new todo item with title, description, and priority"
    }

    async fn invoke(
        &self,
        _kernel: &Kernel,
        arguments: &HashMap<String, String>,
    ) -> semantic_kernel::Result<String> {
        let title = arguments.get("title").unwrap_or(&"Untitled".to_string()).clone();
        let description = arguments.get("description").unwrap_or(&"".to_string()).clone();
        let priority_str = arguments.get("priority").unwrap_or(&"Medium".to_string()).to_lowercase();
        
        let priority = match priority_str.as_str() {
            "low" => Priority::Low,
            "high" => Priority::High,
            _ => Priority::Medium,
        };

        let mut todos = self.todos.lock().unwrap();
        let id = todos.len() + 1;
        let todo = Todo {
            id,
            title: title.clone(),
            description,
            completed: false,
            priority,
        };
        
        todos.push(todo);
        
        Ok(format!("Created todo #{}: {}", id, title))
    }

    fn get_json_schema(&self) -> serde_json::Value {
        serde_json::json!({
            "type": "function",
            "function": {
                "name": "create_todo",
                "description": "Create a new todo item with title, description, and priority",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "The title of the todo item"
                        },
                        "description": {
                            "type": "string", 
                            "description": "Detailed description of the todo item"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                            "description": "Priority level of the todo item"
                        }
                    },
                    "required": ["title"]
                }
            }
        })
    }
}

struct ListTodosFunction {
    todos: std::sync::Arc<std::sync::Mutex<Vec<Todo>>>,
}

#[semantic_kernel::async_trait]
impl KernelFunction for ListTodosFunction {
    fn name(&self) -> &str {
        "list_todos"
    }

    fn description(&self) -> &str {
        "List all todo items, optionally filtered by status"
    }

    async fn invoke(
        &self,
        _kernel: &Kernel,
        arguments: &HashMap<String, String>,
    ) -> semantic_kernel::Result<String> {
        let filter = arguments.get("filter").map(|f| f.to_lowercase());
        let todos = self.todos.lock().unwrap();
        
        let filtered_todos: Vec<&Todo> = todos.iter()
            .filter(|todo| {
                match filter.as_deref() {
                    Some("completed") => todo.completed,
                    Some("pending") => !todo.completed,
                    _ => true,
                }
            })
            .collect();

        if filtered_todos.is_empty() {
            return Ok("No todos found".to_string());
        }

        let mut result = String::new();
        for todo in filtered_todos {
            let status = if todo.completed { "✓" } else { "○" };
            let priority_icon = match todo.priority {
                Priority::High => "🔴",
                Priority::Medium => "🟡", 
                Priority::Low => "🟢",
            };
            result.push_str(&format!(
                "{} {} #{}: {} - {}\n", 
                status, priority_icon, todo.id, todo.title, todo.description
            ));
        }
        
        Ok(result)
    }

    fn get_json_schema(&self) -> serde_json::Value {
        serde_json::json!({
            "type": "function",
            "function": {
                "name": "list_todos",
                "description": "List all todo items, optionally filtered by status",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filter": {
                            "type": "string",
                            "enum": ["all", "completed", "pending"],
                            "description": "Filter todos by completion status"
                        }
                    },
                    "required": []
                }
            }
        })
    }
}

struct CompleteTodoFunction {
    todos: std::sync::Arc<std::sync::Mutex<Vec<Todo>>>,
}

#[semantic_kernel::async_trait]
impl KernelFunction for CompleteTodoFunction {
    fn name(&self) -> &str {
        "complete_todo"
    }

    fn description(&self) -> &str {
        "Mark a todo item as completed by its ID"
    }

    async fn invoke(
        &self,
        _kernel: &Kernel,
        arguments: &HashMap<String, String>,
    ) -> semantic_kernel::Result<String> {
        let id_str = arguments.get("id").ok_or("Todo ID is required")?;
        let id: usize = id_str.parse().map_err(|_| "Invalid todo ID")?;
        
        let mut todos = self.todos.lock().unwrap();
        
        if let Some(todo) = todos.iter_mut().find(|t| t.id == id) {
            if todo.completed {
                Ok(format!("Todo #{} is already completed", id))
            } else {
                todo.completed = true;
                Ok(format!("Completed todo #{}: {}", id, todo.title))
            }
        } else {
            Ok(format!("Todo #{} not found", id))
        }
    }

    fn get_json_schema(&self) -> serde_json::Value {
        serde_json::json!({
            "type": "function",
            "function": {
                "name": "complete_todo",
                "description": "Mark a todo item as completed by its ID",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "description": "The ID of the todo item to complete"
                        }
                    },
                    "required": ["id"]
                }
            }
        })
    }
}

#[semantic_kernel::async_trait]
impl KernelPlugin for TodoPlugin {
    fn name(&self) -> &str {
        "TodoPlugin"
    }

    fn description(&self) -> &str {
        "Plugin for managing todo items - create, list, and complete todos"
    }

    fn functions(&self) -> Vec<&dyn KernelFunction> {
        // This is simplified - in a real implementation we'd store the functions as fields
        vec![]
    }
}

async fn demonstrate_sequential_planner() -> Result<(), Box<dyn std::error::Error>> {
    println!("🔄 Demonstrating Sequential Planner");
    println!("=====================================");

    // Create mock service that simulates planning responses
    let mock_service = MockChatCompletionService::with_responses(vec![
        "To organize your todos, I'll first list existing todos, then create the new high-priority task. Let me call TodoPlugin.list_todos then TodoPlugin.create_todo".to_string()
    ]);

    // Create todo plugin
    let todo_storage = std::sync::Arc::new(std::sync::Mutex::new(Vec::new()));
    let create_fn = CreateTodoFunction { todos: todo_storage.clone() };
    let list_fn = ListTodosFunction { todos: todo_storage.clone() };
    let complete_fn = CompleteTodoFunction { todos: todo_storage.clone() };

    // Create kernel with mock service and todo plugin
    let mut kernel = KernelBuilder::new()
        .add_chat_completion_service(mock_service)
        .build();

    // Add individual functions as plugins (wrapped approach)
    let create_plugin = SingleFunctionPlugin::new(Box::new(create_fn));
    let list_plugin = SingleFunctionPlugin::new(Box::new(list_fn));  
    let complete_plugin = SingleFunctionPlugin::new(Box::new(complete_fn));
    
    kernel.add_plugin("TodoPlugin.create_todo", Box::new(create_plugin));
    kernel.add_plugin("TodoPlugin.list_todos", Box::new(list_plugin));
    kernel.add_plugin("TodoPlugin.complete_todo", Box::new(complete_plugin));

    // Create planner
    let planner = SequentialPlanner::new();

    // Test goal
    let goal = "I need to organize my todo list and add a high-priority task to 'Review quarterly reports'";
    
    println!("Goal: {}", goal);
    println!();

    // Create plan
    match planner.create_plan(&kernel, goal).await {
        Ok(plan) => {
            println!("📋 Generated Plan:");
            println!("Plan ID: {}", plan.id);
            println!("Description: {}", plan.description);
            println!("Steps ({}):", plan.steps.len());
            
            for (i, step) in plan.steps.iter().enumerate() {
                println!("  {}. {} -> {} ({})", 
                    i + 1, 
                    step.plugin_name, 
                    step.function_name,
                    step.description
                );
            }
            
            println!();
            
            // Execute the plan
            println!("⚡ Executing Plan:");
            match plan.execute(&kernel).await {
                Ok(result) => {
                    println!("Success: {}", result.success);
                    println!("Output: {}", result.output);
                    println!("Execution time: {}ms", result.execution_time_ms);
                    
                    // Print JSON trace in .NET format
                    println!();
                    println!("🔍 Execution Trace (.NET Compatible):");
                    let dotnet_trace = result.trace.to_dotnet_format();
                    println!("{}", serde_json::to_string_pretty(&dotnet_trace)?);
                }
                Err(e) => {
                    println!("❌ Execution failed: {}", e);
                }
            }
        }
        Err(e) => {
            println!("❌ Planning failed: {}", e);
        }
    }

    Ok(())
}

async fn demonstrate_stepwise_planner() -> Result<(), Box<dyn std::error::Error>> {
    println!("\n🔄 Demonstrating Function Calling Stepwise Planner");
    println!("====================================================");

    // Create mock service with different responses for stepwise execution
    let mock_service = MockChatCompletionService::with_responses(vec![
        "I need to create a new todo for the user. Let me call the create_todo function.".to_string(),
        "Now I should list the todos to show the user what was created.".to_string(),
        "Task completed successfully. The todo has been created and listed.".to_string(),
    ]);

    // Create kernel and plugin
    let todo_storage = std::sync::Arc::new(std::sync::Mutex::new(Vec::new()));
    let create_fn = CreateTodoFunction { todos: todo_storage.clone() };
    let list_fn = ListTodosFunction { todos: todo_storage.clone() };

    let mut kernel = KernelBuilder::new()
        .add_chat_completion_service(mock_service)
        .build();
    
    kernel.add_plugin("TodoPlugin.create_todo", Box::new(SingleFunctionPlugin::new(Box::new(create_fn))));
    kernel.add_plugin("TodoPlugin.list_todos", Box::new(SingleFunctionPlugin::new(Box::new(list_fn))));

    // Create stepwise planner
    let planner = FunctionCallingStepwisePlanner::new();

    // Different goal for stepwise
    let goal = "Create a new todo item called 'Prepare presentation' with high priority and then show me the current todo list";

    println!("Goal: {}", goal);
    println!();

    // Execute goal stepwise
    match planner.execute_goal(&kernel, goal).await {
        Ok(result) => {
            println!("✅ Stepwise Execution Result:");
            println!("Success: {}", result.success);
            println!("Final Output: {}", result.output);
            println!("Execution time: {}ms", result.execution_time_ms);
            
            // Show function calls that were made
            let function_calls = result.trace.get_function_calls();
            println!("\n📞 Function Calls Made:");
            for (i, call) in function_calls.iter().enumerate() {
                println!("  {}. {} at {}", 
                    i + 1, 
                    call.full_function_name(),
                    call.timestamp.format("%H:%M:%S")
                );
                if !call.arguments.is_empty() {
                    println!("     Arguments: {:?}", call.arguments);
                }
            }

            // Print execution trace
            println!("\n🔍 Stepwise Execution Trace:");
            let dotnet_trace = result.trace.to_dotnet_format();
            println!("{}", serde_json::to_string_pretty(&dotnet_trace)?);
            
            // Also create a plan representation
            println!("\n📋 Equivalent Plan:");
            match planner.create_plan(&kernel, goal).await {
                Ok(plan) => {
                    for (i, step) in plan.steps.iter().enumerate() {
                        println!("  {}. {} -> {}", 
                            i + 1, 
                            step.plugin_name, 
                            step.function_name
                        );
                    }
                }
                Err(e) => {
                    println!("Could not create plan representation: {}", e);
                }
            }
        }
        Err(e) => {
            println!("❌ Stepwise execution failed: {}", e);
        }
    }

    Ok(())
}

async fn demonstrate_plan_dsl() -> Result<(), Box<dyn std::error::Error>> {
    println!("\n🔄 Demonstrating Plan DSL (Fluent API)");
    println!("=======================================");

    // Create a plan manually using the DSL
    let mut arguments = HashMap::new();
    arguments.insert("title".to_string(), "Buy groceries".to_string());
    arguments.insert("priority".to_string(), "medium".to_string());

    let plan = Plan::builder("Manual todo workflow")
        .then_call("TodoPlugin", "create_todo", "Create a grocery shopping todo")
        .then_call_with_args(
            "TodoPlugin", 
            "create_todo", 
            "Create second todo",
            {
                let mut args = HashMap::new();
                args.insert("title".to_string(), "Cook dinner".to_string());
                args.insert("priority".to_string(), "high".to_string());
                args
            }
        )
        .then_call("TodoPlugin", "list_todos", "Show all todos")
        .with_metadata("created_by", "manual_dsl")
        .with_metadata("version", "1.0")
        .with_expected_output("List of created todos")
        .build();

    println!("📋 Plan created with DSL:");
    println!("ID: {}", plan.id);
    println!("Description: {}", plan.description);
    println!("Metadata: {:?}", plan.metadata);
    println!("Expected output: {:?}", plan.expected_output);
    println!();

    println!("Steps:");
    for (i, step) in plan.steps.iter().enumerate() {
        println!("  {}. {} -> {} ({})", 
            i + 1, 
            step.plugin_name, 
            step.function_name,
            step.description
        );
        if !step.arguments.is_empty() {
            println!("     Args: {:?}", step.arguments);
        }
    }

    println!();
    println!("💡 This demonstrates the Plan DSL's fluent API:");
    println!("   - plan.then(step) for adding steps");
    println!("   - plan.then_call() for simple function calls");
    println!("   - plan.then_call_with_args() for calls with arguments");
    println!("   - plan.with_metadata() for adding metadata");
    println!("   - plan.with_expected_output() for setting expectations");

    Ok(())
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("🚀 Semantic Kernel Rust - Todo Planner Demo");
    println!("=============================================");
    println!();
    println!("This example demonstrates:");
    println!("• Sequential Planner - breaks down goals into ordered steps");
    println!("• Function Calling Stepwise Planner - iterative goal achievement"); 
    println!("• Plan DSL - fluent API for constructing plans");
    println!("• JSON trace format compatible with .NET Semantic Kernel");
    println!();

    // Run all demonstrations
    demonstrate_sequential_planner().await?;
    demonstrate_stepwise_planner().await?;
    demonstrate_plan_dsl().await?;

    println!("\n✨ Demo completed! The planners successfully converted natural language");
    println!("goals into ordered function calls, demonstrating the power of AI-driven");
    println!("task orchestration in Rust.");

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_todo_plugin_functions() {
        let todos = std::sync::Arc::new(std::sync::Mutex::new(Vec::new()));
        let create_fn = CreateTodoFunction { todos: todos.clone() };
        let list_fn = ListTodosFunction { todos: todos.clone() };
        let complete_fn = CompleteTodoFunction { todos: todos.clone() };

        let kernel = KernelBuilder::new().build();

        // Test create function
        let mut args = HashMap::new();
        args.insert("title".to_string(), "Test todo".to_string());
        args.insert("priority".to_string(), "high".to_string());

        let result = create_fn.invoke(&kernel, &args).await.unwrap();
        assert!(result.contains("Created todo #1: Test todo"));

        // Test list function
        let result = list_fn.invoke(&kernel, &HashMap::new()).await.unwrap();
        assert!(result.contains("Test todo"));
        assert!(result.contains("🔴")); // High priority icon

        // Test complete function
        let mut args = HashMap::new();
        args.insert("id".to_string(), "1".to_string());
        let result = complete_fn.invoke(&kernel, &args).await.unwrap();
        assert!(result.contains("Completed todo #1"));
    }

    #[tokio::test]
    async fn test_plan_dsl_integration() {
        let plan = Plan::builder("Test DSL plan")
            .then_call("TestPlugin", "test_function", "Test step")
            .with_metadata("test", "true")
            .build();

        assert_eq!(plan.description, "Test DSL plan");
        assert_eq!(plan.steps.len(), 1);
        assert_eq!(plan.steps[0].plugin_name, "TestPlugin");
        assert_eq!(plan.steps[0].function_name, "test_function");
        assert_eq!(plan.metadata.get("test"), Some(&"true".to_string()));
    }
}