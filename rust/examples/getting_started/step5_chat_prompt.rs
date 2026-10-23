//! Step 5: Chat Prompt
//! 
//! This example shows how to construct and invoke chat prompts.
//! It demonstrates:
//! - Creating a chat prompt with message roles
//! - Invoking kernel with structured chat messages
//! - Using system and user message roles
//! - Requesting JSON response format

use anyhow::Result;
use semantic_kernel::{
    Kernel, KernelBuilder,
    content::{ChatHistory, PromptExecutionSettings, AuthorRole},
};
use sk_openai::OpenAIClient;
use std::env;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize environment and logging
    dotenv::dotenv().ok();
    tracing_subscriber::fmt::init();

    println!("🤖 Semantic Kernel Rust - Step 5: Chat Prompt");
    println!("==============================================\n");

    // Create a kernel with OpenAI chat completion
    let kernel = create_kernel()?;

    // Example 1: Invoke chat prompt with message roles
    println!("Example 1: Chat prompt with message roles");
    println!("-----------------------------------------");
    
    // Create a chat history with structured messages
    let mut chat_history = ChatHistory::new();
    chat_history.add_user_message("What is Seattle?");
    chat_history.add_system_message("Respond with JSON.");
    
    // Configure execution settings for JSON response
    let mut settings = PromptExecutionSettings::new()
        .with_max_tokens(200);
    settings.extension_data.insert(
        "response_format".to_string(),
        serde_json::json!({ "type": "json_object" })
    );
    
    let response = kernel.invoke_chat_async(&chat_history, Some(&settings)).await
        .map_err(|e| anyhow::anyhow!("Failed to invoke chat: {}", e))?;
    
    println!("Chat Response:");
    println!("{}", response.content);
    
    // Example 2: Multi-turn conversation
    println!("\nExample 2: Multi-turn conversation");
    println!("-----------------------------------");
    
    let mut conversation = ChatHistory::new();
    conversation.add_system_message("You are a helpful assistant. Keep responses concise.");
    
    // Turn 1: User asks about Rust
    conversation.add_user_message("What is Rust programming language?");
    let response1 = invoke_with_limit(&kernel, &conversation, 100).await?;
    println!("User: What is Rust programming language?");
    println!("Assistant: {}\n", response1.content);
    
    // Turn 2: Follow up question
    conversation.add_assistant_message(&response1.content);
    conversation.add_user_message("What makes it memory safe?");
    let response2 = invoke_with_limit(&kernel, &conversation, 150).await?;
    println!("User: What makes it memory safe?");
    println!("Assistant: {}\n", response2.content);
    
    // Turn 3: Final question
    conversation.add_assistant_message(&response2.content);
    conversation.add_user_message("Give me a simple example.");
    let response3 = invoke_with_limit(&kernel, &conversation, 200).await?;
    println!("User: Give me a simple example.");
    println!("Assistant: {}\n", response3.content);

    // Example 3: Different message role combinations
    println!("Example 3: Different message role patterns");
    println!("------------------------------------------");
    
    // Pattern 1: System instruction + User query
    let mut pattern1 = ChatHistory::new();
    pattern1.add_system_message("You are a weather expert. Always mention temperature in Celsius.");
    pattern1.add_user_message("What's the weather like in London?");
    
    let response = invoke_with_limit(&kernel, &pattern1, 100).await?;
    println!("Weather Expert Pattern:");
    println!("{}\n", response.content);
    
    // Pattern 2: User + System override pattern
    let mut pattern2 = ChatHistory::new();
    pattern2.add_user_message("Tell me about cats.");
    pattern2.add_system_message("Focus only on their hunting behavior.");
    
    let response = invoke_with_limit(&kernel, &pattern2, 100).await?;
    println!("System Override Pattern:");
    println!("{}", response.content);

    println!("\n✅ Step5 example completed!");

    Ok(())
}

/// Create a kernel with OpenAI
fn create_kernel() -> Result<Kernel> {
    if let Ok(api_key) = env::var("OPENAI_API_KEY") {
        println!("✅ OpenAI API key found!");
        println!("📝 Creating kernel for chat prompts...\n");
        
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

/// Invoke chat with a specific token limit
async fn invoke_with_limit(
    kernel: &Kernel, 
    chat_history: &ChatHistory, 
    max_tokens: u32
) -> Result<semantic_kernel::content::ChatMessageContent> {
    let settings = PromptExecutionSettings::new()
        .with_max_tokens(max_tokens);
        
    kernel.invoke_chat_async(chat_history, Some(&settings)).await
        .map_err(|e| anyhow::anyhow!("Failed to invoke chat: {}", e))
}