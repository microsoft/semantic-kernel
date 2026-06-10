//! Step 2: Add Plugins
//! 
//! This example shows how to load KernelPlugin instances.
//! It demonstrates:
//! - Creating plugins with native functions
//! - Using plugins in prompts
//! - Automatic function calling with FunctionChoiceBehavior

use anyhow::Result;
use semantic_kernel::{
    Kernel, KernelBuilder, async_trait,
    kernel::{KernelPlugin, KernelFunction},
    content::{ChatHistory, PromptExecutionSettings},
};
use sk_openai::OpenAIClient;
use std::env;
use std::collections::HashMap;
use chrono::{DateTime, Utc, Datelike};

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize environment
    dotenv::dotenv().ok();
    tracing_subscriber::fmt::init();

    println!("🤖 Semantic Kernel Rust - Step 2: Add Plugins");
    println!("==============================================\n");

    // Create kernel with plugins
    let kernel = create_kernel_with_plugins()?;

    // Example 1: Invoke the kernel with a prompt that asks the AI for information it cannot provide
    println!("Example 1: Asking the AI for information it cannot provide:");
    println!("----------------------------------------------------------");
    let response = invoke_with_short_limit(&kernel, "How many days until Christmas?").await?;
    println!("Response: {}\n", response);

    // Example 2: Use kernel for templated prompts that invoke plugins directly
    println!("Example 2: Using templated prompts that invoke plugins directly:");
    println!("----------------------------------------------------------------");
    let prompt = "The current time is {{TimeInformation-GetCurrentUtcTime}}. How many days until Christmas?";
    let response = invoke_with_plugin_template(&kernel, prompt).await?;
    println!("Response: {}\n", response);

    // Example 3: Use kernel with function calling for automatic plugin invocation
    println!("Example 3: Using function calling for automatic plugin invocation:");
    println!("------------------------------------------------------------------");
    let mut settings = PromptExecutionSettings::new()
        .with_max_tokens(150); // Reasonable for explanation with function calling
    settings.extension_data.insert(
        "function_choice_behavior".to_string(),
        serde_json::json!({ "type": "auto" })
    );
    
    let mut chat_history = ChatHistory::new();
    chat_history.add_user_message("How many days until Christmas? Explain your thinking.");
    
    let response = kernel.invoke_chat_async(&chat_history, Some(&settings)).await
        .map_err(|e| anyhow::anyhow!("Failed to invoke chat: {}", e))?;
    println!("Response: {}\n", response.content);

    // Example 4: Use kernel with function calling for complex scenarios  
    println!("Example 4: Using function calling for complex scenarios:");
    println!("-------------------------------------------------------");
    
    // Create a handy lime colored widget
    let mut chat_history = ChatHistory::new();
    chat_history.add_user_message("Create a handy lime colored widget for me.");
    let response = kernel.invoke_chat_async(&chat_history, Some(&settings)).await
        .map_err(|e| anyhow::anyhow!("Failed to invoke chat: {}", e))?;
    println!("Lime widget: {}", response.content);
    
    // Create a beautiful scarlet colored widget
    let mut chat_history = ChatHistory::new();
    chat_history.add_user_message("Create a beautiful scarlet colored widget for me.");
    let response = kernel.invoke_chat_async(&chat_history, Some(&settings)).await
        .map_err(|e| anyhow::anyhow!("Failed to invoke chat: {}", e))?;
    println!("Scarlet widget: {}", response.content);
    
    // Create an attractive maroon and navy colored widget
    let mut chat_history = ChatHistory::new();
    chat_history.add_user_message("Create an attractive maroon and navy colored widget for me.");
    let response = kernel.invoke_chat_async(&chat_history, Some(&settings)).await
        .map_err(|e| anyhow::anyhow!("Failed to invoke chat: {}", e))?;
    println!("Maroon/Navy widget: {}", response.content);

    println!("\n✅ Step2 example completed!");

    Ok(())
}

/// Create a kernel with plugins
fn create_kernel_with_plugins() -> Result<Kernel> {
    if let Ok(api_key) = env::var("OPENAI_API_KEY") {
        println!("✅ OpenAI API key found!");
        println!("📝 Creating kernel with plugins...\n");
        
        let client = OpenAIClient::new(api_key)?;
        
        let kernel = KernelBuilder::new()
            .add_chat_completion_service(client)
            .add_plugin("TimeInformation", Box::new(TimeInformationPlugin))
            .add_plugin("WidgetFactory", Box::new(WidgetFactoryPlugin))
            .build();
            
        Ok(kernel)
    } else {
        anyhow::bail!(
            "❌ Please set OPENAI_API_KEY environment variable\n\
            You can get an API key from https://platform.openai.com/api-keys"
        );
    }
}

