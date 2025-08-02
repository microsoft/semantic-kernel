//! Step 8: Agent Handoff Orchestration
//! 
//! This example demonstrates handoff orchestration where agents intelligently
//! hand off tasks to other agents based on capabilities and context.
//! It shows:
//! - Dynamic agent selection based on task requirements
//! - Customer support triage and routing systems
//! - Capability-based agent handoffs
//! - Multi-agent collaboration with intelligent routing

use anyhow::Result;
use semantic_kernel::{Kernel, KernelBuilder};
use semantic_kernel::kernel::{KernelPlugin, KernelFunction};
use sk_openai::OpenAIClient;
use sk_agent::{Agent, chat_completion_agent::ChatCompletionAgent, thread::AgentThread};
use std::env;
use std::collections::HashMap;
use semantic_kernel::async_trait;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize environment and logging
    dotenv::dotenv().ok();
    tracing_subscriber::fmt::init();

    println!("🤖 Semantic Kernel Rust - Step 8: Agent Handoff Orchestration");
    println!("=============================================================\n");

    // Example 1: Customer support triage system
    println!("Example 1: Customer Support Triage System");
    println!("=========================================");
    
    customer_support_triage().await?;

    // Example 2: Technical issue routing
    println!("\nExample 2: Technical Issue Routing");
    println!("=================================");
    
    technical_issue_routing().await?;

    // Example 3: Multi-domain expert consultation
    println!("\nExample 3: Multi-Domain Expert Consultation");
    println!("==========================================");
    
    expert_consultation_handoff().await?;

    println!("\n✅ Step8 Handoff Orchestration example completed!");

    Ok(())
}

/// Demonstrate customer support triage with intelligent routing
async fn customer_support_triage() -> Result<()> {
    // Create support team agents
    let triage_agent = create_triage_agent().await?;
    let status_agent = create_order_status_agent().await?;
    let return_agent = create_return_agent().await?;
    let refund_agent = create_refund_agent().await?;
    
    println!("🎧 Created customer support team:");
    println!("  - {} (Routes customer inquiries)", triage_agent.name().unwrap_or("Unknown"));
    println!("  - {} (Handles order status)", status_agent.name().unwrap_or("Unknown"));
    println!("  - {} (Processes returns)", return_agent.name().unwrap_or("Unknown"));
    println!("  - {} (Manages refunds)", refund_agent.name().unwrap_or("Unknown"));
    
    let customer_requests = vec![
        "I need to check the status of my order #12345",
        "I want to return a damaged item from my recent purchase",
        "Can I get a refund for my order? The product didn't meet expectations",
        "I have a general question about your shipping policy",
    ];
    
    let orchestrator = SupportOrchestrator::new(triage_agent, vec![status_agent, return_agent, refund_agent]);
    
    for (i, request) in customer_requests.iter().enumerate() {
        println!("\n📞 Customer Request {}: \"{}\"", i + 1, request);
        let result = orchestrator.handle_customer_request(request).await?;
        println!("   Routed to: {}", result.handled_by);
        println!("   Response: {}", result.response.chars().take(100).collect::<String>() + "...");
    }
    
    Ok(())
}

/// Demonstrate technical issue routing based on expertise
async fn technical_issue_routing() -> Result<()> {
    // Create technical support team
    let coordinator = create_tech_coordinator().await?;
    let network_expert = create_network_expert().await?;
    let security_expert = create_security_expert().await?;
    let database_expert = create_database_expert().await?;
    
    println!("🔧 Created technical support team:");
    println!("  - {} (Coordinates technical issues)", coordinator.name().unwrap_or("Unknown"));
    println!("  - {} (Network connectivity)", network_expert.name().unwrap_or("Unknown"));
    println!("  - {} (Security concerns)", security_expert.name().unwrap_or("Unknown"));
    println!("  - {} (Database problems)", database_expert.name().unwrap_or("Unknown"));
    
    let technical_issues = vec![
        "Our application can't connect to the remote database server",
        "We're experiencing intermittent network timeouts in our API calls",
        "Suspicious login attempts detected from multiple IP addresses",
        "Database queries are running extremely slowly since yesterday",
    ];
    
    let tech_orchestrator = TechnicalOrchestrator::new(coordinator, vec![network_expert, security_expert, database_expert]);
    
    for (i, issue) in technical_issues.iter().enumerate() {
        println!("\n🚨 Technical Issue {}: \"{}\"", i + 1, issue);
        let result = tech_orchestrator.route_technical_issue(issue).await?;
        println!("   Expert assigned: {}", result.expert_assigned);
        println!("   Solution: {}", result.solution.chars().take(120).collect::<String>() + "...");
    }
    
    Ok(())
}

