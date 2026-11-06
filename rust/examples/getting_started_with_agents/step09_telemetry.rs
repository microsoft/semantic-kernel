//! Step 9: Agent Telemetry and Observability
//! 
//! This example demonstrates comprehensive telemetry and observability for agent systems.
//! It shows:
//! - Structured logging for agent operations
//! - Performance metrics and timing
//! - Error tracking and debugging information
//! - Distributed tracing for multi-agent workflows

use anyhow::Result;
use semantic_kernel::{Kernel, KernelBuilder};
use sk_openai::OpenAIClient;
use sk_agent::{Agent, chat_completion_agent::ChatCompletionAgent, thread::AgentThread};
use std::env;
use std::time::{Instant, Duration};
use tracing::{info, warn, error, debug, span, Level, Instrument};
use tracing_subscriber::{self, FmtSubscriber, EnvFilter};

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
You're laser focused on the goal at hand.
Don't waste time with chit chat.
Consider suggestions when refining an idea.
"#;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize comprehensive telemetry
    init_telemetry();
    
    println!("🤖 Semantic Kernel Rust - Step 9: Agent Telemetry");
    println!("================================================\n");

    // Example 1: Basic agent telemetry
    println!("Example 1: Basic Agent Telemetry");
    println!("===============================");
    
    basic_agent_telemetry().await?;

    // Example 2: Multi-agent workflow telemetry
    println!("\nExample 2: Multi-Agent Workflow Telemetry");
    println!("========================================");
    
    workflow_telemetry().await?;

    // Example 3: Performance metrics and error tracking
    println!("\nExample 3: Performance Metrics & Error Tracking");
    println!("==============================================");
    
    performance_metrics().await?;

    println!("\n✅ Step9 Telemetry example completed!");

    Ok(())
}

/// Initialize comprehensive telemetry system
fn init_telemetry() {
    let subscriber = FmtSubscriber::builder()
        .with_env_filter(EnvFilter::from_default_env().add_directive(Level::INFO.into()))
        .with_target(true)
        .with_thread_ids(true)
        .with_file(true)
        .with_line_number(true)
        .finish();

    tracing::subscriber::set_global_default(subscriber)
        .expect("Failed to set global tracing subscriber");

    info!("🔍 Telemetry system initialized");
}

/// Demonstrate basic agent telemetry with structured logging
async fn basic_agent_telemetry() -> Result<()> {
    let span = span!(Level::INFO, "basic_agent_operations");
    async move {
        info!("🎭 Creating agents with telemetry");
        
        let art_director = create_art_director_with_telemetry().await?;
        let copywriter = create_copywriter_with_telemetry().await?;
        
        info!(
            agent_count = 2,
            agents = ?[art_director.name().unwrap_or("Unknown"), copywriter.name().unwrap_or("Unknown")],
            "Agents created successfully"
        );
        
        let concept = "concept: maps made out of egg cartons.";
        info!(input_concept = %concept, "Processing concept with telemetry");
        
        let mut telemetry_chat = TelemetryAgentChat::new(vec![copywriter, art_director]);
        let result = telemetry_chat.execute_with_telemetry(concept, 4).await?;
        
        info!(
            turns_completed = result.turns,
            success = result.success,
            total_duration_ms = result.total_duration.as_millis(),
            "Agent chat completed with telemetry"
        );
        
        Ok(())
    }.instrument(span).await
}

/// Demonstrate multi-agent workflow telemetry
async fn workflow_telemetry() -> Result<()> {
    let span = span!(Level::INFO, "multi_agent_workflow");
    async move {
        info!("🔄 Starting multi-agent workflow with comprehensive telemetry");
        
        let strategist = create_marketing_strategist_with_telemetry().await?;
        let analyst = create_data_analyst_with_telemetry().await?;
        let coordinator = create_workflow_coordinator().await?;
        
        let agents = vec![strategist, analyst, coordinator];
        info!(workflow_agents = agents.len(), "Workflow agents initialized");
        
        let topics = vec![
            "How can we improve customer retention rates?",
            "What are the key metrics for measuring marketing ROI?",
            "How should we structure our quarterly campaign review?",
        ];
        
        let workflow = WorkflowTelemetryManager::new(agents);
        
        for (i, topic) in topics.iter().enumerate() {
            let topic_span = span!(Level::INFO, "topic_processing", topic_id = i, topic = %topic);
            let _enter = topic_span.enter();
            
            info!(topic_number = i + 1, topic_text = %topic, "Processing workflow topic");
            
            let result = workflow.process_topic_with_telemetry(topic).await?;
            
            info!(
                topic_id = i,
                responses_count = result.responses.len(),
                processing_time_ms = result.processing_time.as_millis(),
                "Topic processing completed"
            );
        }
        
        info!("Multi-agent workflow completed successfully");
        Ok(())
    }.instrument(span).await
}

