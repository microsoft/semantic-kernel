//! Step 2: Agents with Plugins
//! 
//! This example demonstrates ChatCompletionAgent working with KernelPlugins.
//! It shows:
//! - Agent with plugin integration for function calling
//! - Menu plugin for restaurant information
//! - Widget factory plugin with enum parameters
//! - Prompt functions created dynamically

use anyhow::Result;
use semantic_kernel::{
    Kernel, KernelBuilder, async_trait,
    kernel::{KernelPlugin, KernelFunction},
};
use sk_openai::OpenAIClient;
use sk_agent::{Agent, chat_completion_agent::ChatCompletionAgent, thread::AgentThread};
use std::env;
use std::collections::HashMap;
use serde::{Serialize, Deserialize};

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize environment and logging
    dotenv::dotenv().ok();
    tracing_subscriber::fmt::init();

    println!("🤖 Semantic Kernel Rust - Step 2: Agents with Plugins");
    println!("======================================================\n");

    // Example 1: Agent with menu plugin
    println!("Example 1: Agent with Menu Plugin");
    println!("==================================");
    
    agent_with_menu_plugin().await?;

    // Example 2: Agent with widget factory plugin (enum parameters)
    println!("\nExample 2: Agent with Widget Factory Plugin");
    println!("============================================");
    
    agent_with_widget_plugin().await?;

    // Example 3: Agent with prompt function
    println!("\nExample 3: Agent with Prompt Function");
    println!("=====================================");
    
    agent_with_prompt_function().await?;

    println!("\n✅ Step2 Plugins example completed!");

    Ok(())
}

/// Demonstrate agent with menu plugin for restaurant information
async fn agent_with_menu_plugin() -> Result<()> {
    let mut kernel = create_kernel()?;
    
    // Add menu plugin to kernel
    let menu_plugin = MenuPlugin::new();
    kernel.add_plugin("MenuPlugin", Box::new(menu_plugin));
    
    // Create agent with plugin-enabled kernel
    let agent = ChatCompletionAgent::builder()
        .name("Host")
        .instructions("Answer questions about the menu. Use the available functions to get current menu information.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create agent: {}", e))?;

    let mut thread = AgentThread::new();

    // Interact with menu questions
    let questions = vec![
        "Hello",
        "What is the special soup and its price?",
        "What is the special drink and its price?",
        "Thank you",
    ];

    for question in questions {
        println!("\n👤 User: {}", question);
        
        let response = agent.invoke_async(&mut thread, question).await
            .map_err(|e| anyhow::anyhow!("Failed to invoke agent: {}", e))?;
        
        println!("🏨 Host: {}", response.content);
    }

    Ok(())
}

/// Demonstrate agent with widget factory plugin using enum parameters
async fn agent_with_widget_plugin() -> Result<()> {
    let mut kernel = create_kernel()?;
    
    // Add widget factory plugin to kernel
    let widget_plugin = WidgetFactoryPlugin::new();
    kernel.add_plugin("WidgetFactory", Box::new(widget_plugin));
    
    // Create agent with widget plugin
    let agent = ChatCompletionAgent::builder()
        .name("WidgetMaker")
        .instructions("You help users create widgets. Use the available functions to create widgets with the colors they request.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create agent: {}", e))?;

    let mut thread = AgentThread::new();

    let request = "Create a beautiful red colored widget for me.";
    println!("\n👤 User: {}", request);
    
    let response = agent.invoke_async(&mut thread, request).await
        .map_err(|e| anyhow::anyhow!("Failed to invoke agent: {}", e))?;
    
    println!("🏭 WidgetMaker: {}", response.content);

    Ok(())
}

