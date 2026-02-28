//! Step 7: Sequential Agent Orchestration
//! 
//! This example demonstrates sequential execution where agents form a pipeline.
//! It shows:
//! - Sequential agent workflows (output of one becomes input of next)
//! - Pipeline orchestration patterns
//! - Multi-stage content processing and refinement
//! - Agent specialization in processing chains

use anyhow::Result;
use semantic_kernel::{Kernel, KernelBuilder};
use sk_openai::OpenAIClient;
use sk_agent::{Agent, chat_completion_agent::ChatCompletionAgent, thread::AgentThread};
use std::env;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize environment and logging
    dotenv::dotenv().ok();
    tracing_subscriber::fmt::init();

    println!("🤖 Semantic Kernel Rust - Step 7: Sequential Agent Orchestration");
    println!("===============================================================\n");

    // Example 1: Marketing content pipeline
    println!("Example 1: Marketing Content Pipeline");
    println!("====================================");
    
    marketing_content_pipeline().await?;

    // Example 2: Research and analysis workflow
    println!("\nExample 2: Research and Analysis Workflow");
    println!("========================================");
    
    research_analysis_workflow().await?;

    // Example 3: Multi-stage content refinement
    println!("\nExample 3: Multi-Stage Content Refinement");
    println!("========================================");
    
    multi_stage_refinement().await?;

    println!("\n✅ Step7 Sequential Orchestration example completed!");

    Ok(())
}

/// Demonstrate marketing content pipeline with analysis → writing → editing
async fn marketing_content_pipeline() -> Result<()> {
    // Create specialized agents for content pipeline
    let analyst = create_marketing_analyst().await?;
    let copywriter = create_copywriter().await?;
    let editor = create_editor().await?;
    
    println!("📝 Created marketing content pipeline:");
    println!("  1. {} (Extract features & audience)", analyst.name().unwrap_or("Unknown"));
    println!("  2. {} (Create compelling copy)", copywriter.name().unwrap_or("Unknown"));
    println!("  3. {} (Polish and finalize)", editor.name().unwrap_or("Unknown"));
    
    let product_description = "An eco-friendly stainless steel water bottle that keeps drinks cold for 24 hours";
    println!("\n📦 Product: {}", product_description);
    
    // Execute sequential pipeline
    let pipeline = SequentialOrchestrator::new(vec![analyst, copywriter, editor]);
    let final_result = pipeline.execute_pipeline(product_description).await?;
    
    println!("\n🎯 Final Marketing Copy:");
    println!("{}", final_result.final_output);
    
    println!("\n📊 Pipeline Execution Summary:");
    for (i, stage) in final_result.stages.iter().enumerate() {
        println!("   Stage {}: {} → {}", i + 1, stage.agent_name, 
            stage.output.chars().take(60).collect::<String>() + "...");
    }
    
    Ok(())
}

/// Demonstrate research and analysis workflow
async fn research_analysis_workflow() -> Result<()> {
    // Create research workflow agents
    let researcher = create_researcher().await?;
    let analyzer = create_data_analyzer().await?;
    let synthesizer = create_synthesizer().await?;
    
    println!("🔬 Created research workflow:");
    println!("  1. {} (Gather information)", researcher.name().unwrap_or("Unknown"));
    println!("  2. {} (Analyze findings)", analyzer.name().unwrap_or("Unknown"));
    println!("  3. {} (Synthesize conclusions)", synthesizer.name().unwrap_or("Unknown"));
    
    let research_topic = "Impact of remote work on team productivity";
    println!("\n🔍 Research Topic: {}", research_topic);
    
    // Execute research workflow
    let workflow = ResearchWorkflow::new(vec![researcher, analyzer, synthesizer]);
    let research_result = workflow.execute_research(research_topic).await?;
    
    println!("\n📋 Research Report:");
    println!("Raw Data: {}", research_result.raw_data.chars().take(100).collect::<String>() + "...");
    println!("Analysis: {}", research_result.analysis.chars().take(100).collect::<String>() + "...");
    println!("Synthesis: {}", research_result.synthesis);
    
    Ok(())
}

