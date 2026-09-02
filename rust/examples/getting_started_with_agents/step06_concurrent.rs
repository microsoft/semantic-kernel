//! Step 6: Concurrent Agent Orchestration
//! 
//! This example demonstrates concurrent execution of multiple agents on the same task.
//! It shows:
//! - Parallel agent execution for comparative analysis
//! - Concurrent orchestration patterns
//! - Multiple perspective gathering from different expert agents
//! - Result aggregation from parallel executions

use anyhow::Result;
use semantic_kernel::{Kernel, KernelBuilder};
use sk_openai::OpenAIClient;
use sk_agent::{Agent, chat_completion_agent::ChatCompletionAgent, thread::AgentThread};
use std::env;
use std::sync::Arc;
use tokio::task::JoinSet;
use futures::future::try_join_all;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize environment and logging
    dotenv::dotenv().ok();
    tracing_subscriber::fmt::init();

    println!("🤖 Semantic Kernel Rust - Step 6: Concurrent Agent Orchestration");
    println!("===============================================================\n");

    // Example 1: Concurrent expert analysis
    println!("Example 1: Concurrent Expert Analysis");
    println!("====================================");
    
    concurrent_expert_analysis().await?;

    // Example 2: Parallel perspective gathering
    println!("\nExample 2: Parallel Perspective Gathering");
    println!("========================================");
    
    parallel_perspective_gathering().await?;

    // Example 3: Multi-agent comparative analysis
    println!("\nExample 3: Multi-Agent Comparative Analysis");
    println!("==========================================");
    
    multi_agent_comparative_analysis().await?;

    println!("\n✅ Step6 Concurrent Orchestration example completed!");

    Ok(())
}

/// Demonstrate concurrent execution of expert agents on the same task
async fn concurrent_expert_analysis() -> Result<()> {
    // Create expert agents
    let physicist = create_physicist_agent().await?;
    let chemist = create_chemist_agent().await?;
    
    println!("🔬 Created expert agents:");
    println!("  - {} (Physics expert)", physicist.name().unwrap_or("Unknown"));
    println!("  - {} (Chemistry expert)", chemist.name().unwrap_or("Unknown"));
    
    let question = "What is temperature?";
    println!("\n❓ Question: {}", question);
    
    // Execute both agents concurrently
    let orchestrator = ConcurrentOrchestrator::new(vec![Arc::new(physicist), Arc::new(chemist)]);
    let results = orchestrator.execute_concurrently(question).await?;
    
    println!("\n📊 Concurrent Analysis Results:");
    for (i, result) in results.iter().enumerate() {
        println!("   Expert {}: {}", i + 1, result.content);
    }
    
    Ok(())
}

/// Demonstrate parallel perspective gathering from multiple viewpoints
async fn parallel_perspective_gathering() -> Result<()> {
    // Create perspective agents
    let historian = create_historian_agent().await?;
    let economist = create_economist_agent().await?;
    let sociologist = create_sociologist_agent().await?;
    
    println!("👥 Created perspective agents:");
    println!("  - {} (Historical perspective)", historian.name().unwrap_or("Unknown"));
    println!("  - {} (Economic perspective)", economist.name().unwrap_or("Unknown"));
    println!("  - {} (Social perspective)", sociologist.name().unwrap_or("Unknown"));
    
    let topic = "How has technology changed human communication?";
    println!("\n📝 Topic: {}", topic);
    
    // Gather perspectives in parallel
    let orchestrator = PerspectiveGatherer::new(vec![Arc::new(historian), Arc::new(economist), Arc::new(sociologist)]);
    let perspectives = orchestrator.gather_perspectives(topic).await?;
    
    println!("\n🔍 Multi-Perspective Analysis:");
    for perspective in perspectives {
        println!("   {}: {}", perspective.agent_name, perspective.analysis);
    }
    
    Ok(())
}

/// Demonstrate multi-agent comparative analysis with result synthesis
async fn multi_agent_comparative_analysis() -> Result<()> {
    // Create analysis agents
    let researcher = create_researcher_agent().await?;
    let critic = create_critic_agent().await?;
    let synthesizer = create_synthesizer_agent().await?;
    
    println!("🧠 Created analysis team:");
    println!("  - {} (Research & facts)", researcher.name().unwrap_or("Unknown"));
    println!("  - {} (Critical analysis)", critic.name().unwrap_or("Unknown"));
    println!("  - {} (Synthesis & conclusions)", synthesizer.name().unwrap_or("Unknown"));
    
    let research_question = "What are the key challenges and opportunities in renewable energy adoption?";
    println!("\n🔬 Research Question: {}", research_question);
    
    // Perform concurrent analysis
    let analyzer = ComparativeAnalyzer::new(vec![Arc::new(researcher), Arc::new(critic), Arc::new(synthesizer)]);
    let analysis = analyzer.perform_comparative_analysis(research_question).await?;
    
    println!("\n📈 Comparative Analysis Results:");
    println!("   Research Findings: {}", analysis.research);
    println!("   Critical Assessment: {}", analysis.critique);
    println!("   Synthesized Conclusion: {}", analysis.synthesis);
    
    Ok(())
}

/// Create a physicist agent
async fn create_physicist_agent() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name("Physicist")
        .instructions("You are an expert in physics. You answer questions from a physics perspective with scientific accuracy and clear explanations.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create physicist: {}", e))
}

