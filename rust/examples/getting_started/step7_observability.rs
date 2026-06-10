//! Step 7: Observability
//! 
//! This example shows how to observe the execution of KernelPlugin instances.
//! It demonstrates:
//! - Function invocation tracing
//! - Prompt rendering observation  
//! - Token usage monitoring
//! - Custom observability filters
//! - Structured logging integration

use anyhow::Result;
use semantic_kernel::{
    Kernel, KernelBuilder, async_trait,
    kernel::{KernelPlugin, KernelFunction},
    content::{ChatHistory, PromptExecutionSettings},
};
use sk_openai::OpenAIClient;
use std::env;
use std::collections::HashMap;
use std::time::Instant;
use chrono::{DateTime, Utc};
use tracing::{info, warn, debug, instrument, Span};

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize environment and structured logging
    dotenv::dotenv().ok();
    tracing_subscriber::fmt()
        .with_target(true)
        .with_level(true)
        .with_thread_ids(true)
        .with_file(true)
        .with_line_number(true)
        .init();

    println!("🤖 Semantic Kernel Rust - Step 7: Observability");
    println!("================================================\n");

    // Example 1: Observability with function invocation tracking
    println!("Example 1: Function invocation observability");
    println!("--------------------------------------------");
    
    let kernel = create_observable_kernel()?;
    
    // Configure execution settings for automatic function calling
    let mut settings = PromptExecutionSettings::new()
        .with_max_tokens(200);
    settings.extension_data.insert(
        "function_choice_behavior".to_string(),
        serde_json::json!({ "type": "auto" })
    );
    
    let mut chat_history = ChatHistory::new();
    chat_history.add_user_message("How many days until Christmas? Explain your thinking.");
    
    info!("Starting prompt execution with observability");
    let start_time = Instant::now();
    
    let response = kernel.invoke_chat_async(&chat_history, Some(&settings)).await
        .map_err(|e| anyhow::anyhow!("Failed to invoke chat: {}", e))?;
    
    let execution_time = start_time.elapsed();
    info!("Prompt execution completed in {:?}", execution_time);
    
    println!("Response: {}", response.content);
    println!("Execution time: {:?}\n", execution_time);

    // Example 2: Manual function invocation with detailed tracing
    println!("Example 2: Manual function invocation tracing");
    println!("----------------------------------------------");
    
    if let Some(plugin) = kernel.get_plugin("TimeInformation") {
        let functions = plugin.functions();
        if let Some(time_function) = functions.iter().find(|f| f.name() == "GetCurrentUtcTime") {
            let args = HashMap::new();
            
            info!("Manually invoking TimeInformation.GetCurrentUtcTime");
            let result = time_function.invoke(&kernel, &args).await
                .map_err(|e| anyhow::anyhow!("Failed to invoke function: {}", e))?;
            info!("Function result: {}", result);
            
            println!("Manual function call result: {}", result);
        }
    }

    // Example 3: Multiple function calls with observability
    println!("\nExample 3: Multiple function calls with metrics");
    println!("-----------------------------------------------");
    
    let mut total_calls = 0;
    let mut total_time = std::time::Duration::default();
    
    for i in 1..=3 {
        let start = Instant::now();
        
        let prompt = format!("Call {} - What time is it?", i);
        let response = invoke_with_tracing(&kernel, &prompt).await?;
        
        let call_time = start.elapsed();
        total_calls += 1;
        total_time += call_time;
        
        println!("Call {}: {} (took {:?})", i, response, call_time);
    }
    
    info!(
        "Summary: {} calls completed in {:?} (avg: {:?})", 
        total_calls, 
        total_time, 
        total_time / total_calls
    );

    println!("\n📊 Summary: {} calls, total time: {:?}", total_calls, total_time);
    println!("✅ Step7 example completed!");

    Ok(())
}

