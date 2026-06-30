//! Step 3: Agent Group Chat
//! 
//! This example demonstrates AgentGroupChat with multiple agents.
//! It shows:
//! - Multi-agent conversation coordination
//! - Agent selection and turn management
//! - Termination strategies for conversations
//! - Role-based agent interactions

use anyhow::Result;
use semantic_kernel::{Kernel, KernelBuilder, async_trait};
use sk_openai::OpenAIClient;
use sk_agent::{Agent, chat_completion_agent::ChatCompletionAgent, thread::AgentThread};
use std::env;

const REVIEWER_NAME: &str = "ArtDirector";
const REVIEWER_INSTRUCTIONS: &str = r#"
You are an art director who has opinions about copywriting born of a love for David Ogilvy.
The goal is to determine if the given copy is acceptable to print.
If so, state that it is approved.
If not, provide insight on how to refine suggested copy without example.
"#;

const COPYWRITER_NAME: &str = "CopyWriter";
const COPYWRITER_INSTRUCTIONS: &str = r#"
You are a copywriter with ten years of experience and are known for brevity and a dry humor.
The goal is to refine and decide on the single best copy as an expert in the field.
Only provide a single proposal per response.
You're laser focused on the goal at hand.
Don't waste time with chit chat.
Consider suggestions when refining an idea.
"#;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize environment and logging
    dotenv::dotenv().ok();
    tracing_subscriber::fmt::init();

    println!("🤖 Semantic Kernel Rust - Step 3: Agent Group Chat");
    println!("===================================================\n");

    // Example 1: Two-agent group chat with termination strategy
    println!("Example 1: Art Director + Copywriter Collaboration");
    println!("==================================================");
    
    agent_group_chat_collaboration().await?;

    // Example 2: Multi-turn conversation management
    println!("\nExample 2: Multi-Turn Conversation Management");
    println!("=============================================");
    
    multi_turn_conversation().await?;

    // Example 3: Different termination strategies
    println!("\nExample 3: Custom Termination Strategies");
    println!("========================================");
    
    custom_termination_strategies().await?;

    println!("\n✅ Step3 Chat example completed!");

    Ok(())
}

/// Demonstrate two-agent collaboration with approval termination
async fn agent_group_chat_collaboration() -> Result<()> {
    // Create agents with specialized roles
    let art_director = create_art_director().await?;
    let copywriter = create_copywriter().await?;
    
    println!("🎭 Created agents:");
    println!("  - {} (Art Director): Reviews and approves copy", art_director.name().unwrap_or("Unknown"));
    println!("  - {} (Copywriter): Creates and refines copy", copywriter.name().unwrap_or("Unknown"));
    
    // Simulate group chat conversation
    let concept = "concept: maps made out of egg cartons.";
    println!("\n👤 User: {}", concept);
    
    let mut conversation = AgentGroupChat::new(vec![copywriter, art_director]);
    let result = conversation.execute_conversation(concept, 6).await?;
    
    println!("\n📊 Conversation completed!");
    println!("Total turns: {}", result.turns);
    println!("Final status: {}", if result.approved { "✅ Approved" } else { "🔄 In Progress" });
    
    Ok(())
}

/// Demonstrate multi-turn conversation management
async fn multi_turn_conversation() -> Result<()> {
    let strategist = create_marketing_strategist().await?;
    let analyst = create_data_analyst().await?;
    
    println!("🧠 Created specialized team:");
    println!("  - Marketing Strategist: Campaign planning");
    println!("  - Data Analyst: Performance insights");
    
    let topics = vec![
        "How should we approach social media marketing for eco-friendly products?",
        "What metrics should we track for success?",
        "How can we optimize our current campaigns?",
    ];
    
    let mut conversation = AgentGroupChat::new(vec![strategist, analyst]);
    
    for (i, topic) in topics.iter().enumerate() {
        println!("\n🔹 Discussion {}: {}", i + 1, topic);
        let result = conversation.execute_conversation(topic, 4).await?;
        println!("   Completed in {} turns", result.turns);
    }
    
    Ok(())
}

/// Demonstrate different termination strategies
async fn custom_termination_strategies() -> Result<()> {
    let researcher = create_researcher().await?;
    let reviewer = create_reviewer().await?;
    
    println!("📚 Research + Review Team:");
    println!("  - Researcher: Gathers information");
    println!("  - Reviewer: Validates findings");
    
    // Short conversation with early termination
    let query = "What are the key benefits of renewable energy?";
    println!("\n🔍 Research Query: {}", query);
    
    let mut conversation = AgentGroupChat::new(vec![researcher, reviewer]);
    let result = conversation.execute_conversation_with_strategy(
        query, 
        8,
        TerminationStrategy::KeywordBased(vec!["comprehensive".to_string(), "complete".to_string()])
    ).await?;
    
    println!("Research completed in {} turns", result.turns);
    println!("Termination reason: {}", result.termination_reason);
    
    Ok(())
}

/// Create an art director agent
async fn create_art_director() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name(REVIEWER_NAME)
        .instructions(REVIEWER_INSTRUCTIONS)
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create art director: {}", e))
}

