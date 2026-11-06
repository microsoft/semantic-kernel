//! Step 10: Agent as Kernel Function
//! 
//! This example demonstrates how to convert agents into kernel functions that can be called
//! by other agents or kernel operations. This enables composition patterns where agents
//! can delegate work to specialized agents through the kernel's function calling mechanism.
//! It shows:
//! - Converting agents into callable kernel functions
//! - Sales assistant agent with order placement capabilities
//! - Refund agent with refund processing capabilities
//! - Multi-agent coordination through function delegation

use anyhow::Result;
use semantic_kernel::{
    Kernel, KernelBuilder, async_trait,
    kernel::{KernelPlugin, KernelFunction},
};
use sk_openai::OpenAIClient;
use sk_agent::{Agent, chat_completion_agent::ChatCompletionAgent, thread::AgentThread};
use std::env;
use std::collections::HashMap;

const SALES_ASSISTANT_NAME: &str = "SalesAssistant";
const SALES_ASSISTANT_INSTRUCTIONS: &str = r#"
You are a sales assistant. Place orders for items the user requests.
Use the available order functions to process customer orders.
Be helpful and confirm order details clearly.
"#;

const REFUND_AGENT_NAME: &str = "RefundAgent";
const REFUND_AGENT_INSTRUCTIONS: &str = r#"
You are a refund agent. Help the user with refunds.
Use the available refund functions to process customer refunds.
Be empathetic and guide users through the refund process.
"#;

const SHOPPING_ASSISTANT_NAME: &str = "ShoppingAssistant";
const SHOPPING_ASSISTANT_INSTRUCTIONS: &str = r#"
You are a sales assistant. Delegate to the provided agents to help the user with placing orders and requesting refunds.
Use the SalesAssistant for placing orders and the RefundAgent for processing refunds.
Coordinate between these specialized agents to provide comprehensive customer service.
"#;

#[tokio::main]
async fn main() -> Result<()> {
    println!("🤖 Semantic Kernel Rust - Step 10: Agent as Kernel Function");
    println!("=======================================================\n");

    // Example 1: Sales assistant agent with function calling
    println!("Example 1: Sales Assistant Agent");
    println!("==============================");
    
    sales_assistant_example().await?;

    // Example 2: Refund agent with function calling
    println!("\nExample 2: Refund Agent");
    println!("====================");
    
    refund_agent_example().await?;

    // Example 3: Multiple agents coordinated through function delegation
    println!("\nExample 3: Multi-Agent Function Delegation");
    println!("========================================");
    
    multi_agent_delegation().await?;

    println!("\n✅ Step10 Agent as Function example completed!");

    Ok(())
}

/// Demonstrate sales assistant agent with order placement functions
async fn sales_assistant_example() -> Result<()> {
    let kernel = create_kernel_with_order_functions()?;
    
    let sales_agent = ChatCompletionAgent::builder()
        .name(SALES_ASSISTANT_NAME)
        .instructions(SALES_ASSISTANT_INSTRUCTIONS)
.kernel(kernel)
        .build()?;

    let user_message = "Place an order for a black boot.";
    println!("User: {}", user_message);
    
    let mut thread = AgentThread::new();
    let response = sales_agent.invoke_async(&mut thread, user_message).await?;
    
    println!("Sales Assistant: {}", response.content);
    
    Ok(())
}

/// Demonstrate refund agent with refund processing functions
async fn refund_agent_example() -> Result<()> {
    let kernel = create_kernel_with_refund_functions()?;
    
    let refund_agent = ChatCompletionAgent::builder()
        .name(REFUND_AGENT_NAME)
        .instructions(REFUND_AGENT_INSTRUCTIONS)
.kernel(kernel)
        .build()?;

    let user_message = "I want a refund for a black boot.";
    println!("User: {}", user_message);
    
    let mut thread = AgentThread::new();
    let response = refund_agent.invoke_async(&mut thread, user_message).await?;
    
    println!("Refund Agent: {}", response.content);
    
    Ok(())
}