/// Demonstrate performance metrics and error tracking
async fn performance_metrics() -> Result<()> {
    let span = span!(Level::INFO, "performance_analysis");
    async move {
        info!("📊 Starting performance metrics analysis");
        
        let performance_agent = std::sync::Arc::new(create_performance_agent().await?);
        let metrics_collector = std::sync::Arc::new(PerformanceMetrics::new());
        
        let test_scenarios = vec![
            ("short_prompt", "Hello"),
            ("medium_prompt", "Explain the concept of artificial intelligence in simple terms"),
            ("long_prompt", "Provide a comprehensive analysis of the current state of machine learning, including recent advances in large language models, computer vision, and reinforcement learning. Discuss the implications for various industries and potential future developments."),
        ];
        
        for (scenario_name, prompt) in test_scenarios {
            let scenario_span = span!(Level::INFO, "performance_scenario", scenario = %scenario_name);
            let agent_clone = performance_agent.clone();
            let metrics_clone = metrics_collector.clone();
            async move {
                info!(scenario = %scenario_name, prompt_length = prompt.len(), "Starting performance test");
                
                let start_time = Instant::now();
                
                let result = match agent_clone.invoke_async(&mut AgentThread::new(), prompt).await {
                    Ok(response) => {
                        let duration = start_time.elapsed();
                        let response_length = response.content.len();
                        
                        info!(
                            scenario = %scenario_name,
                            duration_ms = duration.as_millis(),
                            response_length = response_length,
                            tokens_per_second = (response_length as f64 / duration.as_secs_f64()) as u64,
                            "Performance test completed successfully"
                        );
                        
                        metrics_clone.record_success(scenario_name, duration, response_length).await;
                        Ok(())
                    }
                    Err(e) => {
                        let duration = start_time.elapsed();
                        error!(
                            scenario = %scenario_name,
                            duration_ms = duration.as_millis(),
                            error = %e,
                            "Performance test failed"
                        );
                        
                        metrics_clone.record_error(scenario_name, duration, &e.to_string()).await;
                        Err(e)
                    }
                };
                
                // Simulate recovery for demonstration
                if result.is_err() {
                    warn!(scenario = %scenario_name, "Attempting recovery with fallback strategy");
                    // In a real implementation, this might involve retries, circuit breakers, etc.
                }
                
                Ok::<(), anyhow::Error>(())
            }.instrument(scenario_span).await?;
        }
        
        // Generate performance summary
        let summary = metrics_collector.generate_summary().await;
        info!(
            total_requests = summary.total_requests,
            successful_requests = summary.successful_requests,
            failed_requests = summary.failed_requests,
            average_duration_ms = summary.average_duration.as_millis(),
            success_rate = summary.success_rate,
            "Performance analysis completed"
        );
        
        Ok(())
    }.instrument(span).await
}

/// Create an art director agent with telemetry
async fn create_art_director_with_telemetry() -> Result<ChatCompletionAgent> {
    let span = span!(Level::DEBUG, "create_agent", agent_type = "art_director");
    async move {
        debug!("Creating art director agent with telemetry");
        let kernel = create_kernel_with_telemetry()?;
        
        let agent = ChatCompletionAgent::builder()
            .name(REVIEWER_NAME)
            .instructions(REVIEWER_INSTRUCTIONS)
            .kernel(kernel)
            .build()
            .map_err(|e| {
                error!(error = %e, "Failed to create art director agent");
                anyhow::anyhow!("Failed to create art director: {}", e)
            })?;
        
        debug!(agent_name = %agent.name().unwrap_or("Unknown"), "Art director agent created");
        Ok(agent)
    }.instrument(span).await
}

/// Create a copywriter agent with telemetry
async fn create_copywriter_with_telemetry() -> Result<ChatCompletionAgent> {
    let span = span!(Level::DEBUG, "create_agent", agent_type = "copywriter");
    async move {
        debug!("Creating copywriter agent with telemetry");
        let kernel = create_kernel_with_telemetry()?;
        
        let agent = ChatCompletionAgent::builder()
            .name(COPYWRITER_NAME)
            .instructions(COPYWRITER_INSTRUCTIONS)
            .kernel(kernel)
            .build()
            .map_err(|e| {
                error!(error = %e, "Failed to create copywriter agent");
                anyhow::anyhow!("Failed to create copywriter: {}", e)
            })?;
        
        debug!(agent_name = %agent.name().unwrap_or("Unknown"), "Copywriter agent created");
        Ok(agent)
    }.instrument(span).await
}

