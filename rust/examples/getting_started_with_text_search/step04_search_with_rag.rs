//! Step 4: Search with RAG
//! 
//! This example demonstrates how to use text search for Retrieval Augmented Generation (RAG).
//! It shows:
//! - Creating search plugins for grounding LLM responses
//! - Using search results as context for prompts
//! - Including citations in generated responses
//! - Filtering search results by domain
//! - Processing full web page content for comprehensive RAG

use anyhow::Result;
use semantic_kernel::{Kernel, KernelBuilder, async_trait};
use semantic_kernel::kernel::{KernelPlugin, KernelFunction};
use sk_openai::OpenAIClient;
use std::env;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

const QUERY_SEMANTIC_KERNEL: &str = "What is the Semantic Kernel?";
const QUERY_RUST_FEATURES: &str = "What are the key features of Rust programming language?";

#[derive(Debug, Clone, Serialize, Deserialize)]
struct SearchResult {
    name: String,
    value: String,
    link: String,
    snippet: Option<String>,
    date_last_crawled: Option<String>,
}

#[derive(Debug, Clone)]
struct SearchService {
    search_type: String,
}

impl SearchService {
    fn new(search_type: &str) -> Self {
        Self {
            search_type: search_type.to_string(),
        }
    }

    async fn search(&self, query: &str, filter: Option<&str>) -> Result<Vec<SearchResult>> {
        // Mock search implementation
        let results = match self.search_type.as_str() {
            "bing" => self.mock_bing_search(query, filter).await?,
            "google" => self.mock_google_search(query, filter).await?,
            _ => vec![],
        };
        Ok(results)
    }

    async fn search_with_full_content(&self, query: &str, filter: Option<&str>) -> Result<Vec<SearchResult>> {
        // Mock search with full page content
        let mut results = self.search(query, filter).await?;
        
        // Simulate fetching full page content
        for result in &mut results {
            result.value = format!(
                "{}\n\n[Full Content]: This would be the complete text content of the web page at {}. \
                It contains detailed information about the topic, providing comprehensive context for RAG.",
                result.snippet.as_ref().unwrap_or(&result.value),
                result.link
            );
        }
        
        Ok(results)
    }

    async fn mock_bing_search(&self, query: &str, filter: Option<&str>) -> Result<Vec<SearchResult>> {
        let mut results = vec![];
        
        if query.contains("Semantic Kernel") {
            results.push(SearchResult {
                name: "Semantic Kernel Overview - Microsoft Learn".to_string(),
                value: "Semantic Kernel is an SDK that integrates Large Language Models...".to_string(),
                link: "https://learn.microsoft.com/semantic-kernel".to_string(),
                snippet: Some("Semantic Kernel is an SDK that integrates Large Language Models (LLMs) like OpenAI, Azure OpenAI, and Hugging Face with conventional programming languages like C#, Python, and Java.".to_string()),
                date_last_crawled: Some("2024-12-01T10:30:00Z".to_string()),
            });
            
            results.push(SearchResult {
                name: "Getting Started with Semantic Kernel".to_string(),
                value: "Learn how to build AI applications with Semantic Kernel...".to_string(),
                link: "https://devblogs.microsoft.com/semantic-kernel/getting-started".to_string(),
                snippet: Some("This guide walks through creating your first AI application using Semantic Kernel, including agents, plugins, and function calling.".to_string()),
                date_last_crawled: Some("2024-11-28T14:15:00Z".to_string()),
            });
        }
        
        // Apply filter if specified
        if let Some(site_filter) = filter {
            results.retain(|r| r.link.contains(site_filter));
        }
        
        Ok(results)
    }

