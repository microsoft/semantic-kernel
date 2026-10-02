//! Step 3: Switch Vector Store
//! 
//! This example demonstrates how to switch between different vector stores with the same code.
//! It shows:
//! - Using the same data ingestion code with different stores
//! - Using the same search code with different stores
//! - Comparing results between InMemory and Qdrant stores
//! - Abstracting vector store implementation details
//! 
//! The key insight is that the MemoryStore trait provides a common interface,
//! allowing you to easily switch between different vector store implementations.

use anyhow::Result;
use semantic_kernel::services::EmbeddingService;
use sk_openai::OpenAIClient;
use sk_memory::{MemoryStore, InMemoryMemoryStore, QdrantMemoryStore, MemoryRecord};
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
    println!("🤖 Semantic Kernel Rust - Step 3: Switch Vector Store");
    println!("===================================================\n");

    // Example 1: Use InMemory vector store
    println!("Example 1: InMemory Vector Store");
    println!("===============================");
    
    use_inmemory_store().await?;

    // Example 2: Use Qdrant vector store (if available)
    println!("\nExample 2: Qdrant Vector Store");
    println!("==============================");
    
    use_qdrant_store().await?;

    // Example 3: Abstract store implementation
    println!("\nExample 3: Abstract Store Implementation");
    println!("======================================");
    
    use_abstract_store().await?;

    println!("\n✅ Step03 Switch VectorStore example completed!");

    Ok(())
}

/// Demonstrate using InMemory vector store
async fn use_inmemory_store() -> Result<()> {
    // Create InMemory store
    let memory_store = InMemoryMemoryStore::new();
    let collection_name = "skglossary";
    
    // Ingest data using common function
    ingest_data_into_store(&memory_store, collection_name).await?;
    
    // Search using common function
    let result = search_store(&memory_store, collection_name, "What is an Application Programming Interface?").await?;
    
    if let Some((record, score)) = result {
        println!("📄 InMemory Result:");
        println!("   Term: {}", record.metadata.description.as_ref().unwrap_or(&"Unknown".to_string()));
        println!("   Definition: {}", &record.text[..80.min(record.text.len())]);
        println!("   Score: {:.3}", score);
    }
    
    Ok(())
}

/// Demonstrate using Qdrant vector store
async fn use_qdrant_store() -> Result<()> {
    // Check if Qdrant is available
    let qdrant_url = env::var("QDRANT_URL").unwrap_or_else(|_| "http://localhost:6333".to_string());
    
    // Try to create Qdrant store
    match QdrantMemoryStore::new(qdrant_url.clone()).await {
        Ok(memory_store) => {
            let collection_name = "skglossary_qdrant";
            
            // Create collection if needed
            if !memory_store.collection_exists(collection_name).await
                .map_err(|e| anyhow::anyhow!("Failed to check collection: {}", e))? {
                memory_store.create_collection(collection_name).await
                    .map_err(|e| anyhow::anyhow!("Failed to create collection: {}", e))?;
            }
            
            // Ingest data using common function
            ingest_data_into_store(&memory_store, collection_name).await?;
            
            // Search using common function
            let result = search_store(&memory_store, collection_name, "What is an Application Programming Interface?").await?;
            
            if let Some((record, score)) = result {
                println!("📄 Qdrant Result:");
                println!("   Term: {}", record.metadata.description.as_ref().unwrap_or(&"Unknown".to_string()));
                println!("   Definition: {}", &record.text[..80.min(record.text.len())]);
                println!("   Score: {:.3}", score);
            }
        }
        Err(_) => {
            println!("⚠️  Qdrant not available. To run this example with Qdrant:");
            println!("   1. Start Qdrant: docker run -p 6333:6333 qdrant/qdrant");
            println!("   2. Set QDRANT_URL environment variable if not using localhost:6333");
        }
    }
    
    Ok(())
}