/// Create a marketing strategist with telemetry
async fn create_marketing_strategist_with_telemetry() -> Result<ChatCompletionAgent> {
    let span = span!(Level::DEBUG, "create_agent", agent_type = "marketing_strategist");
    async move {
        let kernel = create_kernel_with_telemetry()?;
        
        let agent = ChatCompletionAgent::builder()
            .name("MarketingStrategist")
            .instructions("You are a marketing strategist with 15 years of experience. Provide strategic insights, campaign ideas, and market positioning advice. Be concise but thorough.")
            .kernel(kernel)
            .build()
            .map_err(|e| anyhow::anyhow!("Failed to create strategist: {}", e))?;
        
        debug!("Marketing strategist agent created");
        Ok(agent)
    }.instrument(span).await
}

/// Create a data analyst with telemetry
async fn create_data_analyst_with_telemetry() -> Result<ChatCompletionAgent> {
    let span = span!(Level::DEBUG, "create_agent", agent_type = "data_analyst");
    async move {
        let kernel = create_kernel_with_telemetry()?;
        
        let agent = ChatCompletionAgent::builder()
            .name("DataAnalyst")
            .instructions("You are a data analyst specializing in marketing metrics. Provide data-driven insights, suggest KPIs, and analyze performance trends. Focus on actionable recommendations.")
            .kernel(kernel)
            .build()
            .map_err(|e| anyhow::anyhow!("Failed to create analyst: {}", e))?;
        
        debug!("Data analyst agent created");
        Ok(agent)
    }.instrument(span).await
}

/// Create a workflow coordinator with telemetry
async fn create_workflow_coordinator() -> Result<ChatCompletionAgent> {
    let span = span!(Level::DEBUG, "create_agent", agent_type = "workflow_coordinator");
    async move {
        let kernel = create_kernel_with_telemetry()?;
        
        let agent = ChatCompletionAgent::builder()
            .name("WorkflowCoordinator")
            .instructions("You are a workflow coordinator. Synthesize insights from different experts and provide comprehensive recommendations.")
            .kernel(kernel)
            .build()
            .map_err(|e| anyhow::anyhow!("Failed to create coordinator: {}", e))?;
        
        debug!("Workflow coordinator agent created");
        Ok(agent)
    }.instrument(span).await
}

/// Create a performance testing agent
async fn create_performance_agent() -> Result<ChatCompletionAgent> {
    let span = span!(Level::DEBUG, "create_agent", agent_type = "performance_agent");
    async move {
        let kernel = create_kernel_with_telemetry()?;
        
        let agent = ChatCompletionAgent::builder()
            .name("PerformanceAgent")
            .instructions("You are a helpful assistant optimized for performance testing. Provide clear, concise responses.")
            .kernel(kernel)
            .build()
            .map_err(|e| anyhow::anyhow!("Failed to create performance agent: {}", e))?;
        
        debug!("Performance agent created");
        Ok(agent)
    }.instrument(span).await
}

/// Create a kernel with telemetry enabled
fn create_kernel_with_telemetry() -> Result<Kernel> {
    let span = span!(Level::DEBUG, "create_kernel");
    let _enter = span.enter();
    
    if let Ok(api_key) = env::var("OPENAI_API_KEY") {
        debug!("Creating kernel with OpenAI service");
        let client = OpenAIClient::new(api_key)?;
        
        Ok(KernelBuilder::new()
            .add_chat_completion_service(client)
            .build())
    } else {
        warn!("OPENAI_API_KEY not found, using mock responses");
        anyhow::bail!(
            "❌ Please set OPENAI_API_KEY environment variable\n\
            You can get an API key from https://platform.openai.com/api-keys"
        );
    }
}

// ===== TELEMETRY IMPLEMENTATIONS =====

/// Agent chat with comprehensive telemetry
struct TelemetryAgentChat {
    agents: Vec<ChatCompletionAgent>,
    thread: AgentThread,
    current_agent_index: usize,
}

#[derive(Debug)]
struct TelemetryResult {
    turns: usize,
    success: bool,
    total_duration: Duration,
}

impl TelemetryAgentChat {
    fn new(agents: Vec<ChatCompletionAgent>) -> Self {
        info!(agent_count = agents.len(), "TelemetryAgentChat initialized");
        Self {
            agents,
            thread: AgentThread::new(),
            current_agent_index: 0,
        }
    }
    
