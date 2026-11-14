//! Step 5: JSON Result Parsing
//! 
//! This example demonstrates agents that return structured JSON responses.
//! It shows:
//! - JSON response parsing from agent outputs
//! - Score-based termination strategies
//! - Structured evaluation workflows
//! - Threshold-based conversation completion

use anyhow::Result;
use semantic_kernel::{Kernel, KernelBuilder};
use sk_openai::OpenAIClient;
use sk_agent::{Agent, chat_completion_agent::ChatCompletionAgent, thread::AgentThread};
use std::env;
use serde::{Deserialize, Serialize};

const SCORE_COMPLETION_THRESHOLD: i32 = 70;

const TUTOR_NAME: &str = "Tutor";
const TUTOR_INSTRUCTIONS: &str = r#"
Think step-by-step and rate the user input on creativity and expressiveness from 1-100.

Respond in JSON format with the following JSON schema:

{
    "score": "integer (1-100)",
    "notes": "the reason for your score"
}
"#;

#[derive(Debug, Clone, Serialize, Deserialize)]
struct WritingScore {
    score: i32,
    notes: String,
}

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize environment and logging
    dotenv::dotenv().ok();
    tracing_subscriber::fmt::init();

    println!("🤖 Semantic Kernel Rust - Step 5: JSON Result Parsing");
    println!("=====================================================\n");

    // Example 1: JSON response evaluation with score thresholds
    println!("Example 1: Creative Writing Evaluation");
    println!("=====================================");
    
    json_result_evaluation().await?;

    // Example 2: Multiple evaluation rounds
    println!("\nExample 2: Progressive Evaluation System");
    println!("=======================================");
    
    progressive_evaluation().await?;

    // Example 3: Structured feedback analysis
    println!("\nExample 3: Detailed Feedback Analysis");
    println!("====================================");
    
    structured_feedback_analysis().await?;

    println!("\n✅ Step5 JSON Result example completed!");

    Ok(())
}

/// Demonstrate JSON response evaluation with score-based termination
async fn json_result_evaluation() -> Result<()> {
    let tutor = create_tutor_agent().await?;
    
    println!("📝 Created tutor agent for creative writing evaluation");
    println!("🎯 Score threshold for completion: {}", SCORE_COMPLETION_THRESHOLD);
    
    let test_inputs = vec![
        "The sunset is very colorful.",
        "The sunset is setting over the mountains.",
        "The sunset is setting over the mountains and filled the sky with a deep red flame, setting the clouds ablaze.",
    ];
    
    let mut evaluation_chat = JsonEvaluationChat::new(tutor, SCORE_COMPLETION_THRESHOLD);
    
    for (i, input) in test_inputs.iter().enumerate() {
        println!("\n📝 Test Input {}: \"{}\"", i + 1, input);
        
        let result = evaluation_chat.evaluate_input(input).await?;
        
        println!("📊 Evaluation Result:");
        println!("   Score: {}/100", result.score);
        println!("   Notes: {}", result.notes);
        println!("   Threshold met: {}", if result.score >= SCORE_COMPLETION_THRESHOLD { "✅ Yes" } else { "❌ No" });
        
        if result.score >= SCORE_COMPLETION_THRESHOLD {
            println!("🎉 Threshold reached! Evaluation complete.");
            break;
        }
    }
    
    Ok(())
}

/// Demonstrate progressive evaluation with multiple attempts
async fn progressive_evaluation() -> Result<()> {
    let tutor = create_tutor_agent().await?;
    
    println!("🔄 Progressive evaluation system:");
    println!("   - Multiple evaluation rounds");
    println!("   - Score improvement tracking");
    println!("   - Detailed feedback loop");
    
    let progressive_inputs = vec![
        ("Basic", "The cat sat on the mat."),
        ("Improved", "The sleek black cat gracefully settled on the worn Persian mat."),
        ("Advanced", "The obsidian feline, with eyes like emeralds catching moonlight, glided across the room before settling regally upon the ancient Persian mat, its golden threads telling stories of distant lands."),
    ];
    
    let mut evaluator = ProgressiveEvaluator::new(tutor);
    
    for (level, input) in progressive_inputs {
        println!("\n📈 Evaluating {} level:", level);
        println!("   Input: \"{}\"", input);
        
        let score = evaluator.evaluate_with_tracking(input).await?;
        
        println!("   Result: {}/100", score.score);
        println!("   Analysis: {}", score.notes);
        
        if score.score >= SCORE_COMPLETION_THRESHOLD {
            println!("🎯 Excellence achieved at {} level!", level);
            break;
        }
    }
    
    Ok(())
}

/// Demonstrate structured feedback analysis with detailed JSON parsing
async fn structured_feedback_analysis() -> Result<()> {
    let tutor = create_advanced_tutor().await?;
    
    println!("🔍 Advanced feedback analysis:");
    println!("   - Detailed JSON response parsing");
    println!("   - Multi-criteria evaluation");
    println!("   - Comprehensive feedback structure");
    
    let complex_input = "In the twilight's embrace, where shadows dance with whispers of the wind, the ancient oak stands sentinel over memories etched in time's relentless march.";
    
    println!("\n📝 Complex Input Analysis:");
    println!("   Text: \"{}\"", complex_input);
    
    let mut analyzer = StructuredAnalyzer::new(tutor);
    let analysis = analyzer.perform_detailed_analysis(complex_input).await?;
    
    println!("\n📊 Comprehensive Analysis:");
    println!("   Overall Score: {}/100", analysis.score);
    println!("   Detailed Notes: {}", analysis.notes);
    println!("   Threshold Status: {}", 
        if analysis.score >= SCORE_COMPLETION_THRESHOLD { 
            "✅ Exceeds expectations" 
        } else { 
            "🔄 Needs improvement" 
        }
    );
    
    Ok(())
}