    async fn mock_google_search(&self, query: &str, _filter: Option<&str>) -> Result<Vec<SearchResult>> {
        let mut results = vec![];
        
        if query.contains("Rust") {
            results.push(SearchResult {
                name: "The Rust Programming Language".to_string(),
                value: "Rust is a multi-paradigm programming language...".to_string(),
                link: "https://www.rust-lang.org/".to_string(),
                snippet: Some("Rust is a multi-paradigm programming language designed for performance and safety, especially safe concurrency.".to_string()),
                date_last_crawled: Some("2024-12-02T08:45:00Z".to_string()),
            });
            
            results.push(SearchResult {
                name: "Why Rust? - The Book".to_string(),
                value: "Rust's key features include zero-cost abstractions...".to_string(),
                link: "https://doc.rust-lang.org/book/ch00-00-introduction.html".to_string(),
                snippet: Some("Rust provides memory safety without garbage collection, fearless concurrency, and zero-cost abstractions.".to_string()),
                date_last_crawled: Some("2024-11-30T16:20:00Z".to_string()),
            });
        }
        
        Ok(results)
    }
}

/// Search kernel function that can be called from prompts
struct SearchKernelFunction {
    service: SearchService,
}

impl SearchKernelFunction {
    fn new(service: SearchService) -> Self {
        Self { service }
    }
}

#[async_trait]
impl KernelFunction for SearchKernelFunction {
    fn name(&self) -> &str {
        "Search"
    }

    fn description(&self) -> &str {
        "Search for information using web search"
    }

    async fn invoke(&self, _kernel: &Kernel, arguments: &HashMap<String, String>) -> semantic_kernel::Result<String> {
        let query = arguments.get("query").cloned().unwrap_or_default();
        let filter = arguments.get("filter").map(|s| s.as_str());
        
        let results = self.service.search(&query, filter).await
            .map_err(|e| e.to_string())
            .map_err(|s| Box::<dyn std::error::Error + Send + Sync>::from(s))?;
        
        // Format results as context
        let context = results.iter()
            .map(|r| format!("Title: {}\nContent: {}\nSource: {}", r.name, r.value, r.link))
            .collect::<Vec<_>>()
            .join("\n\n---\n\n");
        
        Ok(context)
    }
}

/// Citations kernel function
struct CitationsKernelFunction {
    service: SearchService,
}

impl CitationsKernelFunction {
    fn new(service: SearchService) -> Self {
        Self { service }
    }
}

#[async_trait]
impl KernelFunction for CitationsKernelFunction {
    fn name(&self) -> &str {
        "SearchWithCitations"
    }

    fn description(&self) -> &str {
        "Search and format results with citations"
    }

    async fn invoke(&self, _kernel: &Kernel, arguments: &HashMap<String, String>) -> semantic_kernel::Result<String> {
        let query = arguments.get("query").cloned().unwrap_or_default();
        let filter = arguments.get("filter").map(|s| s.as_str());
        
        let results = self.service.search(&query, filter).await
            .map_err(|e| e.to_string())
            .map_err(|s| Box::<dyn std::error::Error + Send + Sync>::from(s))?;
        
        // Format results with citation markers
        let mut context = String::new();
        for (i, r) in results.iter().enumerate() {
            context.push_str(&format!(
                "[{}] Title: {}\nContent: {}\nSource: {}\nLast Updated: {}\n\n",
                i + 1,
                r.name,
                r.snippet.as_ref().unwrap_or(&r.value),
                r.link,
                r.date_last_crawled.as_ref().unwrap_or(&"Unknown".to_string())
            ));
        }
        
        Ok(context)
    }
}

/// Plugin containing search functions
struct SearchPlugin {
    functions: Vec<Box<dyn KernelFunction>>,
}

impl SearchPlugin {
    fn new_with_search(search_type: &str) -> Self {
        let service = SearchService::new(search_type);
        let search_function = Box::new(SearchKernelFunction::new(service));
        Self {
            functions: vec![search_function],
        }
    }

    fn new_with_citations(search_type: &str) -> Self {
        let service = SearchService::new(search_type);
        let citations_function = Box::new(CitationsKernelFunction::new(service));
        Self {
            functions: vec![citations_function],
        }
    }
}

