//! Step 1: Create Kernel
//! 
//! This example shows how to create and use a Kernel.
//! It demonstrates:
//! - Creating a kernel with OpenAI
//! - Simple prompt invocation
//! - Templated prompts with arguments
//! - Streaming responses
//! - Execution settings (temperature, max_tokens)
//! - JSON response format

use anyhow::Result;
use semantic_kernel::{
    Kernel, KernelBuilder,
    content::{ChatHistory, PromptExecutionSettings},
};
use sk_openai::OpenAIClient;
use std::env;
use std::collections::HashMap;
use futures::StreamExt;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize environment
    dotenv::dotenv().ok();
    tracing_subscriber::fmt::init();

    println!("🤖 Semantic Kernel Rust - Step 1: Create Kernel");
    println!("==============================================\n");

    // Create kernel with OpenAI
    let kernel = create_kernel()?;

    // Example 1: Simple prompt invocation
    println!("Example 1: Simple prompt invocation");
    println!("-----------------------------------");
    let response = invoke_with_short_limit(&kernel, "What color is the sky?").await
        .map_err(|e| anyhow::anyhow!("Failed to invoke prompt: {}", e))?;
    println!("Response: {}\n", response);

    // Example 2: Templated prompt with arguments
    println!("Example 2: Templated prompt with arguments");
    println!("------------------------------------------");
    let mut arguments = HashMap::new();
    arguments.insert("topic".to_string(), "sea".to_string());
    
    let prompt = render_template("What color is the {{topic}}?", &arguments);
    let response = invoke_with_short_limit(&kernel, &prompt).await
        .map_err(|e| anyhow::anyhow!("Failed to invoke prompt: {}", e))?;
    println!("Response: {}\n", response);

    // Example 3: Streaming response
    println!("Example 3: Streaming response");
    println!("-----------------------------");
    arguments.insert("topic".to_string(), "ocean".to_string());
    let prompt = render_template("What color is the {{topic}}? Provide a detailed explanation.", &arguments);
    
    print!("Streaming: ");
    stream_prompt(&kernel, &prompt).await?;
    println!("\n");

    // Example 4: Prompt with execution settings  
    println!("Example 4: Prompt with execution settings");
    println!("-----------------------------------------");
    let settings = PromptExecutionSettings::new()
        .with_max_tokens(150) // Reasonable for a short story/fact
        .with_temperature(0.5);
    
    arguments.clear();
    arguments.insert("topic".to_string(), "dogs".to_string());
    
    let prompt = render_template("Tell me a short fact about {{topic}}", &arguments);
    let mut chat_history = ChatHistory::new();
    chat_history.add_user_message(&prompt);
    
    let response = kernel.invoke_chat_async(&chat_history, Some(&settings)).await
        .map_err(|e| anyhow::anyhow!("Failed to invoke chat: {}", e))?;
    println!("Response: {}\n", response.content);

    // Example 5: JSON response format
    println!("Example 5: JSON response format");
    println!("--------------------------------");
    let mut json_settings = PromptExecutionSettings::new();
    json_settings.extension_data.insert(
        "response_format".to_string(), 
        serde_json::json!({ "type": "json_object" })
    );
    
    arguments.clear();
    arguments.insert("topic".to_string(), "chocolate".to_string());
    
    let prompt = render_template("Create a simple {{topic}} cake recipe in JSON format", &arguments);
    let mut chat_history = ChatHistory::new();
    chat_history.add_user_message(&prompt);
    
    let response = kernel.invoke_chat_async(&chat_history, Some(&json_settings)).await
        .map_err(|e| anyhow::anyhow!("Failed to invoke chat: {}", e))?;
    println!("Response: {}", response.content);

    println!("\n✅ Step1 example completed!");

    Ok(())
}

/// Create a kernel with OpenAI
fn create_kernel() -> Result<Kernel> {
    if let Ok(api_key) = env::var("OPENAI_API_KEY") {
        println!("✅ OpenAI API key found!");
        println!("📝 Creating kernel with OpenAI...\n");
        
        let client = OpenAIClient::new(api_key)?;
        
        Ok(KernelBuilder::new()
            .add_chat_completion_service(client)
            .build())
    } else {
        anyhow::bail!(
            "❌ Please set OPENAI_API_KEY environment variable\n\
            You can get an API key from https://platform.openai.com/api-keys"
        );
    }
}

/// Render a template with the given arguments
fn render_template(template: &str, arguments: &HashMap<String, String>) -> String {
    let mut rendered = template.to_string();
    for (key, value) in arguments {
        let placeholder = format!("{{{{{}}}}}", key);
        rendered = rendered.replace(&placeholder, value);
    }
    rendered
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

/// Stream a prompt response
async fn stream_prompt(kernel: &Kernel, prompt: &str) -> Result<()> {
    let mut chat_history = ChatHistory::new();
    chat_history.add_user_message(prompt);
    
    // Get the chat completion service and stream
    if let Some(service) = kernel.services().get_chat_completion_service() {
        let mut stream = service.get_streaming_chat_message_contents(&chat_history.messages, None).await
            .map_err(|e| anyhow::anyhow!("Failed to get streaming content: {}", e))?;
        
        while let Some(chunk) = stream.next().await {
            match chunk {
                Ok(content) => {
                    if let Some(text) = content.content {
                        print!("{}", text);
                    }
                },
                Err(e) => eprintln!("\nStreaming error: {}", e),
            }
        }
    }
    
    Ok(())
}