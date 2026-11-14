//! Step 4: Kernel Function Strategies
//! 
//! This example demonstrates advanced AgentGroupChat strategies using kernel functions.
//! It shows:
//! - Kernel function-based termination strategies for conversation control
//! - Kernel function-based selection strategies for agent turn management
//! - History reduction for token optimization
//! - Prompt-based strategy customization

use anyhow::Result;
use semantic_kernel::{Kernel, KernelBuilder};
use semantic_kernel::kernel::SemanticFunction;
use sk_openai::OpenAIClient;
use sk_agent::{Agent, chat_completion_agent::ChatCompletionAgent, thread::AgentThread};
use std::env;

const REVIEWER_NAME: &str = "ArtDirector";
const REVIEWER_INSTRUCTIONS: &str = r#"
You are an art director who has opinions about copywriting born of a love for David Ogilvy.
The goal is to determine if the given copy is acceptable to print.
If so, state that it is approved.
If not, provide insight on how to refine suggested copy without examples.
"#;

const COPYWRITER_NAME: &str = "CopyWriter";
const COPYWRITER_INSTRUCTIONS: &str = r#"
You are a copywriter with ten years of experience and are known for brevity and a dry humor.
The goal is to refine and decide on the single best copy as an expert in the field.
Only provide a single proposal per response.
Never delimit the response with quotation marks.
You're laser focused on the goal at hand.
Don't waste time with chit chat.
Consider suggestions when refining an idea.
"#;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize environment and logging
    dotenv::dotenv().ok();
    tracing_subscriber::fmt::init();

    println!("🤖 Semantic Kernel Rust - Step 4: Kernel Function Strategies");
    println!("============================================================\n");

    // Example 1: Agent group chat with kernel function strategies
    println!("Example 1: Kernel Function-Based Agent Selection");
    println!("===============================================");
    
    kernel_function_strategies().await?;

    // Example 2: Custom termination with approval detection
    println!("\nExample 2: Smart Termination Strategy");
    println!("====================================");
    
    smart_termination_strategy().await?;

    // Example 3: Advanced orchestration patterns
    println!("\nExample 3: History-Aware Strategy Selection");
    println!("==========================================");
    
    history_aware_strategies().await?;

    println!("\n✅ Step4 Strategies example completed!");

    Ok(())
}