/// Demonstrate expert consultation with capability-based handoffs
async fn expert_consultation_handoff() -> Result<()> {
    // Create expert consultation team
    let coordinator = create_consultation_coordinator().await?;
    let legal_expert = create_legal_expert().await?;
    let financial_expert = create_financial_expert().await?;
    let technical_expert = create_technical_consultant().await?;
    
    println!("👥 Created expert consultation team:");
    println!("  - {} (Coordinates consultations)", coordinator.name().unwrap_or("Unknown"));
    println!("  - {} (Legal matters)", legal_expert.name().unwrap_or("Unknown"));
    println!("  - {} (Financial analysis)", financial_expert.name().unwrap_or("Unknown"));
    println!("  - {} (Technical architecture)", technical_expert.name().unwrap_or("Unknown"));
    
    let consultation_requests = vec![
        "We need advice on data privacy regulations for our new EU expansion",
        "What's the ROI analysis for investing in cloud infrastructure migration?",
        "How should we architect a microservices system for high availability?",
    ];
    
    let consultation_orchestrator = ConsultationOrchestrator::new(
        coordinator, 
        vec![legal_expert, financial_expert, technical_expert]
    );
    
    for (i, request) in consultation_requests.iter().enumerate() {
        println!("\n💼 Consultation {}: \"{}\"", i + 1, request);
        let result = consultation_orchestrator.coordinate_consultation(request).await?;
        println!("   Expert consulted: {}", result.expert_consulted);
        println!("   Advice: {}", result.advice.chars().take(150).collect::<String>() + "...");
    }
    
    Ok(())
}

// ===== AGENT CREATION FUNCTIONS =====

/// Create a triage agent for customer support routing
async fn create_triage_agent() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name("TriageAgent")
        .instructions("You are a customer support agent that triages issues. Analyze customer requests and determine which specialist should handle them: OrderStatus, Returns, Refunds, or General.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create triage agent: {}", e))
}

/// Create an order status agent with order checking capabilities
async fn create_order_status_agent() -> Result<ChatCompletionAgent> {
    let mut kernel = create_kernel()?;
    
    // Add order status plugin
    let order_plugin = OrderStatusPlugin::new();
    kernel.add_plugin("OrderStatus", Box::new(order_plugin));
    
    ChatCompletionAgent::builder()
        .name("OrderStatusAgent")
        .instructions("You handle order status requests. Use the available functions to check order status and provide detailed information to customers.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create order status agent: {}", e))
}

/// Create a return processing agent
async fn create_return_agent() -> Result<ChatCompletionAgent> {
    let mut kernel = create_kernel()?;
    
    // Add return processing plugin
    let return_plugin = ReturnProcessingPlugin::new();
    kernel.add_plugin("Returns", Box::new(return_plugin));
    
    ChatCompletionAgent::builder()
        .name("ReturnAgent")
        .instructions("You handle order return requests. Use available functions to process returns and provide return authorization information.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create return agent: {}", e))
}

/// Create a refund processing agent
async fn create_refund_agent() -> Result<ChatCompletionAgent> {
    let mut kernel = create_kernel()?;
    
    // Add refund processing plugin
    let refund_plugin = RefundProcessingPlugin::new();
    kernel.add_plugin("Refunds", Box::new(refund_plugin));
    
    ChatCompletionAgent::builder()
        .name("RefundAgent")
        .instructions("You handle refund requests. Use available functions to process refunds and provide refund status information.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create refund agent: {}", e))
}

/// Create technical coordination agent
async fn create_tech_coordinator() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name("TechCoordinator")
        .instructions("You coordinate technical issues by analyzing problems and routing them to the appropriate expert: network, security, or database specialists.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create tech coordinator: {}", e))
}

/// Create network expert agent
async fn create_network_expert() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name("NetworkExpert")
        .instructions("You are a network connectivity expert. Diagnose and provide solutions for network-related issues including timeouts, connectivity problems, and API communication failures.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create network expert: {}", e))
}

/// Create security expert agent
async fn create_security_expert() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name("SecurityExpert")
        .instructions("You are a cybersecurity expert. Analyze security threats, suspicious activities, and provide security recommendations and incident response guidance.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create security expert: {}", e))
}

/// Create database expert agent
async fn create_database_expert() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name("DatabaseExpert")
        .instructions("You are a database performance expert. Diagnose database issues, optimize queries, and provide solutions for performance and connectivity problems.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create database expert: {}", e))
}

/// Create consultation coordinator
async fn create_consultation_coordinator() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name("ConsultationCoordinator")
        .instructions("You coordinate expert consultations by analyzing requests and routing them to appropriate experts: legal, financial, or technical consultants.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create consultation coordinator: {}", e))
}

/// Create legal expert agent
async fn create_legal_expert() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name("LegalExpert")
        .instructions("You are a legal consultant specializing in business law, regulations, compliance, and data privacy. Provide legal guidance and regulatory advice.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create legal expert: {}", e))
}