/// Demonstrate multi-stage content refinement
async fn multi_stage_refinement() -> Result<()> {
    // Create refinement pipeline
    let brainstormer = create_brainstormer().await?;
    let structurer = create_content_structurer().await?;
    let stylist = create_stylist().await?;
    let reviewer = create_final_reviewer().await?;
    
    println!("✨ Created content refinement pipeline:");
    println!("  1. {} (Generate ideas)", brainstormer.name().unwrap_or("Unknown"));
    println!("  2. {} (Structure content)", structurer.name().unwrap_or("Unknown"));
    println!("  3. {} (Apply style)", stylist.name().unwrap_or("Unknown"));
    println!("  4. {} (Final review)", reviewer.name().unwrap_or("Unknown"));
    
    let creative_brief = "Write a blog post about the future of artificial intelligence in healthcare";
    println!("\n💡 Creative Brief: {}", creative_brief);
    
    // Execute refinement pipeline
    let refiner = ContentRefiner::new(vec![brainstormer, structurer, stylist, reviewer]);
    let refined_content = refiner.refine_content(creative_brief).await?;
    
    println!("\n📄 Refined Content:");
    println!("{}", refined_content.final_content);
    
    println!("\n🔄 Refinement Stages:");
    for stage in refined_content.refinement_stages {
        println!("   {}: {}", stage.stage_name, 
            stage.improvement.chars().take(80).collect::<String>() + "...");
    }
    
    Ok(())
}

/// Create a marketing analyst agent
async fn create_marketing_analyst() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name("MarketingAnalyst")
        .instructions(r#"
You are a marketing analyst. Given a product description, identify:
- Key features
- Target audience  
- Unique selling points

Provide a structured analysis that can be used by a copywriter.
"#)
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create marketing analyst: {}", e))
}

/// Create a copywriter agent
async fn create_copywriter() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name("Copywriter")
        .instructions(r#"
You are a marketing copywriter. Given analysis of features, audience, and USPs,
compose compelling marketing copy (like a newsletter section) that highlights these points.
Output should be short (around 150 words), output just the copy as a single text block.
"#)
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create copywriter: {}", e))
}

/// Create an editor agent
async fn create_editor() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name("Editor")
        .instructions(r#"
You are an editor. Given draft copy, correct grammar, improve clarity, ensure consistent tone,
format and make it polished. Output the final improved copy as a single text block.
"#)
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create editor: {}", e))
}

/// Create a researcher agent
async fn create_researcher() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name("Researcher")
        .instructions("You are a thorough researcher. Gather comprehensive information and key facts about the given topic. Focus on current trends, statistics, and expert opinions.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create researcher: {}", e))
}

/// Create a data analyzer agent
async fn create_data_analyzer() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name("DataAnalyzer")
        .instructions("You are a data analyst. Take research findings and analyze patterns, trends, and implications. Identify key insights and correlations from the information provided.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create data analyzer: {}", e))
}

/// Create a synthesizer agent
async fn create_synthesizer() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name("Synthesizer")
        .instructions("You are a synthesis expert. Take analyzed data and create coherent conclusions, actionable recommendations, and clear summaries. Focus on practical implications.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create synthesizer: {}", e))
}

/// Create a brainstormer agent
async fn create_brainstormer() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name("Brainstormer")
        .instructions("You are a creative brainstormer. Generate innovative ideas, unique angles, and compelling concepts for the given topic. Focus on creativity and originality.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create brainstormer: {}", e))
}

/// Create a content structurer agent
async fn create_content_structurer() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name("ContentStructurer")
        .instructions("You are a content structurer. Take creative ideas and organize them into a logical, flowing structure with clear sections, headings, and narrative flow.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create content structurer: {}", e))
}

/// Create a stylist agent
async fn create_stylist() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name("Stylist")
        .instructions("You are a content stylist. Take structured content and apply engaging writing style, improve readability, add compelling language, and ensure consistent tone.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create stylist: {}", e))
}