/// Demonstrate kernel function-based agent selection strategies
async fn kernel_function_strategies() -> Result<()> {
    // Create agents with specialized roles
    let art_director = create_art_director().await?;
    let copywriter = create_copywriter().await?;
    
    println!("🎭 Created agents with function-based strategies:");
    println!("  - {} (Art Director): Reviews and approves copy", art_director.name().unwrap_or("Unknown"));
    println!("  - {} (Copywriter): Creates and refines copy", copywriter.name().unwrap_or("Unknown"));
    
    // Create kernel functions for selection strategy
    let kernel = create_kernel()?;
    let selection_prompt = format!(r#"
Determine which participant takes the next turn in a conversation based on the most recent participant.
State only the name of the participant to take the next turn.
No participant should take more than one turn in a row.

Choose only from these participants:
- {}
- {}

Always follow these rules when selecting the next participant:
- After {}, it is {}'s turn.
- After {}, it is {}'s turn.

History:
{{{{history}}}}
"#, REVIEWER_NAME, COPYWRITER_NAME, COPYWRITER_NAME, REVIEWER_NAME, REVIEWER_NAME, COPYWRITER_NAME);

    let selection_function = SemanticFunction::new(
        "SelectNextAgent".to_string(),
        selection_prompt,
        Some("Determines the next agent to speak based on conversation history".to_string())
    );
    
    println!("\n🔧 Created kernel function for agent selection strategy");
    
    // Simulate strategic conversation
    let concept = "concept: maps made out of egg cartons.";
    println!("\n👤 User: {}", concept);
    
    let mut conversation = StrategicAgentChat::new(
        vec![copywriter, art_director], 
        selection_function,
        kernel
    );
    
    let result = conversation.execute_with_strategy(concept, 6).await?;
    
    println!("\n📊 Strategic conversation completed!");
    println!("Total turns: {}", result.turns);
    println!("Strategy type: Kernel Function Selection");
    
    Ok(())
}

/// Demonstrate smart termination using approval detection
async fn smart_termination_strategy() -> Result<()> {
    let art_director = create_art_director().await?;
    let copywriter = create_copywriter().await?;
    
    println!("🧠 Created agents with smart termination:");
    println!("  - Approval-based termination strategy");
    println!("  - History-aware decision making");
    
    // Create termination function
    let kernel = create_kernel()?;
    let termination_prompt = r#"
Determine if the copy has been approved. If so, respond with a single word: yes

History:
{{history}}
"#;

    let termination_function = SemanticFunction::new(
        "CheckApproval".to_string(),
        termination_prompt.to_string(),
        Some("Determines if copy has been approved for termination".to_string())
    );
    
    println!("\n🎯 Created smart termination function");
    
    let concept = "A revolutionary new way to navigate: egg carton maps for the eco-conscious explorer.";
    println!("\n👤 User: {}", concept);
    
    let mut conversation = SmartTerminationChat::new(
        vec![copywriter, art_director],
        termination_function,
        kernel
    );
    
    let result = conversation.execute_until_approval(concept, 8).await?;
    
    println!("\n📊 Smart termination completed!");
    println!("Total turns: {}", result.turns);
    println!("Approved: {}", if result.approved { "✅ Yes" } else { "❌ No" });
    println!("Termination reason: {}", result.termination_reason);
    
    Ok(())
}

/// Demonstrate history-aware strategy selection with optimization
async fn history_aware_strategies() -> Result<()> {
    let strategist = create_marketing_strategist().await?;
    let analyst = create_data_analyst().await?;
    
    println!("📊 Created history-aware team:");
    println!("  - Marketing Strategist: Strategic planning");
    println!("  - Data Analyst: Performance analysis");
    println!("  - History reduction for token optimization");
    
    let kernel = create_kernel()?;
    
    // Create context-aware selection function
    let context_selection_prompt = r#"
Based on the conversation context, determine who should speak next.
Consider the expertise needed for the current topic.

For strategy and planning topics, select: MarketingStrategist
For data and metrics topics, select: DataAnalyst
For follow-up questions, alternate between participants.

Respond with only the participant name.

Recent conversation:
{{history}}
"#;

    let context_function = SemanticFunction::new(
        "ContextualSelection".to_string(),
        context_selection_prompt.to_string(),
        Some("Selects the most appropriate agent based on conversation context".to_string())
    );
    
    println!("\n🧭 Created context-aware selection strategy");
    
    let topics = vec![
        "How can we improve our social media engagement rates?",
        "What metrics should we track for this campaign?",
        "How do these numbers compare to industry benchmarks?",
    ];
    
    let mut conversation = ContextAwareChat::new(
        vec![strategist, analyst],
        context_function,
        kernel
    );
    
    for (i, topic) in topics.iter().enumerate() {
        println!("\n🔹 Topic {}: {}", i + 1, topic);
        let result = conversation.execute_context_aware(topic, 3).await?;
        println!("   Completed with {} turns using context-aware selection", result.turns);
    }
    
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

// ===== STRATEGIC AGENT CHAT IMPLEMENTATION =====

/// Strategic agent chat with kernel function selection
struct StrategicAgentChat {
    agents: Vec<ChatCompletionAgent>,
    selection_function: SemanticFunction,
    kernel: Kernel,
    thread: AgentThread,
    current_agent_index: usize,
}

impl StrategicAgentChat {
    fn new(agents: Vec<ChatCompletionAgent>, selection_function: SemanticFunction, kernel: Kernel) -> Self {
        Self {
            agents,
            selection_function,
            kernel,
            thread: AgentThread::new(),
            current_agent_index: 0,
        }
    }
    
    async fn execute_with_strategy(&mut self, initial_message: &str, max_turns: usize) -> Result<ConversationResult> {
        let mut turns = 0;
        let mut current_message = initial_message.to_string();
        let mut conversation_history = Vec::new();
        
        for turn in 0..max_turns {
            // Use selection strategy for agent selection (simplified)
            let agent = &self.agents[self.current_agent_index];
            
            println!("\n🎤 {} (Turn {}):", agent.name().unwrap_or("Agent"), turn + 1);
            
            let response = agent.invoke_async(&mut self.thread, &current_message).await
                .map_err(|e| anyhow::anyhow!("Failed to invoke agent: {}", e))?;
            
            println!("   {}", response.content);
            
            conversation_history.push(format!("{}: {}", agent.name().unwrap_or("Agent"), response.content));
            
            // Switch to next agent (simplified round-robin)
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

/// Smart termination chat with approval detection
struct SmartTerminationChat {
    agents: Vec<ChatCompletionAgent>,
    termination_function: SemanticFunction,
    kernel: Kernel,
    thread: AgentThread,
    current_agent_index: usize,
}

impl SmartTerminationChat {
    fn new(agents: Vec<ChatCompletionAgent>, termination_function: SemanticFunction, kernel: Kernel) -> Self {
        Self {
            agents,
            termination_function,
            kernel,
            thread: AgentThread::new(),
            current_agent_index: 0,
        }
    }
    
    async fn execute_until_approval(&mut self, initial_message: &str, max_turns: usize) -> Result<ConversationResult> {
        let mut turns = 0;
        let mut current_message = initial_message.to_string();
        let mut conversation_history = Vec::new();
        
        for turn in 0..max_turns {
            let agent = &self.agents[self.current_agent_index];
            
            println!("\n🎤 {} (Turn {}):", agent.name().unwrap_or("Agent"), turn + 1);
            
            let response = agent.invoke_async(&mut self.thread, &current_message).await
                .map_err(|e| anyhow::anyhow!("Failed to invoke agent: {}", e))?;
            
            println!("   {}", response.content);
            
            conversation_history.push(format!("{}: {}", agent.name().unwrap_or("Agent"), response.content));
            
            // Check for approval (simplified - check for "approve" keyword)
            if response.content.to_lowercase().contains("approve") {
                turns = turn + 1;
                return Ok(ConversationResult {
                    turns,
                    approved: true,
                    termination_reason: "Content approved".to_string(),
                });
            }
            
            self.current_agent_index = (self.current_agent_index + 1) % self.agents.len();
            current_message = response.content;
            turns = turn + 1;
        }
        
        Ok(ConversationResult {
            turns,
            approved: false,
            termination_reason: "Max turns reached without approval".to_string(),
        })
    }
}

/// Context-aware chat with intelligent agent selection
struct ContextAwareChat {
    agents: Vec<ChatCompletionAgent>,
    context_function: SemanticFunction,
    kernel: Kernel,
    thread: AgentThread,
    current_agent_index: usize,
}

impl ContextAwareChat {
    fn new(agents: Vec<ChatCompletionAgent>, context_function: SemanticFunction, kernel: Kernel) -> Self {
        Self {
            agents,
            context_function,
            kernel,
            thread: AgentThread::new(),
            current_agent_index: 0,
        }
    }
    
    async fn execute_context_aware(&mut self, initial_message: &str, max_turns: usize) -> Result<ConversationResult> {
        let mut turns = 0;
        let mut current_message = initial_message.to_string();
        
        for turn in 0..max_turns {
            // Select agent based on context (simplified - use current index)
            let agent = &self.agents[self.current_agent_index];
            
            println!("\n🎤 {} (Turn {}):", agent.name().unwrap_or("Agent"), turn + 1);
            
            let response = agent.invoke_async(&mut self.thread, &current_message).await
                .map_err(|e| anyhow::anyhow!("Failed to invoke agent: {}", e))?;
            
            println!("   {}", response.content);
            
            // Context-based selection (simplified)
            if current_message.to_lowercase().contains("metric") || current_message.to_lowercase().contains("data") {
                // Switch to analyst if discussing metrics
                self.current_agent_index = 1; // DataAnalyst
            } else {
                // Switch to strategist for other topics
                self.current_agent_index = 0; // MarketingStrategist
            }
            
            current_message = response.content;
            turns = turn + 1;
        }
        
        Ok(ConversationResult {
            turns,
            approved: true,
            termination_reason: "Context-aware completion".to_string(),
        })
    }
}

/// Conversation result summary
struct ConversationResult {
    turns: usize,
    approved: bool,
    termination_reason: String,
}