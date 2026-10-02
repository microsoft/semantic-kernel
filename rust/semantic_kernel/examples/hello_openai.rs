//! Hello OpenAI Example
//! 
//! This example demonstrates the simplest way to use OpenAI with Semantic Kernel Rust.
//! Make sure to set OPENAI_API_KEY environment variable before running.

use semantic_kernel::KernelBuilder;
use sk_openai::OpenAIClient;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    println!("🤖 Semantic Kernel Rust - Hello OpenAI Example");
    println!("==============================================\n");

    // Create OpenAI client from environment variable
    let openai_client = match OpenAIClient::from_env() {
        Ok(client) => {
            println!("✅ OpenAI API key found!");
            client
        },
        Err(e) => {
            eprintln!("❌ Error: {}", e);
            eprintln!("\nPlease set your OpenAI API key:");
            eprintln!("  export OPENAI_API_KEY=your_key_here");
            eprintln!("\nOr create a .env file with:");
            eprintln!("  OPENAI_API_KEY=your_key_here");
            return Ok(());
        }
    };

    // Create kernel with OpenAI service
    let kernel = KernelBuilder::new()
        .add_chat_completion_service(openai_client)
        .build();

    // Send a simple prompt
    println!("📝 Sending prompt to OpenAI...\n");
    let prompt = "Hello OpenAI! Please respond with a friendly greeting and tell me one interesting fact about Rust programming language.";
    
    match kernel.invoke_prompt_async(prompt).await {
        Ok(response) => {
            println!("User: {}", prompt);
            println!("\n🤖 OpenAI Response:");
            println!("{}", response);
        },
        Err(e) => {
            eprintln!("❌ Error calling OpenAI: {}", e);
        }
    }

    println!("\n✅ Hello world example completed!");
    Ok(())
}