//! ChatGPT Example using real OpenAI API
//!
//! This example demonstrates how to use the OpenAI connector to interact with
//! real OpenAI models. Set the OPENAI_API_KEY environment variable to run.
//!
//! Usage:
//!   OPENAI_API_KEY=your_key_here cargo run -p chat_gpt

use std::io::{self, Write};
use semantic_kernel::{KernelBuilder, content::{ChatHistory, PromptExecutionSettings}};
use sk_openai::OpenAIClient;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    // Initialize tracing
    tracing_subscriber::fmt::init();

    println!("🤖 Semantic Kernel Rust - ChatGPT Example");
    println!("==========================================");

    // Try to create OpenAI client from environment
    let openai_client = match OpenAIClient::from_env() {
        Ok(client) => {
            println!("✅ OpenAI API key found, using real OpenAI");
            client
        },
        Err(_) => {
            println!("❌ OPENAI_API_KEY environment variable not set");
            println!("Please set your OpenAI API key: export OPENAI_API_KEY=your_key_here");
            println!();
            println!("🔄 Using mock service for demonstration...");
            
            // Fall back to mock service for demonstration
            use semantic_kernel::mock::MockChatCompletionService;
            
            let mock_service = MockChatCompletionService::echo();
            let kernel = KernelBuilder::new()
                .add_chat_completion_service(mock_service)
                .build();

            let response = kernel.invoke_prompt_async("Hello from Semantic Kernel Rust!").await?;
            println!("Mock response: {}", response);
            return Ok(());
        }
    };

    // Create kernel with OpenAI service
    let kernel = KernelBuilder::new()
        .add_chat_completion_service(openai_client)
        .build();

    // Set up execution settings
    let execution_settings = PromptExecutionSettings::new()
        .with_max_tokens(150)
        .with_temperature(0.7)
        .with_model_id("gpt-3.5-turbo");

    // Interactive chat loop
    println!("\n💬 Chat with OpenAI (type 'quit' to exit):");
    println!("-------------------------------------------");

    let mut chat_history = ChatHistory::new();
    chat_history.add_system_message("You are a helpful AI assistant that provides concise and informative responses.");

    loop {
        // Get user input
        print!("\n👤 You: ");
        io::stdout().flush()?;
        
        let mut input = String::new();
        io::stdin().read_line(&mut input)?;
        let input = input.trim();

        if input.is_empty() {
            continue;
        }

        if input.eq_ignore_ascii_case("quit") || input.eq_ignore_ascii_case("exit") {
            println!("👋 Goodbye!");
            break;
        }

        // Add user message to history
        chat_history.add_user_message(input);

        // Get response from OpenAI
        print!("🤖 Assistant: ");
        io::stdout().flush()?;

        match kernel.invoke_chat_async(&chat_history, Some(&execution_settings)).await {
            Ok(response) => {
                println!("{}", response.content);
                
                // Add assistant response to history
                chat_history.add_assistant_message(&response.content);

                // Show some metadata
                if let Some(model) = response.model_id {
                    println!("   (Model: {})", model);
                }
            },
            Err(err) => {
                eprintln!("❌ Error: {}", err);
                println!("Please try again or check your API key.");
            }
        }
    }

    Ok(())
}