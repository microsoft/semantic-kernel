//! Step 1: Basic Agent Usage
//! 
//! This example demonstrates creation of ChatCompletionAgent and
//! eliciting its response to user messages.
//! It shows:
//! - Single agent interaction without conversation history
//! - Agent with conversation history maintained
//! - Creating agents with different personalities/instructions

use anyhow::Result;
use semantic_kernel::{Kernel, KernelBuilder, PromptExecutionSettings};
use sk_openai::OpenAIClient;
use sk_agent::{Agent, chat_completion_agent::ChatCompletionAgent, thread::AgentThread};
use std::env;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize environment and logging
    dotenv::dotenv().ok();
    tracing_subscriber::fmt::init();

    println!("🤖 Semantic Kernel Rust - Step 1: Basic Agent Usage");
    println!("===================================================\n");

    // Example 1: Single agent interactions without conversation history
    println!("Example 1: Single Agent - No Conversation History");
    println!("================================================");
    
    single_agent_no_history().await?;

    // Example 2: Agent with conversation history
    println!("\nExample 2: Agent with Conversation History");
    println!("==========================================");
    
    agent_with_conversation_history().await?;

    // Example 3: Multiple agents with different personalities
    println!("\nExample 3: Multiple Agents with Different Personalities");
    println!("======================================================");
    
    multiple_agent_personalities().await?;

    println!("\n✅ Step1 Agent example completed!");

    Ok(())
}

/// Demonstrate single agent usage where each invocation is independent
async fn single_agent_no_history() -> Result<()> {
    let kernel = create_kernel()?;
    
    // Define the agent with parrot personality using builder
    let agent = ChatCompletionAgent::builder()
        .name("Parrot")
        .instructions("Repeat the user message in the voice of a pirate and then end with a parrot sound.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create agent: {}", e))?;

    // Test phrases
    let phrases = vec![
        "Fortune favors the bold.",
        "I came, I saw, I conquered.",
        "Practice makes perfect.",
    ];

    for phrase in phrases {
        println!("\n👤 User: {}", phrase);
        
        let response = invoke_agent_once(&agent, phrase).await?;
        println!("🦜 Parrot: {}", response);
    }

    Ok(())
}

/// Demonstrate agent with conversation history
async fn agent_with_conversation_history() -> Result<()> {
    let kernel = create_kernel()?;
    
    // Define the agent with joker personality using builder
    let agent = ChatCompletionAgent::builder()
        .name("Joker")
        .instructions("You are good at telling jokes. Keep responses concise and fun.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create agent: {}", e))?;

    // Maintain conversation thread
    let mut thread = AgentThread::new();

    // First interaction
    let user_msg1 = "Tell me a joke about a pirate.";
    println!("\n👤 User: {}", user_msg1);
    
    let response1 = agent.invoke_async(&mut thread, user_msg1).await
        .map_err(|e| anyhow::anyhow!("Failed to invoke agent: {}", e))?;
    println!("😄 Joker: {}", response1.content);

    // Second interaction - building on the first
    let user_msg2 = "Now add some emojis to that joke.";
    println!("\n👤 User: {}", user_msg2);
    
    let response2 = agent.invoke_async(&mut thread, user_msg2).await
        .map_err(|e| anyhow::anyhow!("Failed to invoke agent: {}", e))?;
    println!("😄 Joker: {}", response2.content);

    Ok(())
}

/// Demonstrate multiple agents with different personalities
async fn multiple_agent_personalities() -> Result<()> {
    let kernel1 = create_kernel()?;
    let kernel2 = create_kernel()?;
    let kernel3 = create_kernel()?;

    // Create agents with different personalities using builder
    let poet = ChatCompletionAgent::builder()
        .name("Poet")
        .instructions("You are a romantic poet. Respond to everything in beautiful, lyrical language.")
        .kernel(kernel1)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create poet agent: {}", e))?;

    let scientist = ChatCompletionAgent::builder()
        .name("Scientist")
        .instructions("You are a logical scientist. Explain everything with facts and reason.")
        .kernel(kernel2)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create scientist agent: {}", e))?;

    let comedian = ChatCompletionAgent::builder()
        .name("Comedian")
        .instructions("You are a witty comedian. Make everything funny and light-hearted.")
        .kernel(kernel3)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create comedian agent: {}", e))?;

    // Same question to all three agents
    let question = "What do you think about the moon?";
    println!("\n📝 Question for all agents: {}", question);

    // Get responses from each agent
    println!("\n🌹 Poet's response:");
    let poet_response = invoke_agent_once(&poet, question).await?;
    println!("{}", poet_response);

    println!("\n🔬 Scientist's response:");
    let scientist_response = invoke_agent_once(&scientist, question).await?;
    println!("{}", scientist_response);

    println!("\n😂 Comedian's response:");
    let comedian_response = invoke_agent_once(&comedian, question).await?;
    println!("{}", comedian_response);

    Ok(())
}

/// Invoke an agent once without maintaining conversation history
async fn invoke_agent_once(agent: &ChatCompletionAgent, message: &str) -> Result<String> {
    let mut thread = AgentThread::new();
    
    let response = agent.invoke_async(&mut thread, message).await
        .map_err(|e| anyhow::anyhow!("Failed to invoke agent: {}", e))?;
    
    Ok(response.content)
}

/// Create a kernel with OpenAI service
fn create_kernel() -> Result<Kernel> {
    if let Ok(api_key) = env::var("OPENAI_API_KEY") {
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