/// Invoke a prompt with plugin template syntax
async fn invoke_with_plugin_template(kernel: &Kernel, template: &str) -> Result<String> {
    // Parse and replace plugin calls in the template
    let mut rendered = template.to_string();
    
    // Simple regex to find {{PluginName-FunctionName}} patterns
    let pattern = regex::Regex::new(r"\{\{(\w+)-(\w+)\}\}").unwrap();
    
    for cap in pattern.captures_iter(template) {
        let plugin_name = &cap[1];
        let function_name = &cap[2];
        
        if let Some(plugin) = kernel.get_plugin(plugin_name) {
            let functions = plugin.functions();
            if let Some(function) = functions.iter().find(|f| f.name() == function_name) {
                let args = HashMap::new(); // No arguments for GetCurrentUtcTime
                if let Ok(result) = function.invoke(kernel, &args).await {
                    let placeholder = format!("{{{{{}-{}}}}}", plugin_name, function_name);
                    rendered = rendered.replace(&placeholder, &result);
                }
            }
        }
    }
    
    // Now invoke with the rendered prompt (using short limit for testing)
    invoke_with_short_limit(kernel, &rendered).await
}

/// Invoke a prompt with reasonable token limit for testing
async fn invoke_with_short_limit(kernel: &Kernel, prompt: &str) -> Result<String> {
    let settings = PromptExecutionSettings::new()
        .with_max_tokens(100); // Reasonable for testing - allows complete sentences
        
    let mut chat_history = ChatHistory::new();
    chat_history.add_user_message(prompt);
    
    let response = kernel.invoke_chat_async(&chat_history, Some(&settings)).await
        .map_err(|e| anyhow::anyhow!("Failed to invoke prompt: {}", e))?;
    Ok(response.content)
}

// ===== PLUGINS =====

/// Time information plugin
struct TimeInformationPlugin;

#[async_trait]
impl KernelPlugin for TimeInformationPlugin {
    fn name(&self) -> &str {
        "TimeInformation"
    }
    
    fn description(&self) -> &str {
        "Provides time and date information"
    }
    
    fn functions(&self) -> Vec<&dyn KernelFunction> {
        vec![&GetCurrentUtcTimeFunction as &dyn KernelFunction]
    }
}

struct GetCurrentUtcTimeFunction;

#[async_trait]
impl KernelFunction for GetCurrentUtcTimeFunction {
    fn name(&self) -> &str {
        "GetCurrentUtcTime"
    }
    
    fn description(&self) -> &str {
        "Retrieves the current time in UTC"
    }
    
    async fn invoke(
        &self,
        _kernel: &Kernel,
        _arguments: &HashMap<String, String>,
    ) -> semantic_kernel::Result<String> {
        let now: DateTime<Utc> = Utc::now();
        Ok(now.format("%Y-%m-%d %H:%M:%S UTC").to_string())
    }
    
    fn get_json_schema(&self) -> serde_json::Value {
        serde_json::json!({
            "type": "function",
            "function": {
                "name": self.name(),
                "description": self.description(),
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        })
    }
}

/// Widget factory plugin
struct WidgetFactoryPlugin;

#[async_trait]
impl KernelPlugin for WidgetFactoryPlugin {
    fn name(&self) -> &str {
        "WidgetFactory"
    }
    
    fn description(&self) -> &str {
        "Creates widgets of various types and colors"
    }
    
    fn functions(&self) -> Vec<&dyn KernelFunction> {
        vec![&CreateWidgetFunction as &dyn KernelFunction]
    }
}

struct CreateWidgetFunction;

#[async_trait]
impl KernelFunction for CreateWidgetFunction {
    fn name(&self) -> &str {
        "CreateWidget"
    }
    
    fn description(&self) -> &str {
        "Creates a widget with specified type and colors"
    }
    
    async fn invoke(
        &self,
        _kernel: &Kernel,
        arguments: &HashMap<String, String>,
    ) -> semantic_kernel::Result<String> {
        let widget_type = arguments.get("widgetType")
            .unwrap_or(&"Standard".to_string())
            .to_string();
            
        let colors = arguments.get("colors")
            .unwrap_or(&"Gray".to_string())
            .to_string();
            
        // Map widget types to actual descriptions
        let type_desc = match widget_type.to_lowercase().as_str() {
            "handy" => "Compact",
            "beautiful" => "Elegant", 
            "attractive" => "Premium",
            _ => "Standard",
        };
        
        Ok(format!(
            "Created a {} {} widget with {} color scheme. SKU: WDG-{:04}",
            type_desc,
            widget_type,
            colors,
            rand::random::<u16>() % 10000
        ))
    }
    
    fn get_json_schema(&self) -> serde_json::Value {
        serde_json::json!({
            "type": "function",
            "function": {
                "name": self.name(),
                "description": self.description(),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "widgetType": {
                            "type": "string",
                            "description": "The type of widget (Handy, Beautiful, Attractive)",
                            "enum": ["Handy", "Beautiful", "Attractive"]
                        },
                        "colors": {
                            "type": "string",
                            "description": "Color or colors for the widget"
                        }
                    },
                    "required": ["widgetType", "colors"]
                }
            }
        })
    }
}