/// Demonstrate agent with dynamically created prompt function
async fn agent_with_prompt_function() -> Result<()> {
    let mut kernel = create_kernel()?;
    
    // Add vowel counting plugin to kernel
    let vowel_plugin = VowelCountingPlugin::new();
    kernel.add_plugin("VowelCounter", Box::new(vowel_plugin));
    
    // Create agent specialized in vowel analysis
    let agent = ChatCompletionAgent::builder()
        .name("VowelAnalyzer")
        .instructions("Your job is to analyze vowels in user input. Use the available functions to count vowels and present results clearly.")
        .kernel(kernel)
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to create agent: {}", e))?;

    let mut thread = AgentThread::new();

    let text = "Who would know naught of art must learn, act, and then take his ease.";
    println!("\n👤 User: {}", text);
    
    let response = agent.invoke_async(&mut thread, text).await
        .map_err(|e| anyhow::anyhow!("Failed to invoke agent: {}", e))?;
    
    println!("📊 VowelAnalyzer: {}", response.content);

    Ok(())
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

// ===== MENU PLUGIN =====

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Color {
    Red,
    Green,
    Blue,
    Yellow,
    Purple,
    Orange,
    Pink,
    Black,
    White,
    Brown,
}

/// Menu plugin for restaurant information
struct MenuPlugin {
    functions: Vec<Box<dyn KernelFunction>>,
}

impl MenuPlugin {
    fn new() -> Self {
        let functions: Vec<Box<dyn KernelFunction>> = vec![
            Box::new(GetSpecialSoupFunction),
            Box::new(GetSpecialDrinkFunction),
        ];
        
        Self { functions }
    }
}

#[async_trait]
impl KernelPlugin for MenuPlugin {
    fn name(&self) -> &str {
        "MenuPlugin"
    }
    
    fn description(&self) -> &str {
        "Plugin for getting restaurant menu information"
    }
    
    fn functions(&self) -> Vec<&dyn KernelFunction> {
        self.functions.iter().map(|f| f.as_ref()).collect()
    }
}

struct GetSpecialSoupFunction;

#[async_trait]
impl KernelFunction for GetSpecialSoupFunction {
    fn name(&self) -> &str {
        "GetSpecialSoup"
    }
    
    fn description(&self) -> &str {
        "Gets today's special soup and its price"
    }
    
    async fn invoke(
        &self,
        _kernel: &Kernel,
        _arguments: &HashMap<String, String>,
    ) -> semantic_kernel::Result<String> {
        Ok("Today's special soup is Tomato Basil Soup for $8.99".to_string())
    }
    
    fn get_json_schema(&self) -> serde_json::Value {
        serde_json::json!({
            "type": "function",
            "function": {
                "name": self.name(),
                "description": self.description(),
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        })
    }
}

struct GetSpecialDrinkFunction;

#[async_trait]
impl KernelFunction for GetSpecialDrinkFunction {
    fn name(&self) -> &str {
        "GetSpecialDrink"
    }
    
    fn description(&self) -> &str {
        "Gets today's special drink and its price"
    }
    
    async fn invoke(
        &self,
        _kernel: &Kernel,
        _arguments: &HashMap<String, String>,
    ) -> semantic_kernel::Result<String> {
        Ok("Today's special drink is Fresh Lemonade for $4.50".to_string())
    }
    
    fn get_json_schema(&self) -> serde_json::Value {
        serde_json::json!({
            "type": "function",
            "function": {
                "name": self.name(),
                "description": self.description(),
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        })
    }
}

// ===== WIDGET FACTORY PLUGIN =====

/// Widget factory plugin demonstrating enum parameters
struct WidgetFactoryPlugin {
    function: CreateWidgetFunction,
}

impl WidgetFactoryPlugin {
    fn new() -> Self {
        Self {
            function: CreateWidgetFunction,
        }
    }
}

#[async_trait]
impl KernelPlugin for WidgetFactoryPlugin {
    fn name(&self) -> &str {
        "WidgetFactory"
    }
    
    fn description(&self) -> &str {
        "Factory for creating colored widgets"
    }
    
    fn functions(&self) -> Vec<&dyn KernelFunction> {
        vec![&self.function as &dyn KernelFunction]
    }
}

struct CreateWidgetFunction;

#[async_trait]
impl KernelFunction for CreateWidgetFunction {
    fn name(&self) -> &str {
        "CreateWidget"
    }
    
    fn description(&self) -> &str {
        "Creates a widget with the specified color"
    }
    
    async fn invoke(
        &self,
        _kernel: &Kernel,
        arguments: &HashMap<String, String>,
    ) -> semantic_kernel::Result<String> {
        let color = arguments.get("color")
            .unwrap_or(&"blue".to_string())
            .clone();
        
        Ok(format!("✨ Created a beautiful {} widget! It's shiny and perfectly crafted.", color))
    }
    
    fn get_json_schema(&self) -> serde_json::Value {
        serde_json::json!({
            "type": "function",
            "function": {
                "name": self.name(),
                "description": self.description(),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "color": {
                            "type": "string",
                            "description": "The color of the widget to create",
                            "enum": ["red", "green", "blue", "yellow", "purple", "orange", "pink", "black", "white", "brown"]
                        }
                    },
                    "required": ["color"]
                }
            }
        })
    }
}

// ===== VOWEL COUNTING PLUGIN =====

/// Plugin that demonstrates prompt-based functions
struct VowelCountingPlugin {
    function: CountVowelsFunction,
}

impl VowelCountingPlugin {
    fn new() -> Self {
        Self {
            function: CountVowelsFunction,
        }
    }
}

#[async_trait]
impl KernelPlugin for VowelCountingPlugin {
    fn name(&self) -> &str {
        "VowelCounter"
    }
    
    fn description(&self) -> &str {
        "Plugin for analyzing vowels in text"
    }
    
    fn functions(&self) -> Vec<&dyn KernelFunction> {
        vec![&self.function as &dyn KernelFunction]
    }
}

struct CountVowelsFunction;

#[async_trait]
impl KernelFunction for CountVowelsFunction {
    fn name(&self) -> &str {
        "CountVowels"
    }
    
    fn description(&self) -> &str {
        "Counts the number of vowels in the given text"
    }
    
    async fn invoke(
        &self,
        _kernel: &Kernel,
        arguments: &HashMap<String, String>,
    ) -> semantic_kernel::Result<String> {
        let input = arguments.get("input")
            .ok_or("Missing 'input' parameter")?;
        
        let vowels = ['a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U'];
        let mut counts = HashMap::new();
        
        for vowel in &vowels {
            counts.insert(*vowel, 0);
        }
        
        for char in input.chars() {
            if vowels.contains(&char) {
                *counts.entry(char.to_ascii_lowercase()).or_insert(0) += 1;
            }
        }
        
        let total: usize = counts.values().sum();
        
        let mut result = format!("# Vowel Analysis\n\nText: \"{}\"\n\n## Results\n\n| Vowel | Count |\n|-------|-------|\n", input);
        
        for vowel in ['a', 'e', 'i', 'o', 'u'] {
            let count = counts.get(&vowel).unwrap_or(&0);
            result.push_str(&format!("| {} | {} |\n", vowel.to_uppercase(), count));
        }
        
        result.push_str(&format!("\n**Total vowels**: {}", total));
        
        Ok(result)
    }
    
    fn get_json_schema(&self) -> serde_json::Value {
        serde_json::json!({
            "type": "function",
            "function": {
                "name": self.name(),
                "description": self.description(),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input": {
                            "type": "string",
                            "description": "The text to analyze for vowels"
                        }
                    },
                    "required": ["input"]
                }
            }
        })
    }
}