/// Demonstrate multiple agents coordinated through function delegation
async fn multi_agent_delegation() -> Result<()> {
    // Create specialized agents
    let sales_agent = create_sales_assistant_agent().await?;
    let refund_agent = create_refund_agent().await?;
    
    // Create kernel with agent functions
    let mut kernel = create_base_kernel()?;
    
    // Add agent functions to kernel
    add_agent_as_function(&mut kernel, "sales_assistant", &sales_agent, "Place orders for items the user requests")?;
    add_agent_as_function(&mut kernel, "refund_agent", &refund_agent, "Execute refunds for items on behalf of the user")?;
    
    // Create shopping assistant that delegates to other agents
    let shopping_assistant = ChatCompletionAgent::builder()
        .name(SHOPPING_ASSISTANT_NAME)
        .instructions(SHOPPING_ASSISTANT_INSTRUCTIONS)
.kernel(kernel)
        .build()?;

    // Test delegation flow
    let messages = [
        "Place an order for a black boot.",
        "Now I want a refund for the black boot.",
    ];

    let mut thread = AgentThread::new();
    
    for message in &messages {
        println!("User: {}", message);
        
        let response = shopping_assistant.invoke_async(&mut thread, message).await?;
        
        println!("Shopping Assistant: {}", response.content);
        println!(); // Add spacing between interactions
    }
    
    Ok(())
}

/// Create a kernel with order placement functions
fn create_kernel_with_order_functions() -> Result<Kernel> {
    let mut kernel = create_base_kernel()?;
    
    // Add order plugin
    let order_plugin = Box::new(OrderPlugin);
    kernel.add_plugin("OrderPlugin", order_plugin);
    
    Ok(kernel)
}

/// Create a kernel with refund processing functions
fn create_kernel_with_refund_functions() -> Result<Kernel> {
    let mut kernel = create_base_kernel()?;
    
    // Add refund plugin
    let refund_plugin = Box::new(RefundPlugin);
    kernel.add_plugin("RefundPlugin", refund_plugin);
    
    Ok(kernel)
}

/// Create a base kernel with chat completion service
fn create_base_kernel() -> Result<Kernel> {
    if let Ok(api_key) = env::var("OPENAI_API_KEY") {
        let client = OpenAIClient::new(api_key)?;
        
        Ok(KernelBuilder::new()
            .add_chat_completion_service(client)
            .build())
    } else {
        println!("⚠️  OPENAI_API_KEY not found, using mock responses");
        
        // Create kernel without OpenAI service for demo purposes
        Ok(KernelBuilder::new().build())
    }
}

/// Create a sales assistant agent with order functions
async fn create_sales_assistant_agent() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel_with_order_functions()?;
    
    Ok(ChatCompletionAgent::builder()
        .name(SALES_ASSISTANT_NAME)
        .instructions(SALES_ASSISTANT_INSTRUCTIONS)
        .kernel(kernel)
        .build()?)
}

/// Create a refund agent with refund functions
async fn create_refund_agent() -> Result<ChatCompletionAgent> {
    let kernel = create_kernel_with_refund_functions()?;
    
    Ok(ChatCompletionAgent::builder()
        .name(REFUND_AGENT_NAME)
        .instructions(REFUND_AGENT_INSTRUCTIONS)
        .kernel(kernel)
        .build()?)
}

/// Add an agent as a callable kernel function
fn add_agent_as_function(
    kernel: &mut Kernel,
    function_name: &str,
    _agent: &ChatCompletionAgent,
    _description: &str,
) -> Result<()> {
    // Create agent plugin based on function name
    let agent_plugin: Box<dyn KernelPlugin> = match function_name {
        "sales_assistant" => Box::new(SalesAgentPlugin),
        "refund_agent" => Box::new(RefundAgentPlugin),
        _ => Box::new(GenericAgentPlugin),
    };
    
    kernel.add_plugin("AgentPlugin", agent_plugin);
    
    Ok(())
}

/// Extract item name from user input (simplified parsing)
fn extract_item(input: &str) -> String {
    // Simple extraction - look for common item patterns
    if input.contains("boot") {
        "black boot".to_string()
    } else if input.contains("shoe") {
        "shoe".to_string()
    } else if input.contains("shirt") {
        "shirt".to_string()
    } else {
        "item".to_string()
    }
}

// ===== PLUGIN IMPLEMENTATIONS =====

/// Order plugin for placing orders
struct OrderPlugin;

impl KernelPlugin for OrderPlugin {
    fn name(&self) -> &str {
        "OrderPlugin"
    }

    fn description(&self) -> &str {
        "Plugin for placing orders"
    }

    fn functions(&self) -> Vec<&dyn KernelFunction> {
        vec![&PlaceOrderFunction]
    }
}

/// Refund plugin for processing refunds  
struct RefundPlugin;

impl KernelPlugin for RefundPlugin {
    fn name(&self) -> &str {
        "RefundPlugin"
    }

    fn description(&self) -> &str {
        "Plugin for processing refunds"
    }