/// Create financial expert agent
async fn create_financial_expert() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name("FinancialExpert")
        .instructions("You are a financial analyst and consultant. Provide ROI analysis, investment advice, cost-benefit assessments, and financial planning guidance.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create financial expert: {}", e))
}

/// Create technical consultant agent
async fn create_technical_consultant() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel()?;
    
    ChatCompletionAgent::builder()
        .name("TechnicalConsultant")
        .instructions("You are a technical architecture consultant. Provide guidance on system design, technology choices, scalability, and best practices for software development.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create technical consultant: {}", e))
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

// ===== ORCHESTRATION IMPLEMENTATIONS =====

/// Support orchestrator for customer service routing
struct SupportOrchestrator {
    triage_agent: ChatCompletionAgent,
    specialist_agents: Vec<ChatCompletionAgent>,
}

#[derive(Debug)]
struct SupportResult {
    handled_by: String,
    response: String,
}

impl SupportOrchestrator {
    fn new(triage_agent: ChatCompletionAgent, specialist_agents: Vec<ChatCompletionAgent>) -> Self {
        Self {
            triage_agent,
            specialist_agents,
        }
    }
    
    async fn handle_customer_request(&self, request: &str) -> Result<SupportResult> {
        // First, triage agent determines routing
        let mut triage_thread = AgentThread::new();
        let triage_response = self.triage_agent.invoke_async(&mut triage_thread, request).await
            .map_err(|e| anyhow::anyhow!("Triage failed: {}", e))?;
        
        // Simple routing logic based on keywords (in real implementation, would use triage response)
        let specialist = if request.to_lowercase().contains("status") || request.to_lowercase().contains("order") {
            &self.specialist_agents[0] // OrderStatus
        } else if request.to_lowercase().contains("return") {
            &self.specialist_agents[1] // Returns
        } else if request.to_lowercase().contains("refund") {
            &self.specialist_agents[2] // Refunds
        } else {
            &self.specialist_agents[0] // Default to first specialist
        };
        
        // Route to specialist
        let mut specialist_thread = AgentThread::new();
        let specialist_response = specialist.invoke_async(&mut specialist_thread, request).await
            .map_err(|e| anyhow::anyhow!("Specialist handling failed: {}", e))?;
        
        Ok(SupportResult {
            handled_by: specialist.name().unwrap_or("Unknown").to_string(),
            response: specialist_response.content,
        })
    }
}

/// Technical orchestrator for expert routing
struct TechnicalOrchestrator {
    coordinator: ChatCompletionAgent,
    experts: Vec<ChatCompletionAgent>,
}

#[derive(Debug)]
struct TechnicalResult {
    expert_assigned: String,
    solution: String,
}

impl TechnicalOrchestrator {
    fn new(coordinator: ChatCompletionAgent, experts: Vec<ChatCompletionAgent>) -> Self {
        Self { coordinator, experts }
    }
    
    async fn route_technical_issue(&self, issue: &str) -> Result<TechnicalResult> {
        // Route based on issue content (simplified routing logic)
        let expert = if issue.to_lowercase().contains("network") || issue.to_lowercase().contains("timeout") || issue.to_lowercase().contains("api") {
            &self.experts[0] // Network expert
        } else if issue.to_lowercase().contains("security") || issue.to_lowercase().contains("login") || issue.to_lowercase().contains("suspicious") {
            &self.experts[1] // Security expert
        } else if issue.to_lowercase().contains("database") || issue.to_lowercase().contains("query") || issue.to_lowercase().contains("slow") {
            &self.experts[2] // Database expert
        } else {
            &self.experts[0] // Default to network expert
        };
        
        let mut expert_thread = AgentThread::new();
        let expert_response = expert.invoke_async(&mut expert_thread, issue).await
            .map_err(|e| anyhow::anyhow!("Expert consultation failed: {}", e))?;
        
        Ok(TechnicalResult {
            expert_assigned: expert.name().unwrap_or("Unknown").to_string(),
            solution: expert_response.content,
        })
    }
}

/// Consultation orchestrator for expert advice
struct ConsultationOrchestrator {
    coordinator: ChatCompletionAgent,
    experts: Vec<ChatCompletionAgent>,
}

#[derive(Debug)]
struct ConsultationResult {
    expert_consulted: String,
    advice: String,
}

impl ConsultationOrchestrator {
    fn new(coordinator: ChatCompletionAgent, experts: Vec<ChatCompletionAgent>) -> Self {
        Self { coordinator, experts }
    }
    