/// Create a final reviewer agent
async fn create_final_reviewer() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name("FinalReviewer")
        .instructions("You are a final reviewer. Conduct a comprehensive review for accuracy, clarity, completeness, and impact. Make final polishing touches and ensure publication readiness.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create final reviewer: {}", e))
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

// ===== SEQUENTIAL ORCHESTRATION IMPLEMENTATIONS =====

/// Sequential orchestrator for pipeline execution
struct SequentialOrchestrator {
    agents: Vec<ChatCompletionAgent>,
}

#[derive(Debug)]
struct PipelineResult {
    final_output: String,
    stages: Vec<PipelineStage>,
}

#[derive(Debug)]
struct PipelineStage {
    agent_name: String,
    output: String,
}

impl SequentialOrchestrator {
    fn new(agents: Vec<ChatCompletionAgent>) -> Self {
        Self { agents }
    }
    
    async fn execute_pipeline(&self, initial_input: &str) -> Result<PipelineResult> {
        let mut current_input = initial_input.to_string();
        let mut stages = Vec::new();
        
        for agent in &self.agents {
            let mut thread = AgentThread::new();
            let response = agent.invoke_async(&mut thread, &current_input).await
                .map_err(|e| anyhow::anyhow!("Failed to invoke agent {}: {}", 
                    agent.name().unwrap_or("Unknown"), e))?;
            
            stages.push(PipelineStage {
                agent_name: agent.name().unwrap_or("Unknown").to_string(),
                output: response.content.clone(),
            });
            
            // Output becomes input for next stage
            current_input = response.content;
        }
        
        Ok(PipelineResult {
            final_output: current_input,
            stages,
        })
    }
}

/// Research workflow for sequential research processing
struct ResearchWorkflow {
    agents: Vec<ChatCompletionAgent>,
}

#[derive(Debug)]
struct ResearchResult {
    raw_data: String,
    analysis: String,
    synthesis: String,
}

impl ResearchWorkflow {
    fn new(agents: Vec<ChatCompletionAgent>) -> Self {
        Self { agents }
    }
    
    async fn execute_research(&self, topic: &str) -> Result<ResearchResult> {
        let mut current_input = topic.to_string();
        let mut outputs = Vec::new();
        
        for agent in &self.agents {
            let mut thread = AgentThread::new();
            let response = agent.invoke_async(&mut thread, &current_input).await
                .map_err(|e| anyhow::anyhow!("Failed to invoke research agent: {}", e))?;
            
            outputs.push(response.content.clone());
            current_input = response.content;
        }
        
        Ok(ResearchResult {
            raw_data: outputs.get(0).cloned().unwrap_or_default(),
            analysis: outputs.get(1).cloned().unwrap_or_default(),
            synthesis: outputs.get(2).cloned().unwrap_or_default(),
        })
    }
}

/// Content refiner for multi-stage content improvement
struct ContentRefiner {
    agents: Vec<ChatCompletionAgent>,
}

#[derive(Debug)]
struct RefinedContent {
    final_content: String,
    refinement_stages: Vec<RefinementStage>,
}

#[derive(Debug)]
struct RefinementStage {
    stage_name: String,
    improvement: String,
}

impl ContentRefiner {
    fn new(agents: Vec<ChatCompletionAgent>) -> Self {
        Self { agents }
    }
    
    async fn refine_content(&self, initial_brief: &str) -> Result<RefinedContent> {
        let mut current_content = initial_brief.to_string();
        let mut refinement_stages = Vec::new();
        
        let stage_names = vec!["Ideation", "Structure", "Style", "Review"];
        
        for (i, agent) in self.agents.iter().enumerate() {
            let mut thread = AgentThread::new();
            let response = agent.invoke_async(&mut thread, &current_content).await
                .map_err(|e| anyhow::anyhow!("Failed to invoke refinement agent: {}", e))?;
            
            refinement_stages.push(RefinementStage {
                stage_name: stage_names.get(i).unwrap_or(&"Unknown").to_string(),
                improvement: response.content.clone(),
            });
            
            current_content = response.content;
        }
        
        Ok(RefinedContent {
            final_content: current_content,
            refinement_stages,
        })
    }
}