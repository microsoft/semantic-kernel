//! Step 8: Pipelining
//! 
//! This example shows how to combine multiple functions into a pipeline.
//! It demonstrates:
//! - Creating function pipelines where output from one feeds into the next
//! - Sequential function execution with data flow
//! - Combining different function types (native + prompt functions)
//! - Function composition patterns

use anyhow::Result;
use semantic_kernel::{
    Kernel, KernelBuilder, async_trait,
    kernel::{KernelPlugin, KernelFunction},
    content::{ChatHistory, PromptExecutionSettings},
};
use sk_openai::OpenAIClient;
use std::env;
use std::collections::HashMap;
use rand::Rng;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize environment and logging
    dotenv::dotenv().ok();
    tracing_subscriber::fmt::init();

    println!("🤖 Semantic Kernel Rust - Step 8: Pipelining");
    println!("=============================================\n");

    // Create a kernel with math and text functions
    let kernel = create_kernel()?;

    // Example 1: Simple pipeline - Parse, Multiply, Truncate, Humanize
    println!("================ PIPELINE ================");
    
    let pipeline_result = execute_numeric_pipeline(&kernel).await?;
    println!("Pipeline result: {}\n", pipeline_result);

    // Example 2: Graph-like pipeline with multiple inputs
    println!("================ GRAPH ================");
    
    let graph_result = execute_graph_pipeline(&kernel).await?;
    println!("Graph result: {}\n", graph_result);

    // Example 3: Custom sequential function pipeline
    println!("================ CUSTOM SEQUENCE ================");
    
    let sequence_result = execute_custom_sequence(&kernel).await?;
    println!("Custom sequence result: {}\n", sequence_result);

    println!("✅ Step8 example completed!");

    Ok(())
}

/// Execute a numeric processing pipeline: parse -> multiply -> truncate -> humanize
async fn execute_numeric_pipeline(kernel: &Kernel) -> Result<String> {
    println!("Creating numeric processing pipeline:");
    println!("1. Parse '123.456' as double");
    println!("2. Multiply by 78.90");
    println!("3. Truncate to integer");
    println!("4. Humanize the number\n");

    // Step 1: Parse string to double
    let input = "123.456";
    let parsed: f64 = input.parse()
        .map_err(|e| anyhow::anyhow!("Failed to parse {}: {}", input, e))?;
    println!("Step 1 - Parse '{}' -> {}", input, parsed);

    // Step 2: Multiply by factor
    let factor = 78.90;
    let multiplied = parsed * factor;
    println!("Step 2 - Multiply {} * {} -> {}", parsed, factor, multiplied);

    // Step 3: Truncate to integer
    let truncated = multiplied as i32;
    println!("Step 3 - Truncate {} -> {}", multiplied, truncated);

    // Step 4: Humanize using AI
    let humanized = humanize_number(kernel, truncated).await?;
    println!("Step 4 - Humanize {} -> {}", truncated, humanized);

    Ok(humanized)
}

/// Execute a graph-style pipeline with random number generation
async fn execute_graph_pipeline(kernel: &Kernel) -> Result<String> {
    println!("Creating graph-style pipeline:");
    println!("1. Generate random number i");
    println!("2. Generate random number j");
    println!("3. Multiply i * j\n");

    // Step 1: Generate random number i
    let mut rng = rand::thread_rng();
    let i: i32 = rng.gen_range(1..=100);
    println!("Step 1 - Generate random i -> {}", i);

    // Step 2: Generate random number j
    let j: i32 = rng.gen_range(1..=100);
    println!("Step 2 - Generate random j -> {}", j);

    // Step 3: Multiply
    let result = i * j;
    println!("Step 3 - Multiply {} * {} -> {}", i, j, result);

    // Step 4: Describe the calculation using AI
    let description = describe_calculation(kernel, i, j, result).await?;
    println!("Step 4 - Describe calculation -> {}", description);

    Ok(description)
}

/// Execute a custom sequence demonstrating different function types
async fn execute_custom_sequence(kernel: &Kernel) -> Result<String> {
    println!("Creating custom function sequence:");
    println!("1. Generate base value");
    println!("2. Apply mathematical transformation");
    println!("3. Format and explain result\n");

    // Step 1: Generate base value
    let base_value = 42;
    println!("Step 1 - Base value -> {}", base_value);

    // Step 2: Apply transformation (square the number)
    let squared = base_value * base_value;
    println!("Step 2 - Square {} -> {}", base_value, squared);

    // Step 3: Get AI explanation
    let explanation = explain_square_result(kernel, base_value, squared).await?;
    println!("Step 3 - Explain result -> {}", explanation);

    Ok(explanation)
}