/// Create a kernel with observability features
#[instrument]
fn create_observable_kernel() -> Result<Kernel> {
    info!("Creating observable kernel");
    
    if let Ok(api_key) = env::var("OPENAI_API_KEY") {
        info!("OpenAI API key found, initializing client");
        
        let client = OpenAIClient::new(api_key)?;
        
        // Create observable time plugin
        let time_plugin = ObservableTimeInformationPlugin::new();
        
        let kernel = KernelBuilder::new()
            .add_chat_completion_service(client)
            .add_plugin("TimeInformation", Box::new(time_plugin))
            .build();
            
        info!("Observable kernel created successfully");
        Ok(kernel)
    } else {
        anyhow::bail!(
            "❌ Please set OPENAI_API_KEY environment variable\n\
            You can get an API key from https://platform.openai.com/api-keys"
        );
    }
}

/// Invoke a prompt with detailed tracing
#[instrument(skip(kernel))]
async fn invoke_with_tracing(kernel: &Kernel, prompt: &str) -> Result<String> {
    info!("Invoking prompt with tracing");
    debug!("Prompt content: {}", prompt);
    
    let start_time = Instant::now();
    
    let mut chat_history = ChatHistory::new();
    chat_history.add_user_message(prompt);
    
    let settings = PromptExecutionSettings::new()
        .with_max_tokens(100);
    
    let response = kernel.invoke_chat_async(&chat_history, Some(&settings)).await
        .map_err(|e| anyhow::anyhow!("Failed to invoke prompt: {}", e))?;
    
    let execution_time = start_time.elapsed();
    
    info!(
        "Prompt execution completed: {}ms, response length: {}", 
        execution_time.as_millis(),
        response.content.len()
    );
    
    Ok(response.content)
}

// ===== OBSERVABLE PLUGINS =====

/// Time information plugin with built-in observability
struct ObservableTimeInformationPlugin {
    function: ObservableGetCurrentUtcTimeFunction,
}

impl ObservableTimeInformationPlugin {
    fn new() -> Self {
        Self {
            function: ObservableGetCurrentUtcTimeFunction,
        }
    }
}

#[async_trait]
impl KernelPlugin for ObservableTimeInformationPlugin {
    fn name(&self) -> &str {
        "TimeInformation"
    }
    
    fn description(&self) -> &str {
        "Provides current time information with observability"
    }
    
    fn functions(&self) -> Vec<&dyn KernelFunction> {
        vec![&self.function as &dyn KernelFunction]
    }
}

struct ObservableGetCurrentUtcTimeFunction;

#[async_trait]
impl KernelFunction for ObservableGetCurrentUtcTimeFunction {
    fn name(&self) -> &str {
        "GetCurrentUtcTime"
    }
    
    fn description(&self) -> &str {
        "Retrieves the current time in UTC with observability"
    }
    
    #[instrument(skip(self, _kernel, _arguments))]
    async fn invoke(
        &self,
        _kernel: &Kernel,
        _arguments: &HashMap<String, String>,
    ) -> semantic_kernel::Result<String> {
        info!("Starting GetCurrentUtcTime function execution");
        
        let start_time = Instant::now();
        
        // Simulate some processing time for demonstration
        tokio::time::sleep(tokio::time::Duration::from_millis(10)).await;
        
        let utc_now: DateTime<Utc> = Utc::now();
        let time_str = utc_now.format("%a, %d %b %Y %H:%M:%S GMT").to_string();
        
        let execution_time = start_time.elapsed();
        
        info!(
            "GetCurrentUtcTime function completed: {}μs, result length: {}",
            execution_time.as_micros(),
            time_str.len()
        );
        
        // Add structured data to current span
        let span = Span::current();
        span.record("function.name", "GetCurrentUtcTime");
        span.record("function.result", &time_str);
        span.record("function.execution_time_ms", execution_time.as_millis());
        
        Ok(time_str)
    }
    
    fn get_json_schema(&self) -> serde_json::Value {
        debug!("Generating JSON schema for GetCurrentUtcTime function");
        
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