/// Demonstrate abstract store usage - write once, run with any store
async fn use_abstract_store() -> Result<()> {
    println!("This example shows how the same code works with different stores:\n");
    
    // Create different stores
    let inmemory_store: Arc<dyn MemoryStore> = Arc::new(InMemoryMemoryStore::new());
    let mut stores: Vec<(&str, Arc<dyn MemoryStore>)> = vec![
        ("InMemory", inmemory_store),
    ];
    
    // Add Qdrant if available
    if let Ok(qdrant_store) = QdrantMemoryStore::new("http://localhost:6333").await {
        stores.push(("Qdrant", Arc::new(qdrant_store)));
    }
    
    // Run the same workflow with each store
    for (store_name, store) in stores {
        println!("🔧 Using {} store:", store_name);
        
        let collection_name = format!("glossary_{}", store_name.to_lowercase());
        
        // Same ingestion code for all stores
        ingest_data_into_store(store.as_ref(), &collection_name).await?;
        
        // Same search code for all stores
        let queries = vec![
            "What is an SDK?",
            "Tell me about AI models",
            "How does semantic kernel work?",
        ];
        
        for query in queries {
            let result = search_store(store.as_ref(), &collection_name, query).await?;
            
            if let Some((record, score)) = result {
                println!("   Query: \"{}\"", query);
                println!("   Found: {} (score: {:.3})", 
                    record.metadata.description.as_ref().unwrap_or(&"Unknown".to_string()),
                    score
                );
            }
        }
        println!();
    }
    
    println!("🎯 Key Insight: The same code works with any MemoryStore implementation!");
    
    Ok(())
}

/// Common function to ingest data into any memory store
async fn ingest_data_into_store(
    memory_store: &dyn MemoryStore,
    collection_name: &str,
) -> Result<()> {
    // Create collection if it doesn't exist
    if !memory_store.collection_exists(collection_name).await
        .map_err(|e| anyhow::anyhow!("Failed to check collection: {}", e))? {
        memory_store.create_collection(collection_name).await
            .map_err(|e| anyhow::anyhow!("Failed to create collection: {}", e))?;
    }
    
    // Create sample data
    let entries = create_glossary_entries();
    
    // Create embedding service if available
    let embedding_service = create_embedding_service().await?;
    
    // Ingest data with embeddings
    let mut records = Vec::new();
    for entry in entries {
        let embedding = if let Some(ref embeddings) = embedding_service {
            embeddings.generate_embeddings(&[entry.definition.clone()]).await
                .map_err(|e| anyhow::anyhow!("Failed to generate embedding: {}", e))?
                .into_iter()
                .next()
                .unwrap_or_else(|| vec![0.0; 1536])
        } else {
            generate_mock_embedding(&entry.definition)
        };
        
        let record = MemoryRecord::with_embedding(&entry.key, &entry.definition, embedding)
            .with_source(&entry.category)
            .with_tag(&entry.category)
            .with_description(&entry.term)
            .with_attribute("term", &entry.term);
        records.push(record);
    }
    
    memory_store.upsert_batch(collection_name, records).await
        .map_err(|e| anyhow::anyhow!("Failed to ingest data: {}", e))?;
    
    Ok(())
}

/// Common function to search any memory store
async fn search_store(
    memory_store: &dyn MemoryStore,
    collection_name: &str,
    query: &str,
) -> Result<Option<(MemoryRecord, f32)>> {
    // Create embedding service if available
    let embedding_service = create_embedding_service().await?;
    
    // Generate embedding for query
    let search_embedding = if let Some(ref embeddings) = embedding_service {
        embeddings.generate_embeddings(&[query.to_string()]).await
            .map_err(|e| anyhow::anyhow!("Failed to generate embedding: {}", e))?
            .into_iter()
            .next()
            .unwrap_or_else(|| vec![0.0; 1536])
    } else {
        generate_mock_embedding(query)
    };
    
    // Search the store
    let result = memory_store.get_nearest_match(
        collection_name,
        search_embedding,
        0.5, // minimum relevance score
        false, // don't include embeddings in results
    ).await
        .map_err(|e| anyhow::anyhow!("Failed to search: {}", e))?;
    
    Ok(result.map(|r| (r.record, r.score)))
}

/// Generate a mock embedding
fn generate_mock_embedding(text: &str) -> Vec<f32> {
    let mut embedding = vec![0.0; 1536];
    let text_lower = text.to_lowercase();
    let keywords = vec!["api", "sdk", "kernel", "ai", "llm", "rag", "software", "semantic"];
    
    for (i, keyword) in keywords.iter().enumerate() {
        let count = text_lower.matches(keyword).count() as f32;
        if count > 0.0 {
            embedding[i * 100] = count * 0.3;
        }
    }
    
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