/// Create a copywriter agent
async fn create_copywriter() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name(COPYWRITER_NAME)
        .instructions(COPYWRITER_INSTRUCTIONS)
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create copywriter: {}", e))
}

/// Create a marketing strategist agent
async fn create_marketing_strategist() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name("MarketingStrategist")
        .instructions("You are a marketing strategist with 15 years of experience. Provide strategic insights, campaign ideas, and market positioning advice. Be concise but thorough.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create strategist: {}", e))
}

/// Create a data analyst agent
async fn create_data_analyst() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name("DataAnalyst")
        .instructions("You are a data analyst specializing in marketing metrics. Provide data-driven insights, suggest KPIs, and analyze performance trends. Focus on actionable recommendations.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create analyst: {}", e))
}

/// Create a researcher agent
async fn create_researcher() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name("Researcher")
        .instructions("You are a thorough researcher. Gather comprehensive information on topics, provide detailed findings, and ensure accuracy. End responses with 'Research complete' when done.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create researcher: {}", e))
}

/// Create a reviewer agent
async fn create_reviewer() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name("Reviewer")
        .instructions("You are a critical reviewer. Validate information, check for completeness, and provide feedback. Use 'comprehensive' when content meets all requirements.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create reviewer: {}", e))
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

// ===== AGENT GROUP CHAT IMPLEMENTATION =====

/// Agent group chat coordinator
struct AgentGroupChat {
    agents: Vec<ChatCompletionAgent>,
    thread: AgentThread,
    current_agent_index: usize,
}

impl AgentGroupChat {
    fn new(agents: Vec<ChatCompletionAgent>) -> Self {
        Self {
            agents,
            thread: AgentThread::new(),
            current_agent_index: 0,
        }
    }
    
    /// Execute a conversation with basic turn-based coordination
    async fn execute_conversation(&mut self, initial_message: &str, max_turns: usize) -> Result<ConversationResult> {
        let mut turns = 0;
        let mut current_message = initial_message.to_string();
        let mut approved = false;
        
        for turn in 0..max_turns {
            let agent = &self.agents[self.current_agent_index];
            
            println!("\n🎤 {} (Turn {}):", agent.name().unwrap_or("Agent"), turn + 1);
            
            let response = agent.invoke_async(&mut self.thread, &current_message).await
                .map_err(|e| anyhow::anyhow!("Failed to invoke agent: {}", e))?;
            
            println!("   {}", response.content);
            
            // Check for approval termination
            if response.content.to_lowercase().contains("approve") {
                approved = true;
                turns = turn + 1;
                break;
            }
            
            // Switch to next agent
            self.current_agent_index = (self.current_agent_index + 1) % self.agents.len();
            current_message = response.content;
            turns = turn + 1;
        }
        
        Ok(ConversationResult {
            turns,
            approved,
            termination_reason: if approved { "Approved".to_string() } else { "Max turns reached".to_string() },
        })
    }
    
    /// Execute a conversation with custom termination strategy
    async fn execute_conversation_with_strategy(
        &mut self, 
        initial_message: &str, 
        max_turns: usize, 
        strategy: TerminationStrategy
    ) -> Result<ConversationResult> {
        let mut turns = 0;
        let mut current_message = initial_message.to_string();
        
        for turn in 0..max_turns {
            let agent = &self.agents[self.current_agent_index];
            
            println!("\n🎤 {} (Turn {}):", agent.name().unwrap_or("Agent"), turn + 1);
            
            let response = agent.invoke_async(&mut self.thread, &current_message).await
                .map_err(|e| anyhow::anyhow!("Failed to invoke agent: {}", e))?;
            
            println!("   {}", response.content);
            
            // Check termination strategy
            if strategy.should_terminate(&response.content) {
                turns = turn + 1;
                return Ok(ConversationResult {
                    turns,
                    approved: true,
                    termination_reason: strategy.reason(),
                });
            }
            
            // Switch to next agent
            self.current_agent_index = (self.current_agent_index + 1) % self.agents.len();
            current_message = response.content;
            turns = turn + 1;
        }
        
        Ok(ConversationResult {
            turns,
            approved: false,
            termination_reason: "Max turns reached".to_string(),
        })
    }
}

/// Conversation result summary
struct ConversationResult {
    turns: usize,
    approved: bool,
    termination_reason: String,
}

/// Termination strategy for conversations
enum TerminationStrategy {
    KeywordBased(Vec<String>),
    ApprovalBased,
    MaxTurns(usize),
}

impl TerminationStrategy {
    fn should_terminate(&self, message: &str) -> bool {
        match self {
            TerminationStrategy::KeywordBased(keywords) => {
                keywords.iter().any(|keyword| message.to_lowercase().contains(&keyword.to_lowercase()))
            },
            TerminationStrategy::ApprovalBased => {
                message.to_lowercase().contains("approve")
            },
            TerminationStrategy::MaxTurns(_) => false, // Handled externally
        }
    }
    
    fn reason(&self) -> String {
        match self {
            TerminationStrategy::KeywordBased(_) => "Keyword match found".to_string(),
            TerminationStrategy::ApprovalBased => "Content approved".to_string(),
            TerminationStrategy::MaxTurns(_) => "Maximum turns reached".to_string(),
        }
    }
}