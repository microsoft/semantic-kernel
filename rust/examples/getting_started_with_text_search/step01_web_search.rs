//! Step 1: Web Search
//! 
//! This example demonstrates how to create and use text search functionality.
//! It shows:
//! - Creating a text search interface
//! - Performing web searches with different providers
//! - Processing and displaying search results
//! - Integration with Semantic Kernel for AI-powered search

use anyhow::Result;
use semantic_kernel::KernelBuilder;
use sk_openai::OpenAIClient;
use std::env;
use serde::{Deserialize, Serialize};

const BING_SEARCH_QUERY: &str = "What is the Semantic Kernel?";
const GOOGLE_SEARCH_QUERY: &str = "Rust programming language features";

#[derive(Debug, Serialize, Deserialize)]
struct SearchResult {
    title: String,
    url: String,
    snippet: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct SearchResults {
    results: Vec<SearchResult>,
    total_results: usize,
}

/// Trait for text search implementations
trait TextSearch {
    async fn search_async(&self, query: &str, top: usize) -> Result<SearchResults>;
}

/// Mock Bing text search implementation
struct BingTextSearch {
    _api_key: String,
}

impl BingTextSearch {
    fn new(api_key: String) -> Self {
        Self { _api_key: api_key }
    }
}

impl TextSearch for BingTextSearch {
    async fn search_async(&self, query: &str, top: usize) -> Result<SearchResults> {
        // Mock implementation - in real scenario, this would call Bing Search API
        let mock_results = vec![
            SearchResult {
                title: "Semantic Kernel - Microsoft Learn".to_string(),
                url: "https://learn.microsoft.com/semantic-kernel".to_string(),
                snippet: "Semantic Kernel is an SDK that integrates Large Language Models (LLMs) like OpenAI, Azure OpenAI, and Hugging Face with conventional programming languages.".to_string(),
            },
            SearchResult {
                title: "microsoft/semantic-kernel - GitHub".to_string(),
                url: "https://github.com/microsoft/semantic-kernel".to_string(),
                snippet: "Integrate cutting-edge LLM technology quickly and easily into your apps. Microsoft Semantic Kernel is an SDK for AI orchestration.".to_string(),
            },
            SearchResult {
                title: "Getting Started with Semantic Kernel".to_string(),
                url: "https://devblogs.microsoft.com/semantic-kernel/".to_string(),
                snippet: "Learn how to build AI applications with Semantic Kernel, featuring agents, plugins, and multi-modal capabilities.".to_string(),
            },
            SearchResult {
                title: "Semantic Kernel Documentation".to_string(),
                url: "https://docs.microsoft.com/semantic-kernel".to_string(),
                snippet: "Complete documentation for Semantic Kernel including tutorials, API reference, and best practices for AI development.".to_string(),
            },
        ];

        let results: Vec<SearchResult> = mock_results.into_iter().take(top).collect();
        
        println!("🔍 Bing Search: \"{}\"", query);
        
        Ok(SearchResults {
            total_results: results.len(),
            results,
        })
    }
}

/// Mock Google text search implementation
struct GoogleTextSearch {
    _search_engine_id: String,
    _api_key: String,
}

impl GoogleTextSearch {
    fn new(search_engine_id: String, api_key: String) -> Self {
        Self {
            _search_engine_id: search_engine_id,
            _api_key: api_key,
        }
    }
}

impl TextSearch for GoogleTextSearch {
    async fn search_async(&self, query: &str, top: usize) -> Result<SearchResults> {
        // Mock implementation - in real scenario, this would call Google Custom Search API
        let mock_results = vec![
            SearchResult {
                title: "Rust Programming Language".to_string(),
                url: "https://www.rust-lang.org/".to_string(),
                snippet: "Rust is a systems programming language that runs blazingly fast, prevents segfaults, and guarantees thread safety.".to_string(),
            },
            SearchResult {
                title: "The Rust Programming Language Book".to_string(),
                url: "https://doc.rust-lang.org/book/".to_string(),
                snippet: "This book will teach you about the Rust programming language. Rust is a systems programming language focused on safety and performance.".to_string(),
            },
            SearchResult {
                title: "Rust Features and Capabilities".to_string(),
                url: "https://forge.rust-lang.org/".to_string(),
                snippet: "Zero-cost abstractions, move semantics, guaranteed memory safety, threads without data races, trait-based generics, and more.".to_string(),
            },
            SearchResult {
                title: "Why Rust? - Mozilla Research".to_string(),
                url: "https://research.mozilla.org/rust/".to_string(),
                snippet: "Rust provides memory safety without garbage collection, making it perfect for systems programming and performance-critical applications.".to_string(),
            },
        ];

        let results: Vec<SearchResult> = mock_results.into_iter().take(top).collect();
        
        println!("🔍 Google Search: \"{}\"", query);
        
        Ok(SearchResults {
            total_results: results.len(),
            results,
        })
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    println!("🤖 Semantic Kernel Rust - Step 1: Web Search");
    println!("===========================================\n");

    // Example 1: Bing search
    println!("Example 1: Bing Text Search");
    println!("===========================");
    
    bing_search_example().await?;

    // Example 2: Google search
    println!("\nExample 2: Google Text Search");
    println!("=============================");
    
    google_search_example().await?;

    // Example 3: AI-powered search with kernel integration
    println!("\nExample 3: AI-Powered Search Analysis");
    println!("====================================");
    
    ai_powered_search_example().await?;

    println!("\n✅ Step01 Web Search example completed!");

    Ok(())
}

/// Demonstrate Bing text search
async fn bing_search_example() -> Result<()> {
    // Use mock API key for demonstration
    let api_key = env::var("BING_API_KEY").unwrap_or_else(|_| "mock_bing_key".to_string());
    let text_search = BingTextSearch::new(api_key);

    let search_results = text_search.search_async(BING_SEARCH_QUERY, 4).await?;

    println!("Found {} results:", search_results.total_results);
    for (i, result) in search_results.results.iter().enumerate() {
        println!("\n{}. {}", i + 1, result.title);
        println!("   URL: {}", result.url);
        println!("   {}", result.snippet);
    }

    Ok(())
}

/// Demonstrate Google text search
async fn google_search_example() -> Result<()> {
    // Use mock credentials for demonstration
    let search_engine_id = env::var("GOOGLE_SEARCH_ENGINE_ID").unwrap_or_else(|_| "mock_engine_id".to_string());
    let api_key = env::var("GOOGLE_API_KEY").unwrap_or_else(|_| "mock_google_key".to_string());
    
    let text_search = GoogleTextSearch::new(search_engine_id, api_key);

    let search_results = text_search.search_async(GOOGLE_SEARCH_QUERY, 4).await?;

    println!("Found {} results:", search_results.total_results);
    for (i, result) in search_results.results.iter().enumerate() {
        println!("\n{}. {}", i + 1, result.title);
        println!("   URL: {}", result.url);
        println!("   {}", result.snippet);
    }

    Ok(())
}

/// Demonstrate AI-powered search analysis using Semantic Kernel
async fn ai_powered_search_example() -> Result<()> {
    // Create search results from both providers
    let bing_search = BingTextSearch::new("mock_key".to_string());
    let google_search = GoogleTextSearch::new("mock_engine".to_string(), "mock_key".to_string());

    let bing_results = bing_search.search_async(BING_SEARCH_QUERY, 2).await?;
    let google_results = google_search.search_async(GOOGLE_SEARCH_QUERY, 2).await?;

    // Combine results for AI analysis
    let mut all_results = Vec::new();
    all_results.extend(bing_results.results);
    all_results.extend(google_results.results);

    println!("Analyzing {} search results with AI...", all_results.len());

    // Create kernel for AI analysis
    if let Ok(api_key) = env::var("OPENAI_API_KEY") {
        let client = OpenAIClient::new(api_key)?;
        let kernel = KernelBuilder::new()
            .add_chat_completion_service(client)
            .build();

        // Create analysis prompt
        let results_text = all_results
            .iter()
            .map(|r| format!("Title: {}\nSnippet: {}", r.title, r.snippet))
            .collect::<Vec<_>>()
            .join("\n\n");

        let analysis_prompt = format!(
            "Analyze these search results and provide a summary of the key themes and insights:\n\n{}",
            results_text
        );

        let analysis = kernel.invoke_prompt_async(&analysis_prompt).await
            .map_err(|e| anyhow::anyhow!("Failed to get AI analysis: {}", e))?;
        println!("\n🤖 AI Analysis:");
        println!("{}", analysis);
    } else {
        println!("⚠️  OPENAI_API_KEY not found, skipping AI analysis");
        println!("Mock AI Analysis: The search results show information about Semantic Kernel (an AI SDK) and Rust (a systems programming language), demonstrating diverse topics in modern software development.");
    }

    Ok(())
}