/// Create a kernel with OpenAI service
fn create_kernel() -> Result<Kernel> {
    if let Ok(api_key) = env::var("OPENAI_API_KEY") {
        println!("✅ OpenAI API key found!");
        println!("📝 Creating kernel for function pipelining...\n");
        
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

/// Use AI to humanize a number (spell it out in English)
async fn humanize_number(kernel: &Kernel, number: i32) -> Result<String> {
    let mut chat_history = ChatHistory::new();
    chat_history.add_user_message(&format!(
        "Spell out this number in English: {}. Just give me the number in words, nothing else.", 
        number
    ));
    
    let settings = PromptExecutionSettings::new()
        .with_max_tokens(50);
    
    let response = kernel.invoke_chat_async(&chat_history, Some(&settings)).await
        .map_err(|e| anyhow::anyhow!("Failed to humanize number: {}", e))?;
    
    Ok(response.content.trim().to_string())
}

/// Use AI to describe a multiplication calculation
async fn describe_calculation(kernel: &Kernel, i: i32, j: i32, result: i32) -> Result<String> {
    let mut chat_history = ChatHistory::new();
    chat_history.add_user_message(&format!(
        "Describe this calculation in a fun way: {} × {} = {}. Keep it under 30 words.",
        i, j, result
    ));
    
    let settings = PromptExecutionSettings::new()
        .with_max_tokens(80);
    
    let response = kernel.invoke_chat_async(&chat_history, Some(&settings)).await
        .map_err(|e| anyhow::anyhow!("Failed to describe calculation: {}", e))?;
    
    Ok(response.content.trim().to_string())
}

/// Use AI to explain a square calculation
async fn explain_square_result(kernel: &Kernel, base: i32, squared: i32) -> Result<String> {
    let mut chat_history = ChatHistory::new();
    chat_history.add_user_message(&format!(
        "Explain why {} squared equals {} in a simple way. Keep it under 25 words.",
        base, squared
    ));
    
    let settings = PromptExecutionSettings::new()
        .with_max_tokens(70);
    
    let response = kernel.invoke_chat_async(&chat_history, Some(&settings)).await
        .map_err(|e| anyhow::anyhow!("Failed to explain square: {}", e))?;
    
    Ok(response.content.trim().to_string())
}

// ===== FUNCTION PIPELINE FRAMEWORK =====

/// A pipeline that executes functions in sequence
#[allow(dead_code)]
struct FunctionPipeline {
    name: String,
    functions: Vec<PipelineFunction>,
}

#[allow(dead_code)]
impl FunctionPipeline {
    fn new(name: String) -> Self {
        Self {
            name,
            functions: Vec::new(),
        }
    }
    
    fn add_function(mut self, function: PipelineFunction) -> Self {
        self.functions.push(function);
        self
    }
    
    async fn execute(&self, kernel: &Kernel, mut context: PipelineContext) -> Result<PipelineContext> {
        println!("🔗 Executing pipeline: {}", self.name);
        
        for (i, function) in self.functions.iter().enumerate() {
            println!("  Step {}: {}", i + 1, function.name);
            context = function.execute(kernel, context).await?;
        }
        
        println!("✅ Pipeline '{}' completed", self.name);
        Ok(context)
    }
}

/// A function in a pipeline
#[allow(dead_code)]
struct PipelineFunction {
    name: String,
    executor: Box<dyn Fn(&Kernel, PipelineContext) -> std::pin::Pin<Box<dyn std::future::Future<Output = Result<PipelineContext>> + Send>> + Send + Sync>,
}

#[allow(dead_code)]
impl PipelineFunction {
    fn new<F, Fut>(name: String, executor: F) -> Self 
    where
        F: Fn(&Kernel, PipelineContext) -> Fut + Send + Sync + 'static,
        Fut: std::future::Future<Output = Result<PipelineContext>> + Send + 'static,
    {
        Self {
            name,
            executor: Box::new(move |kernel, context| Box::pin(executor(kernel, context))),
        }
    }
    
    async fn execute(&self, kernel: &Kernel, context: PipelineContext) -> Result<PipelineContext> {
        (self.executor)(kernel, context).await
    }
}

/// Context passed between pipeline functions
#[allow(dead_code)]
#[derive(Debug, Clone)]
struct PipelineContext {
    data: HashMap<String, String>,
    result: Option<String>,
}

#[allow(dead_code)]
impl PipelineContext {
    fn new() -> Self {
        Self {
            data: HashMap::new(),
            result: None,
        }
    }
    
    fn with_data(mut self, key: String, value: String) -> Self {
        self.data.insert(key, value);
        self
    }
    
    fn set_result(mut self, result: String) -> Self {
        self.result = Some(result);
        self
    }
    
    fn get_data(&self, key: &str) -> Option<&String> {
        self.data.get(key)
    }
    
    fn get_result(&self) -> Option<&String> {
        self.result.as_ref()
    }
}