    async fn coordinate_consultation(&self, request: &str) -> Result<ConsultationResult> {
        // Route based on consultation type
        let expert = if request.to_lowercase().contains("legal") || request.to_lowercase().contains("regulation") || request.to_lowercase().contains("privacy") {
            &self.experts[0] // Legal expert
        } else if request.to_lowercase().contains("roi") || request.to_lowercase().contains("financial") || request.to_lowercase().contains("investment") {
            &self.experts[1] // Financial expert
        } else if request.to_lowercase().contains("architect") || request.to_lowercase().contains("technical") || request.to_lowercase().contains("microservices") {
            &self.experts[2] // Technical expert
        } else {
            &self.experts[0] // Default to first expert
        };
        
        let mut expert_thread = AgentThread::new();
        let expert_response = expert.invoke_async(&mut expert_thread, request).await
            .map_err(|e| anyhow::anyhow!("Expert consultation failed: {}", e))?;
        
        Ok(ConsultationResult {
            expert_consulted: expert.name().unwrap_or("Unknown").to_string(),
            advice: expert_response.content,
        })
    }
}

// ===== PLUGIN IMPLEMENTATIONS =====

/// Order status plugin for checking orders
struct OrderStatusPlugin {
    function: CheckOrderStatusFunction,
}

impl OrderStatusPlugin {
    fn new() -> Self {
        Self {
            function: CheckOrderStatusFunction,
        }
    }
}

#[async_trait]
impl KernelPlugin for OrderStatusPlugin {
    fn name(&self) -> &str {
        "OrderStatus"
    }
    
    fn description(&self) -> &str {
        "Plugin for checking order status"
    }
    
    fn functions(&self) -> Vec<&dyn KernelFunction> {
        vec![&self.function as &dyn KernelFunction]
    }
}

struct CheckOrderStatusFunction;

#[async_trait]
impl KernelFunction for CheckOrderStatusFunction {
    fn name(&self) -> &str {
        "CheckOrderStatus"
    }
    
    fn description(&self) -> &str {
        "Check the status of an order by order ID"
    }
    
    async fn invoke(&self, _kernel: &Kernel, arguments: &HashMap<String, String>) -> semantic_kernel::Result<String> {
        let default_order = "unknown".to_string();
        let order_id = arguments.get("orderId").unwrap_or(&default_order);
        Ok(format!("Order {} is shipped and will arrive in 2-3 days.", order_id))
    }
}

/// Return processing plugin
struct ReturnProcessingPlugin {
    function: ProcessReturnFunction,
}

impl ReturnProcessingPlugin {
    fn new() -> Self {
        Self {
            function: ProcessReturnFunction,
        }
    }
}

#[async_trait]
impl KernelPlugin for ReturnProcessingPlugin {
    fn name(&self) -> &str {
        "Returns"
    }
    
    fn description(&self) -> &str {
        "Plugin for processing product returns"
    }
    
    fn functions(&self) -> Vec<&dyn KernelFunction> {
        vec![&self.function as &dyn KernelFunction]
    }
}

struct ProcessReturnFunction;

#[async_trait]
impl KernelFunction for ProcessReturnFunction {
    fn name(&self) -> &str {
        "ProcessReturn"
    }
    
    fn description(&self) -> &str {
        "Process a product return request"
    }
    
    async fn invoke(&self, _kernel: &Kernel, arguments: &HashMap<String, String>) -> semantic_kernel::Result<String> {
        let default_order = "unknown".to_string();
        let default_reason = "unspecified".to_string();
        let order_id = arguments.get("orderId").unwrap_or(&default_order);
        let reason = arguments.get("reason").unwrap_or(&default_reason);
        Ok(format!("Return for order {} has been processed successfully. Reason: {}", order_id, reason))
    }
}

/// Refund processing plugin
struct RefundProcessingPlugin {
    function: ProcessRefundFunction,
}

impl RefundProcessingPlugin {
    fn new() -> Self {
        Self {
            function: ProcessRefundFunction,
        }
    }
}

#[async_trait]
impl KernelPlugin for RefundProcessingPlugin {
    fn name(&self) -> &str {
        "Refunds"
    }
    
    fn description(&self) -> &str {
        "Plugin for processing refunds"
    }
    
    fn functions(&self) -> Vec<&dyn KernelFunction> {
        vec![&self.function as &dyn KernelFunction]
    }
}

struct ProcessRefundFunction;

#[async_trait]
impl KernelFunction for ProcessRefundFunction {
    fn name(&self) -> &str {
        "ProcessRefund"
    }
    
    fn description(&self) -> &str {
        "Process a refund request"
    }
    
    async fn invoke(&self, _kernel: &Kernel, arguments: &HashMap<String, String>) -> semantic_kernel::Result<String> {
        let default_order = "unknown".to_string();
        let default_amount = "unknown".to_string();
        let order_id = arguments.get("orderId").unwrap_or(&default_order);
        let amount = arguments.get("amount").unwrap_or(&default_amount);
        Ok(format!("Refund for order {} has been processed successfully. Amount: ${}", order_id, amount))
    }
}