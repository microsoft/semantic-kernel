//! Step 2: Vector Search
//! 
//! This example demonstrates how to perform vector searches on a memory store.
//! It shows:
//! - Basic vector similarity search
//! - Finding the most relevant results
//! - Filtering search results by metadata
//! - Calculating and displaying similarity scores
//! - Multi-result searches with top-k retrieval

use anyhow::Result;
use semantic_kernel::services::EmbeddingService;
use sk_openai::OpenAIClient;
use sk_memory::{MemoryStore, InMemoryMemoryStore, MemoryRecord, SearchResult};
use std::env;
use std::sync::Arc;

/// Sample glossary entry structure
struct GlossaryEntry {
    key: String,
    category: String,
    term: String,
    definition: String,
}

impl GlossaryEntry {
    fn new(key: &str, category: &str, term: &str, definition: &str) -> Self {
        Self {
            key: key.to_string(),
            category: category.to_string(),
            term: term.to_string(),
            definition: definition.to_string(),
        }
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    println!("🤖 Semantic Kernel Rust - Step 2: Vector Search");
    println!("==============================================\n");

    // Example 1: Basic vector search
    println!("Example 1: Basic Vector Search");
    println!("=============================");
    
    basic_vector_search_example().await?;

    // Example 2: Vector search with filtering
    println!("\nExample 2: Vector Search with Filtering");
    println!("======================================");
    
    filtered_vector_search_example().await?;

    // Example 3: Multi-result search
    println!("\nExample 3: Multi-Result Vector Search");
    println!("====================================");
    
    multi_result_search_example().await?;

    println!("\n✅ Step02 Vector Search example completed!");

    Ok(())
}

/// Demonstrate basic vector search functionality
async fn basic_vector_search_example() -> Result<()> {
    // Set up memory store with data
    let (memory_store, collection_name) = setup_vector_store_with_data().await?;
    
    // Create embedding service
    let embedding_service = create_embedding_service().await?;
    
    // Search query
    let search_query = "What is an Application Programming Interface?";
    println!("🔍 Search query: \"{}\"", search_query);
    
    // Generate embedding for search query
    let search_embedding = if let Some(ref embeddings) = embedding_service {
        embeddings.generate_embeddings(&[search_query.to_string()]).await
            .map_err(|e| anyhow::anyhow!("Failed to generate embedding: {}", e))?
            .into_iter()
            .next()
            .unwrap_or_else(|| vec![0.0; 1536])
    } else {
        // Mock embedding for demonstration
        println!("⚠️  Using mock embedding for search");
        vec![0.1; 1536]
    };
    
    // Search the vector store
    let search_results = memory_store.get_nearest_match(
        &collection_name,
        search_embedding,
        0.5, // minimum relevance score
        false, // don't include embeddings in results
    ).await
        .map_err(|e| anyhow::anyhow!("Failed to search: {}", e))?;
    
    // Display results
    if let Some(result) = search_results {
        println!("\n📄 Top Match:");
        println!("   Term: {}", result.record.metadata.description.as_ref().unwrap_or(&"Unknown".to_string()));
        println!("   Definition: {}", result.record.text);
        println!("   Score: {:.3}", result.score);
        println!("   Category: {}", result.record.metadata.source.as_ref().unwrap_or(&"Unknown".to_string()));
    } else {
        println!("❌ No matches found above threshold");
    }
    
    Ok(())
}

/// Demonstrate vector search with filtering
async fn filtered_vector_search_example() -> Result<()> {
    // Set up memory store with data
    let (memory_store, collection_name) = setup_vector_store_with_data().await?;
    
    // Create embedding service
    let embedding_service = create_embedding_service().await?;
    
    // Search query targeting AI category
    let search_query = "How do I provide additional context to an LLM?";
    println!("🔍 Search query: \"{}\"", search_query);
    println!("🏷️  Filter: Category = 'AI'");
    
    // Generate embedding for search query
    let search_embedding = if let Some(ref embeddings) = embedding_service {
        embeddings.generate_embeddings(&[search_query.to_string()]).await
            .map_err(|e| anyhow::anyhow!("Failed to generate embedding: {}", e))?
            .into_iter()
            .next()
            .unwrap_or_else(|| vec![0.0; 1536])
    } else {
        vec![0.1; 1536]
    };
    
    // Search with multiple results to demonstrate filtering
    let all_results = memory_store.get_nearest_matches(
        &collection_name,
        search_embedding,
        5, // get top 5 results
        0.0, // no minimum score to see all results
        false,
    ).await
        .map_err(|e| anyhow::anyhow!("Failed to search: {}", e))?;
    
    // Filter results by category
    let filtered_results: Vec<SearchResult> = all_results
        .into_iter()
        .filter(|result| {
            result.record.metadata.source.as_ref()
                .map(|s| s == "AI")
                .unwrap_or(false)
        })
        .collect();
    
    // Display filtered results
    println!("\n📄 Filtered Results (AI category only):");
    for (i, result) in filtered_results.iter().take(3).enumerate() {
        println!("\n{}. Match:", i + 1);
        println!("   Term: {}", result.record.metadata.description.as_ref().unwrap_or(&"Unknown".to_string()));
        println!("   Definition: {}", &result.record.text[..100.min(result.record.text.len())]);
        println!("   Score: {:.3}", result.score);
        println!("   Category: {}", result.record.metadata.source.as_ref().unwrap_or(&"Unknown".to_string()));
    }
    
    Ok(())
}

/// Demonstrate multi-result vector search
async fn multi_result_search_example() -> Result<()> {
    // Set up memory store with data
    let (memory_store, collection_name) = setup_vector_store_with_data().await?;
    
    // Create embedding service
    let embedding_service = create_embedding_service().await?;
    
    // Search query
    let search_query = "software development tools and frameworks";
    println!("🔍 Search query: \"{}\"", search_query);
    println!("📊 Retrieving top 3 matches");
    
    // Generate embedding for search query
    let search_embedding = if let Some(ref embeddings) = embedding_service {
        embeddings.generate_embeddings(&[search_query.to_string()]).await
            .map_err(|e| anyhow::anyhow!("Failed to generate embedding: {}", e))?
            .into_iter()
            .next()
            .unwrap_or_else(|| vec![0.0; 1536])
    } else {
        vec![0.1; 1536]
    };
    
    // Search for multiple results
    let search_results = memory_store.get_nearest_matches(
        &collection_name,
        search_embedding,
        3, // get top 3 results
        0.3, // minimum relevance score
        false,
    ).await
        .map_err(|e| anyhow::anyhow!("Failed to search: {}", e))?;
    
    // Display all results with ranking
    println!("\n📄 Search Results:");
    for (i, result) in search_results.iter().enumerate() {
        println!("\n{}. Match (Score: {:.3}):", i + 1, result.score);
        println!("   Term: {}", result.record.metadata.description.as_ref().unwrap_or(&"Unknown".to_string()));
        println!("   Definition: {}...", &result.record.text[..80.min(result.record.text.len())]);
        println!("   Category: {}", result.record.metadata.source.as_ref().unwrap_or(&"Unknown".to_string()));
    }
    
    // Analysis of results
    if !search_results.is_empty() {
        let avg_score: f32 = search_results.iter().map(|r| r.score).sum::<f32>() / search_results.len() as f32;
        println!("\n📊 Search Statistics:");
        println!("   Results found: {}", search_results.len());
        println!("   Average score: {:.3}", avg_score);
        println!("   Score range: {:.3} - {:.3}", 
            search_results.last().map(|r| r.score).unwrap_or(0.0),
            search_results.first().map(|r| r.score).unwrap_or(0.0)
        );
    }
    
    Ok(())
}

/// Set up vector store with sample data
async fn setup_vector_store_with_data() -> Result<(InMemoryMemoryStore, String)> {
    let memory_store = InMemoryMemoryStore::new();
    let collection_name = "skglossary";
    
    // Create collection
    if !memory_store.collection_exists(collection_name).await
        .map_err(|e| anyhow::anyhow!("Failed to check collection: {}", e))? {
        memory_store.create_collection(collection_name).await
            .map_err(|e| anyhow::anyhow!("Failed to create collection: {}", e))?;
    }
    
    // Create sample data
    let entries = create_glossary_entries();
    
    // Ingest data with mock embeddings
    let mut records = Vec::new();
    for entry in entries {
        let embedding = generate_mock_embedding(&entry.definition);
        let record = MemoryRecord::with_embedding(&entry.key, &entry.definition, embedding)
            .with_source(&entry.category)
            .with_tag(&entry.category)
            .with_description(&entry.term)
            .with_attribute("term", &entry.term);
        records.push(record);
    }
    
    memory_store.upsert_batch(collection_name, records).await
        .map_err(|e| anyhow::anyhow!("Failed to ingest data: {}", e))?;
    
    Ok((memory_store, collection_name.to_string()))
}

/// Generate a mock embedding that provides some semantic similarity
fn generate_mock_embedding(text: &str) -> Vec<f32> {
    let mut embedding = vec![0.0; 1536];
    
    // Simple mock: use character frequencies to create pseudo-semantic embedding
    let text_lower = text.to_lowercase();
    let keywords = vec!["api", "sdk", "kernel", "ai", "llm", "rag", "software", "language", "model"];
    
    for (i, keyword) in keywords.iter().enumerate() {
        let count = text_lower.matches(keyword).count() as f32;
        if count > 0.0 {
            // Set specific dimensions based on keyword presence
            embedding[i * 100] = count * 0.3;
            embedding[i * 100 + 1] = count * 0.2;
        }
    }
    
    // Add some variation based on text length
    let length_factor = (text.len() as f32 / 100.0).min(1.0);
    embedding[1000] = length_factor;
    
    // Normalize
    let magnitude: f32 = embedding.iter().map(|x| x * x).sum::<f32>().sqrt();
    if magnitude > 0.0 {
        for value in &mut embedding {
            *value /= magnitude;
        }
    }
    
    embedding
}

/// Create sample glossary entries
fn create_glossary_entries() -> Vec<GlossaryEntry> {
    vec![
        GlossaryEntry::new("1", "Software", "API", 
            "Application Programming Interface. A set of rules and specifications that allow software components to communicate and exchange data."),
        GlossaryEntry::new("2", "Software", "SDK", 
            "Software development kit. A set of libraries and tools that allow software developers to build software more easily."),
        GlossaryEntry::new("3", "SK", "Connectors", 
            "Semantic Kernel Connectors allow software developers to integrate with various services providing AI capabilities, including LLM, AudioToText, TextToAudio, Embedding generation, etc."),
        GlossaryEntry::new("4", "SK", "Semantic Kernel", 
            "Semantic Kernel is a set of libraries that allow software developers to more easily develop applications that make use of AI experiences."),
        GlossaryEntry::new("5", "AI", "RAG", 
            "Retrieval Augmented Generation - a term that refers to the process of retrieving additional data to provide as context to an LLM to use when generating a response (completion) to a user's question (prompt)."),
        GlossaryEntry::new("6", "AI", "LLM", 
            "Large language model. A type of artificial intelligence algorithm that is designed to understand and generate human language."),
    ]
}

/// Create embedding service if API key is available
async fn create_embedding_service() -> Result<Option<Arc<dyn EmbeddingService>>> {
    if let Ok(api_key) = env::var("OPENAI_API_KEY") {
        let client = OpenAIClient::new(api_key)?;
        Ok(Some(Arc::new(client)))
    } else {
        println!("⚠️  OPENAI_API_KEY not found, using mock embeddings");
        Ok(None)
    }
}