#[async_trait]
impl KernelPlugin for SearchPlugin {
    fn name(&self) -> &str {
        "SearchPlugin"
    }

    fn description(&self) -> &str {
        "Plugin for web search functionality"
    }

    fn functions(&self) -> Vec<&dyn KernelFunction> {
        self.functions.iter().map(|f| f.as_ref()).collect()
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    println!("🤖 Semantic Kernel Rust - Step 4: Search with RAG");
    println!("=================================================\n");

    // Example 1: Basic RAG with search plugin
    println!("Example 1: Basic RAG with Search Plugin");
    println!("======================================");
    
    basic_rag_example().await?;

    // Example 2: RAG with citations
    println!("\nExample 2: RAG with Citations");
    println!("=============================");
    
    rag_with_citations_example().await?;

    // Example 3: Domain-filtered RAG
    println!("\nExample 3: Domain-Filtered RAG");
    println!("==============================");
    
    domain_filtered_rag_example().await?;

    // Example 4: RAG with full page content
    println!("\nExample 4: RAG with Full Page Content");
    println!("====================================");
    
    full_content_rag_example().await?;

    println!("\n✅ Step04 Search with RAG example completed!");

    Ok(())
}

/// Demonstrate basic RAG with search plugin
async fn basic_rag_example() -> Result<()> {
    let mut kernel = create_kernel_with_search_plugin("bing").await?;
    
    // Note: In real implementation, we would use template processing
    // For now, we'll demonstrate the concept with mock search
    println!("🔍 Query: {}", QUERY_SEMANTIC_KERNEL);
    
    // Manually invoke search function
    let search_plugin = SearchService::new("bing");
    let results = search_plugin.search(QUERY_SEMANTIC_KERNEL, None).await?;
    
    if !results.is_empty() {
        println!("\n📊 Search Results Found:");
        for result in &results {
            println!("- {}: {}", result.name, result.snippet.as_ref().unwrap_or(&result.value));
        }
    }
    
    // Build context from search results
    let context = results.iter()
        .map(|r| format!("{}: {}", r.name, r.snippet.as_ref().unwrap_or(&r.value)))
        .collect::<Vec<_>>()
        .join("\n");
    
    let prompt = format!(
        "Based on the following search results:\n{}\n\nAnswer the question: {}",
        context, QUERY_SEMANTIC_KERNEL
    );
    
    if env::var("OPENAI_API_KEY").is_ok() {
        let response = kernel.invoke_prompt_async(&prompt).await
            .map_err(|e| anyhow::anyhow!("Failed to invoke prompt: {}", e))?;
        println!("\n📝 Response:\n{}", response);
    } else {
        // Mock response for demonstration
        println!("\n⚠️  OPENAI_API_KEY not found, showing mock response");
        println!("\n📝 Mock Response:");
        println!("Based on the search results, Semantic Kernel is an SDK that integrates Large Language Models (LLMs) like OpenAI, Azure OpenAI, and Hugging Face with conventional programming languages. It enables developers to build AI applications by combining AI models with existing code, supporting languages like C#, Python, and Java.");
    }
    
    Ok(())
}

/// Demonstrate RAG with citations
async fn rag_with_citations_example() -> Result<()> {
    let mut kernel = create_kernel_with_citations_plugin("google").await?;
    
    println!("🔍 Query: {}", QUERY_RUST_FEATURES);
    
    // Manually invoke citations function
    let search_plugin = SearchService::new("google");
    let results = search_plugin.search(QUERY_RUST_FEATURES, None).await?;
    
    // Format with citations
    let mut citations = String::new();
    for (i, result) in results.iter().enumerate() {
        citations.push_str(&format!(
            "[{}] {}: {}\n",
            i + 1,
            result.name,
            result.snippet.as_ref().unwrap_or(&result.value)
        ));
    }
    
    println!("\n📊 Search Results with Citations:");
    println!("{}", citations);
    
    if env::var("OPENAI_API_KEY").is_ok() {
        let prompt = format!(
            "Based on the following search results:\n{}\n\nAnswer the question '{}' and include citations [1], [2], etc. where relevant.",
            citations, QUERY_RUST_FEATURES
        );
        let response = kernel.invoke_prompt_async(&prompt).await
            .map_err(|e| anyhow::anyhow!("Failed to invoke prompt: {}", e))?;
        println!("\n📝 Response with Citations:\n{}", response);
    } else {
        // Mock response for demonstration
        println!("\n📝 Mock Response with Citations:");
        println!("Based on the search results, Rust has several key features [1]:");
        println!("- Memory safety without garbage collection [1]");
        println!("- Fearless concurrency through ownership system [2]");
        println!("- Zero-cost abstractions for performance [2]");
        println!("\nThese features make Rust ideal for systems programming where performance and safety are critical [1][2].");
    }
    
    Ok(())
}

/// Demonstrate domain-filtered RAG
async fn domain_filtered_rag_example() -> Result<()> {
    println!("🌐 Filtering search to devblogs.microsoft.com only");
    
    let search_plugin = SearchService::new("bing");
    let results = search_plugin.search(QUERY_SEMANTIC_KERNEL, Some("devblogs.microsoft.com")).await?;
    
    println!("\n📊 Domain-Filtered Results: {} found", results.len());
    for result in &results {
        println!("- {}: {}", result.name, result.link);
    }
    
    if results.is_empty() {
        println!("No results found for the specified domain filter.");
    } else {
        println!("\n💡 Domain filtering ensures results come only from trusted sources");
    }
    
    Ok(())
}

/// Demonstrate RAG with full page content
async fn full_content_rag_example() -> Result<()> {
    println!("📄 Using full page content for comprehensive RAG");
    
    let search_plugin = SearchService::new("bing");
    let results = search_plugin.search_with_full_content(QUERY_SEMANTIC_KERNEL, Some("learn.microsoft.com")).await?;
    
    println!("\n🔍 Retrieved {} pages with full content", results.len());
    
    if !results.is_empty() {
        println!("\n📑 Sample Full Content Result:");
        println!("Title: {}", results[0].name);
        println!("Content Preview: {}...", &results[0].value[..200.min(results[0].value.len())]);
        println!("Source: {}", results[0].link);
    }
    
    // Demonstrate how full content improves RAG quality
    println!("\n💡 Full page content provides:");
    println!("- More comprehensive context for accurate answers");
    println!("- Detailed technical information beyond snippets");
    println!("- Better grounding for complex queries");
    
    Ok(())
}

/// Create kernel with search plugin
async fn create_kernel_with_search_plugin(search_type: &str) -> Result<Kernel> {
    let mut kernel_builder = KernelBuilder::new();
    
    if let Ok(api_key) = env::var("OPENAI_API_KEY") {
        let client = OpenAIClient::new(api_key)?;
        kernel_builder = kernel_builder.add_chat_completion_service(client);
    }
    
    let mut kernel = kernel_builder.build();
    
    // Add search plugin
    let plugin = Box::new(SearchPlugin::new_with_search(search_type));
    kernel.add_plugin("SearchPlugin", plugin);
    
    Ok(kernel)
}

/// Create kernel with citations plugin
async fn create_kernel_with_citations_plugin(search_type: &str) -> Result<Kernel> {
    let mut kernel_builder = KernelBuilder::new();
    
    if let Ok(api_key) = env::var("OPENAI_API_KEY") {
        let client = OpenAIClient::new(api_key)?;
        kernel_builder = kernel_builder.add_chat_completion_service(client);
    }
    
    let mut kernel = kernel_builder.build();
    
    // Add citations plugin
    let plugin = Box::new(SearchPlugin::new_with_citations(search_type));
    kernel.add_plugin("SearchPlugin", plugin);
    
    Ok(kernel)
}