    async fn execute_with_telemetry(&mut self, initial_message: &str, max_turns: usize) -> Result<TelemetryResult> {
        let _span = span!(Level::INFO, "agent_chat_execution", max_turns = max_turns);
        let start_time = Instant::now();
        let mut turns = 0;
        let mut current_message = initial_message.to_string();
        
        info!(
            initial_message = %initial_message,
            max_turns = max_turns,
            "Starting agent chat execution"
        );
        
        for turn in 0..max_turns {
            let turn_span = span!(Level::INFO, "agent_turn", turn_number = turn + 1);
            let _enter = turn_span.enter();
            
            let agent = &self.agents[self.current_agent_index];
            let agent_name = agent.name().unwrap_or("Unknown");
            
            debug!(
                turn = turn + 1,
                agent = %agent_name,
                message_length = current_message.len(),
                "Starting agent turn"
            );
            
            let turn_start = Instant::now();
            
            let response = agent.invoke_async(&mut self.thread, &current_message).await
                .map_err(|e| {
                    error!(
                        turn = turn + 1,
                        agent = %agent_name,
                        error = %e,
                        "Agent invocation failed"
                    );
                    anyhow::anyhow!("Failed to invoke agent {}: {}", agent_name, e)
                })?;
            
            let turn_duration = turn_start.elapsed();
            
            info!(
                turn = turn + 1,
                agent = %agent_name,
                response_length = response.content.len(),
                turn_duration_ms = turn_duration.as_millis(),
                "Agent turn completed"
            );
            
            self.current_agent_index = (self.current_agent_index + 1) % self.agents.len();
            current_message = response.content;
            turns = turn + 1;
        }
        
        let total_duration = start_time.elapsed();
        
        info!(
            total_turns = turns,
            total_duration_ms = total_duration.as_millis(),
            average_turn_ms = if turns > 0 { total_duration.as_millis() / turns as u128 } else { 0 },
            "Agent chat execution completed"
        );
        
        Ok(TelemetryResult {
            turns,
            success: true,
            total_duration,
        })
    }
}

/// Workflow telemetry manager
struct WorkflowTelemetryManager {
    agents: Vec<ChatCompletionAgent>,
}

#[derive(Debug)]
struct WorkflowResult {
    responses: Vec<String>,
    processing_time: Duration,
}

impl WorkflowTelemetryManager {
    fn new(agents: Vec<ChatCompletionAgent>) -> Self {
        Self { agents }
    }
    
    async fn process_topic_with_telemetry(&self, topic: &str) -> Result<WorkflowResult> {
        let span = span!(Level::INFO, "workflow_topic_processing");
        let _enter = span.enter();
        
        let start_time = Instant::now();
        let mut responses = Vec::new();
        
        for (i, agent) in self.agents.iter().enumerate() {
            let agent_span = span!(Level::INFO, "workflow_agent", agent_index = i);
            let _enter = agent_span.enter();
            
            let agent_name = agent.name().unwrap_or("Unknown");
            debug!(agent = %agent_name, "Processing with workflow agent");
            
            let mut thread = AgentThread::new();
            let response = agent.invoke_async(&mut thread, topic).await
                .map_err(|e| anyhow::anyhow!("Workflow agent {} failed: {}", agent_name, e))?;
            
            responses.push(response.content);
            debug!(agent = %agent_name, "Workflow agent completed");
        }
        
        let processing_time = start_time.elapsed();
        
        Ok(WorkflowResult {
            responses,
            processing_time,
        })
    }
}

/// Performance metrics collection
struct PerformanceMetrics {
    requests: tokio::sync::Mutex<Vec<RequestMetric>>,
}

#[derive(Debug, Clone)]
struct RequestMetric {
    scenario: String,
    duration: Duration,
    success: bool,
    response_length: Option<usize>,
    error: Option<String>,
}

#[derive(Debug)]
struct PerformanceSummary {
    total_requests: usize,
    successful_requests: usize,
    failed_requests: usize,
    average_duration: Duration,
    success_rate: f64,
}

impl PerformanceMetrics {
    fn new() -> Self {
        Self {
            requests: tokio::sync::Mutex::new(Vec::new()),
        }
    }
    
    async fn record_success(&self, scenario: &str, duration: Duration, response_length: usize) {
        let mut requests = self.requests.lock().await;
        requests.push(RequestMetric {
            scenario: scenario.to_string(),
            duration,
            success: true,
            response_length: Some(response_length),
            error: None,
        });
    }
    
    async fn record_error(&self, scenario: &str, duration: Duration, error: &str) {
        let mut requests = self.requests.lock().await;
        requests.push(RequestMetric {
            scenario: scenario.to_string(),
            duration,
            success: false,
            response_length: None,
            error: Some(error.to_string()),
        });
    }
    
    async fn generate_summary(&self) -> PerformanceSummary {
        let requests = self.requests.lock().await;
        let total_requests = requests.len();
        let successful_requests = requests.iter().filter(|r| r.success).count();
        let failed_requests = total_requests - successful_requests;
        
        let total_duration: Duration = requests.iter().map(|r| r.duration).sum();
        let average_duration = if total_requests > 0 {
            total_duration / total_requests as u32
        } else {
            Duration::from_secs(0)
        };
        
        let success_rate = if total_requests > 0 {
            (successful_requests as f64 / total_requests as f64) * 100.0
        } else {
            0.0
        };
        
        PerformanceSummary {
            total_requests,
            successful_requests,
            failed_requests,
            average_duration,
            success_rate,
        }
    }
}