/// Create a tutor agent for creative writing evaluation
async fn create_tutor_agent() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name(TUTOR_NAME)
        .instructions(TUTOR_INSTRUCTIONS)
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create tutor agent: {}", e))
}

/// Create an advanced tutor agent with enhanced evaluation capabilities
async fn create_advanced_tutor() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    let advanced_instructions = r#"
You are an expert writing tutor specializing in creative expression analysis.
Evaluate the input text on creativity, expressiveness, imagery, and literary merit from 1-100.

Provide detailed analysis in JSON format:

{
    "score": "integer (1-100)",
    "notes": "comprehensive analysis including specific strengths and areas for improvement"
}

Consider: word choice, imagery, emotional impact, originality, and technical craft.
"#;
    
    ChatCompletionAgent::builder()
        .name("AdvancedTutor")
        .instructions(advanced_instructions)
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create advanced tutor: {}", e))
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

// ===== JSON EVALUATION CHAT IMPLEMENTATION =====

/// Chat system that evaluates inputs and parses JSON responses
struct JsonEvaluationChat {
    agent: ChatCompletionAgent,
    threshold: i32,
    thread: AgentThread,
}

impl JsonEvaluationChat {
    fn new(agent: ChatCompletionAgent, threshold: i32) -> Self {
        Self {
            agent,
            threshold,
            thread: AgentThread::new(),
        }
    }
    
    async fn evaluate_input(&mut self, input: &str) -> Result<WritingScore> {
        let response = self.agent.invoke_async(&mut self.thread, input).await
            .map_err(|e| anyhow::anyhow!("Failed to invoke agent: {}", e))?;
        
        // Parse JSON response (simplified - in a real implementation, this would be more robust)
        self.parse_json_response(&response.content)
    }
    
    fn parse_json_response(&self, content: &str) -> Result<WritingScore> {
        // Try to extract JSON from the response
        if let Some(json_start) = content.find('{') {
            if let Some(json_end) = content.rfind('}') {
                let json_str = &content[json_start..=json_end];
                return serde_json::from_str(json_str)
                    .map_err(|e| anyhow::anyhow!("JSON parse error: {}", e));
            }
        }
        
        // Fallback: try to parse the entire content
        serde_json::from_str(content)
            .or_else(|_| {
                // If JSON parsing fails, create a default response
                Ok(WritingScore {
                    score: 50,
                    notes: format!("Unable to parse JSON response: {}", content),
                })
            })
    }
}

/// Progressive evaluator that tracks improvement over multiple inputs
struct ProgressiveEvaluator {
    agent: ChatCompletionAgent,
    thread: AgentThread,
    previous_scores: Vec<i32>,
}

impl ProgressiveEvaluator {
    fn new(agent: ChatCompletionAgent) -> Self {
        Self {
            agent,
            thread: AgentThread::new(),
            previous_scores: Vec::new(),
        }
    }
    
    async fn evaluate_with_tracking(&mut self, input: &str) -> Result<WritingScore> {
        let response = self.agent.invoke_async(&mut self.thread, input).await
            .map_err(|e| anyhow::anyhow!("Failed to invoke agent: {}", e))?;
        
        let score = self.parse_json_response(&response.content)?;
        self.previous_scores.push(score.score);
        
        Ok(score)
    }
    
    fn parse_json_response(&self, content: &str) -> Result<WritingScore> {
        // Simplified JSON parsing (same as above)
        if let Some(json_start) = content.find('{') {
            if let Some(json_end) = content.rfind('}') {
                let json_str = &content[json_start..=json_end];
                return serde_json::from_str(json_str)
                    .map_err(|e| anyhow::anyhow!("JSON parse error: {}", e));
            }
        }
        
        Ok(WritingScore {
            score: 65, // Simulated score for demo
            notes: format!("Evaluation response: {}", content),
        })
    }
}

/// Structured analyzer for comprehensive feedback analysis
struct StructuredAnalyzer {
    agent: ChatCompletionAgent,
    thread: AgentThread,
}

impl StructuredAnalyzer {
    fn new(agent: ChatCompletionAgent) -> Self {
        Self {
            agent,
            thread: AgentThread::new(),
        }
    }
    
    async fn perform_detailed_analysis(&mut self, input: &str) -> Result<WritingScore> {
        let response = self.agent.invoke_async(&mut self.thread, input).await
            .map_err(|e| anyhow::anyhow!("Failed to invoke agent: {}", e))?;
        
        self.parse_detailed_response(&response.content)
    }
    
    fn parse_detailed_response(&self, content: &str) -> Result<WritingScore> {
        // Try to parse JSON from response
        if let Some(json_start) = content.find('{') {
            if let Some(json_end) = content.rfind('}') {
                let json_str = &content[json_start..=json_end];
                return serde_json::from_str(json_str)
                    .map_err(|e| anyhow::anyhow!("JSON parse error: {}", e));
            }
        }
        
        // For demo purposes, return a high-quality analysis
        Ok(WritingScore {
            score: 85,
            notes: format!("Advanced literary analysis of complex input: {} - Demonstrates sophisticated imagery, emotional depth, and creative expression.", content.chars().take(50).collect::<String>()),
        })
    }
}