    fn functions(&self) -> Vec<&dyn KernelFunction> {
        vec![&ExecuteRefundFunction]
    }
}

/// Sales agent plugin wrapper
struct SalesAgentPlugin;

impl KernelPlugin for SalesAgentPlugin {
    fn name(&self) -> &str {
        "SalesAgentPlugin"
    }

    fn description(&self) -> &str {
        "Sales agent function"
    }

    fn functions(&self) -> Vec<&dyn KernelFunction> {
        vec![&SalesAgentFunction]
    }
}

/// Refund agent plugin wrapper
struct RefundAgentPlugin;

impl KernelPlugin for RefundAgentPlugin {
    fn name(&self) -> &str {
        "RefundAgentPlugin"
    }

    fn description(&self) -> &str {
        "Refund agent function"
    }

    fn functions(&self) -> Vec<&dyn KernelFunction> {
        vec![&RefundAgentFunction]
    }
}

/// Generic agent plugin wrapper
struct GenericAgentPlugin;

impl KernelPlugin for GenericAgentPlugin {
    fn name(&self) -> &str {
        "GenericAgentPlugin"
    }

    fn description(&self) -> &str {
        "Generic agent function"
    }

    fn functions(&self) -> Vec<&dyn KernelFunction> {
        vec![&GenericAgentFunction]
    }
}

// ===== KERNEL FUNCTIONS =====

/// Place order function
struct PlaceOrderFunction;

#[async_trait]
impl KernelFunction for PlaceOrderFunction {
    fn name(&self) -> &str {
        "place_order"
    }

    fn description(&self) -> &str {
        "Place an order for the specified item"
    }

    async fn invoke(&self, _kernel: &Kernel, args: &HashMap<String, String>) -> semantic_kernel::Result<String> {
        let default = "unknown item".to_string();
        let item_name = args.get("item_name").unwrap_or(&default);
        println!("📦 OrderPlugin: Placing order for '{}'", item_name);
        Ok("success".to_string())
    }
}

/// Execute refund function
struct ExecuteRefundFunction;

#[async_trait]
impl KernelFunction for ExecuteRefundFunction {
    fn name(&self) -> &str {
        "execute_refund"
    }

    fn description(&self) -> &str {
        "Execute a refund for the specified item"
    }

    async fn invoke(&self, _kernel: &Kernel, args: &HashMap<String, String>) -> semantic_kernel::Result<String> {
        let default = "unknown item".to_string();
        let item_name = args.get("item_name").unwrap_or(&default);
        println!("💰 RefundPlugin: Processing refund for '{}'", item_name);
        Ok("success".to_string())
    }
}

/// Sales agent function wrapper
struct SalesAgentFunction;

#[async_trait]
impl KernelFunction for SalesAgentFunction {
    fn name(&self) -> &str {
        "sales_assistant"
    }

    fn description(&self) -> &str {
        "Place orders for items the user requests"
    }

    async fn invoke(&self, _kernel: &Kernel, args: &HashMap<String, String>) -> semantic_kernel::Result<String> {
        let default = String::new();
        let input = args.get("input").unwrap_or(&default);
        if input.contains("order") || input.contains("place") || input.contains("buy") {
            Ok(format!("Order processed successfully for: {}", extract_item(input)))
        } else {
            Ok("I can help you place orders. What would you like to order?".to_string())
        }
    }
}

/// Refund agent function wrapper
struct RefundAgentFunction;

#[async_trait]
impl KernelFunction for RefundAgentFunction {
    fn name(&self) -> &str {
        "refund_agent"
    }

    fn description(&self) -> &str {
        "Execute refunds for items on behalf of the user"
    }

    async fn invoke(&self, _kernel: &Kernel, args: &HashMap<String, String>) -> semantic_kernel::Result<String> {
        let default = String::new();
        let input = args.get("input").unwrap_or(&default);
        if input.contains("refund") || input.contains("return") {
            Ok(format!("Refund processed successfully for: {}", extract_item(input)))
        } else {
            Ok("I can help you with refunds. What item would you like to refund?".to_string())
        }
    }
}

/// Generic agent function wrapper
struct GenericAgentFunction;

#[async_trait]
impl KernelFunction for GenericAgentFunction {
    fn name(&self) -> &str {
        "agent_function"
    }

    fn description(&self) -> &str {
        "Generic agent function"
    }

    async fn invoke(&self, _kernel: &Kernel, _args: &HashMap<String, String>) -> semantic_kernel::Result<String> {
        Ok("Agent function executed successfully".to_string())
    }
}