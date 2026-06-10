//! Hello Prompt Example
//! 
//! This example demonstrates how to use the Semantic Kernel to send a prompt 
//! through a mock LLM service and get a response.

use semantic_kernel::KernelBuilder;
use semantic_kernel::content::{ChatHistory, PromptExecutionSettings};

#[cfg(feature = "mock")]
use semantic_kernel::mock::MockChatCompletionService;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    println!("🤖 Semantic Kernel Rust - Hello Prompt Example");
    println!("================================================");

    // Create a kernel with a mock chat completion service
    #[cfg(feature = "mock")]
    let kernel = {
        let mock_service = MockChatCompletionService::echo();
        KernelBuilder::new()
            .add_chat_completion_service(mock_service)
            .build()
    };

    #[cfg(not(feature = "mock"))]
    let kernel = KernelBuilder::new().build();

    // Simple prompt invocation
    println!("\n📝 Simple Prompt Invocation:");
    let response = kernel.invoke_prompt_async("Hello, Semantic Kernel!").await?;
    println!("User: Hello, Semantic Kernel!");
    println!("Assistant: {}", response);

    // Chat history example
    println!("\n💬 Chat History Example:");
    let mut chat_history = ChatHistory::new();
    chat_history.add_system_message("You are a helpful AI assistant specialized in Rust programming.");
    chat_history.add_user_message("What is the main benefit of using Rust?");

    let chat_response = kernel.invoke_chat_async(&chat_history, None).await?;
    println!("System: You are a helpful AI assistant specialized in Rust programming.");
    println!("User: What is the main benefit of using Rust?");
    println!("Assistant: {}", chat_response.content);

    // Using execution settings
    println!("\n⚙️ Using Execution Settings:");
    let execution_settings = PromptExecutionSettings::new()
        .with_max_tokens(100)
        .with_temperature(0.7)
        .with_model_id("mock-gpt");

    chat_history.add_user_message("Can you explain memory safety in Rust?");
    let advanced_response = kernel.invoke_chat_async(&chat_history, Some(&execution_settings)).await?;
    println!("User: Can you explain memory safety in Rust?");
    println!("Assistant: {}", advanced_response.content);
    println!("Model: {}", advanced_response.model_id.unwrap_or("unknown".to_string()));

    // Demonstrate kernel data storage
    println!("\n📋 Kernel Data Storage:");
    let mut kernel_with_data = kernel;
    kernel_with_data.add_data("user_preference", "verbose");
    kernel_with_data.add_data("session_id", "example_session_001");
    
    if let Some(preference) = kernel_with_data.get_data("user_preference") {
        println!("User preference: {}", preference);
    }
    if let Some(session) = kernel_with_data.get_data("session_id") {
        println!("Session ID: {}", session);
    }

    println!("\n✅ Example completed successfully!");
    Ok(())
}