/// Create a chemist agent
async fn create_chemist_agent() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name("Chemist")
        .instructions("You are an expert in chemistry. You answer questions from a chemistry perspective with molecular-level insights and practical applications.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create chemist: {}", e))
}

/// Create a historian agent
async fn create_historian_agent() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name("Historian")
        .instructions("You are a historian. Provide historical context and evolutionary perspectives on topics, tracing how things developed over time.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create historian: {}", e))
}

/// Create an economist agent
async fn create_economist_agent() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name("Economist")
        .instructions("You are an economist. Analyze topics from economic perspectives including costs, benefits, market forces, and financial implications.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create economist: {}", e))
}

/// Create a sociologist agent
async fn create_sociologist_agent() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name("Sociologist")
        .instructions("You are a sociologist. Examine topics through the lens of human behavior, social structures, and cultural implications.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create sociologist: {}", e))
}

/// Create a researcher agent
async fn create_researcher_agent() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name("Researcher")
        .instructions("You are a thorough researcher. Provide comprehensive factual information, data, and evidence-based insights on topics.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create researcher: {}", e))
}

/// Create a critic agent
async fn create_critic_agent() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name("Critic")
        .instructions("You are a critical analyst. Examine topics for potential flaws, limitations, counterarguments, and areas of concern.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create critic: {}", e))
}

/// Create a synthesizer agent
async fn create_synthesizer_agent() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name("Synthesizer")
        .instructions("You are a synthesis expert. Combine different perspectives into coherent conclusions and actionable recommendations.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create synthesizer: {}", e))
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

// ===== CONCURRENT ORCHESTRATION IMPLEMENTATIONS =====

/// Concurrent orchestrator for parallel agent execution
struct ConcurrentOrchestrator {
    agents: Vec<Arc<ChatCompletionAgent>>,
}

impl ConcurrentOrchestrator {
    fn new(agents: Vec<Arc<ChatCompletionAgent>>) -> Self {
        Self { agents }
    }
    
    async fn execute_concurrently(&self, input: &str) -> Result<Vec<semantic_kernel::content::ChatMessageContent>> {
        // Create async tasks for each agent
        let mut task_set = JoinSet::new();
        
        for agent in &self.agents {
            let agent_arc = Arc::clone(agent);
            let input_clone = input.to_string();
            
            task_set.spawn(async move {
                let mut thread = AgentThread::new();
                agent_arc.invoke_async(&mut thread, &input_clone).await
            });
        }
        
        // Collect results as they complete
        let mut results = Vec::new();
        while let Some(task_result) = task_set.join_next().await {
            match task_result {
                Ok(Ok(response)) => results.push(response),
                Ok(Err(e)) => return Err(anyhow::anyhow!("Agent execution failed: {}", e)),
                Err(e) => return Err(anyhow::anyhow!("Task join failed: {}", e)),
            }
        }
        
        Ok(results)
    }
}

/// Perspective gatherer for multi-viewpoint analysis
struct PerspectiveGatherer {
    agents: Vec<Arc<ChatCompletionAgent>>,
}

#[derive(Debug)]
struct Perspective {
    agent_name: String,
    analysis: String,
}

impl PerspectiveGatherer {
    fn new(agents: Vec<Arc<ChatCompletionAgent>>) -> Self {
        Self { agents }
    }
    
    async fn gather_perspectives(&self, topic: &str) -> Result<Vec<Perspective>> {
        // Execute all agents concurrently using try_join_all
        let futures: Vec<_> = self.agents.iter().map(|agent| {
            let topic = topic.to_string();
            let agent_arc = Arc::clone(agent);
            async move {
                let mut thread = AgentThread::new();
                let response = agent_arc.invoke_async(&mut thread, &topic).await?;
                Ok::<Perspective, anyhow::Error>(Perspective {
                    agent_name: agent_arc.name().unwrap_or("Unknown").to_string(),
                    analysis: response.content,
                })
            }
        }).collect();
        
        try_join_all(futures).await
    }
}

/// Comparative analyzer for multi-agent research analysis
struct ComparativeAnalyzer {
    agents: Vec<Arc<ChatCompletionAgent>>,
}

#[derive(Debug)]
struct ComparativeAnalysis {
    research: String,
    critique: String,
    synthesis: String,
}

impl ComparativeAnalyzer {
    fn new(agents: Vec<Arc<ChatCompletionAgent>>) -> Self {
        Self { agents }
    }
    
    async fn perform_comparative_analysis(&self, question: &str) -> Result<ComparativeAnalysis> {
        // Execute first three agents concurrently
        let futures: Vec<_> = self.agents.iter().take(3).map(|agent| {
            let question = question.to_string();
            let agent_arc = Arc::clone(agent);
            async move {
                let mut thread = AgentThread::new();
                agent_arc.invoke_async(&mut thread, &question).await
            }
        }).collect();
        
        let results = try_join_all(futures).await?;
        
        Ok(ComparativeAnalysis {
            research: results.get(0).map(|r| r.content.clone()).unwrap_or_default(),
            critique: results.get(1).map(|r| r.content.clone()).unwrap_or_default(),
            synthesis: results.get(2).map(|r| r.content.clone()).unwrap_or_default(),
        })
    }
}

