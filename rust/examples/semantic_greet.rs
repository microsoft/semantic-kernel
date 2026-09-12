//! Semantic Greet Example
//! 
//! This example demonstrates how to load a semantic function from a prompt file
//! and use it to generate greetings.

use semantic_kernel::{KernelBuilder, kernel::SemanticFunction};
use std::collections::HashMap;
use std::path::Path;

#[cfg(feature = "mock")]
use semantic_kernel::mock::MockChatCompletionService;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    println!("👋 Semantic Kernel Rust - Semantic Greet Example");
    println!("=================================================");

    // Create a kernel with a mock chat completion service
    #[cfg(feature = "mock")]
    let mut kernel = {
        let mock_service = MockChatCompletionService::echo();
        KernelBuilder::new()
            .add_chat_completion_service(mock_service)
            .build()
    };

    #[cfg(not(feature = "mock"))]
    let mut kernel = KernelBuilder::new().build();

    // Load the semantic function from a prompt file
    println!("\n📂 Loading Semantic Function from Prompt File:");
    let prompt_path = Path::new("../examples/greet_prompt.prompt");
    
    match SemanticFunction::from_prompt_file(prompt_path) {
        Ok(greet_function) => {
            println!("✅ Loaded semantic function: {}", greet_function.name);
            println!("📝 Description: {}", greet_function.description);
            println!("🔤 Template: {}", greet_function.prompt_template);
            
            // Add the semantic function to the kernel
            kernel.add_semantic_function("greet", greet_function.prompt_template.clone(), Some("Greets a person".to_string()));
            
            // Test the semantic function with different parameters
            println!("\n🎭 Testing Semantic Function:");
            
            // Simple greeting
            let mut args = HashMap::new();
            args.insert("name".to_string(), "Alice".to_string());
            
            if let Some(plugin) = kernel.get_plugin("greet") {
                let functions = plugin.functions();
                if let Some(greet_fn) = functions.first() {
                    let result = greet_fn.invoke(&kernel, &args).await?;
                    println!("Greeting for Alice: {}", result);
                    
                    // Show JSON schema for the semantic function
                    let schema = greet_fn.get_json_schema();
                    println!("Semantic Function JSON Schema: {}", serde_json::to_string_pretty(&schema)?);
                }
            }
            
            // Greeting with occasion
            args.insert("occasion".to_string(), "birthday".to_string());
            if let Some(plugin) = kernel.get_plugin("greet") {
                let functions = plugin.functions();
                if let Some(greet_fn) = functions.first() {
                    let result = greet_fn.invoke(&kernel, &args).await?;
                    println!("Birthday greeting for Alice: {}", result);
                }
            }
            
            // Test with different names
            args.insert("name".to_string(), "Bob".to_string());
            args.insert("occasion".to_string(), "holiday".to_string());
            if let Some(plugin) = kernel.get_plugin("greet") {
                let functions = plugin.functions();
                if let Some(greet_fn) = functions.first() {
                    let result = greet_fn.invoke(&kernel, &args).await?;
                    println!("Holiday greeting for Bob: {}", result);
                }
            }
        }
        Err(e) => {
            println!("❌ Failed to load prompt file: {}", e);
            println!("📝 Creating inline semantic function instead:");
            
            // Create an inline semantic function
            let inline_prompt = "Hello {{name}}! Welcome to Semantic Kernel Rust!";
            kernel.add_semantic_function("inline_greet", inline_prompt, Some("Inline greeting function".to_string()));
            
            let mut args = HashMap::new();
            args.insert("name".to_string(), "Charlie".to_string());
            
            if let Some(plugin) = kernel.get_plugin("inline_greet") {
                let functions = plugin.functions();
                if let Some(greet_fn) = functions.first() {
                    let result = greet_fn.invoke(&kernel, &args).await?;
                    println!("Inline greeting for Charlie: {}", result);
                }
            }
        }
    }

    // Demonstrate loading from different file types
    println!("\n📄 Testing Different File Formats:");
    
    // Test with a simple prompt template
    let simple_template = "You are a helpful assistant. Please help {{user}} with {{task}}.";
    kernel.add_semantic_function("helper", simple_template, Some("Helper function".to_string()));
    
    let mut helper_args = HashMap::new();
    helper_args.insert("user".to_string(), "the developer".to_string());
    helper_args.insert("task".to_string(), "writing Rust code".to_string());
    
    if let Some(plugin) = kernel.get_plugin("helper") {
        let functions = plugin.functions();
        if let Some(helper_fn) = functions.first() {
            let result = helper_fn.invoke(&kernel, &helper_args).await?;
            println!("Helper response: {}", result);
        }
    }

    println!("\n✅ Semantic Greet example completed successfully!");
    Ok(())
}