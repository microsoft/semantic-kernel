//! Step 1: Ingest Data
//! 
//! This example demonstrates how to generate embeddings and ingest data into a memory store.
//! It shows:
//! - Creating memory store collections
//! - Defining data models with vector embeddings
//! - Generating embeddings for text content
//! - Batch inserting data into the memory store
//! - Retrieving stored data by key

use anyhow::Result;
use semantic_kernel::services::EmbeddingService;
use sk_openai::OpenAIClient;
use sk_memory::{MemoryStore, InMemoryMemoryStore, MemoryRecord};
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
    println!("🤖 Semantic Kernel Rust - Step 1: Ingest Data");
    println!("============================================\n");

    // Example 1: Basic data ingestion
    println!("Example 1: Basic Data Ingestion");
    println!("==============================");
    
    basic_ingestion_example().await?;

    // Example 2: Batch ingestion with embeddings
    println!("\nExample 2: Batch Ingestion with Embeddings");
    println!("=========================================");
    
    batch_ingestion_with_embeddings().await?;

    // Example 3: Category-based ingestion
    println!("\nExample 3: Category-Based Organization");
    println!("=====================================");
    
    category_based_ingestion().await?;

    println!("\n✅ Step01 Ingest Data example completed!");

    Ok(())
}

/// Demonstrate basic data ingestion into memory store
async fn basic_ingestion_example() -> Result<()> {
    // Create an in-memory memory store
    let memory_store = InMemoryMemoryStore::new();
    
    // Create the collection if it doesn't exist
    let collection_name = "skglossary";
    if !memory_store.collection_exists(collection_name).await
        .map_err(|e| anyhow::anyhow!("Failed to check collection: {}", e))? {
        memory_store.create_collection(collection_name).await
            .map_err(|e| anyhow::anyhow!("Failed to create collection: {}", e))?;
        println!("📁 Created collection: {}", collection_name);
    }

    // Create sample glossary entries
    let entries = vec![
        GlossaryEntry::new("1", "Software", "API", 
            "Application Programming Interface. A set of rules and specifications that allow software components to communicate and exchange data."),
        GlossaryEntry::new("2", "Software", "SDK", 
            "Software development kit. A set of libraries and tools that allow software developers to build software more easily."),
    ];

    // Insert entries into the collection
    for entry in &entries {
        let record = MemoryRecord::new(
            &entry.key,
            &format!("{}: {}", entry.term, entry.definition),
        )
        .with_source(&entry.category)
        .with_tag(&entry.category)
        .with_description(&entry.term)
        .with_attribute("term", &entry.term);
        
        memory_store.upsert(collection_name, record).await
            .map_err(|e| anyhow::anyhow!("Failed to upsert: {}", e))?;
        println!("✅ Ingested: {} - {}", entry.term, entry.category);
    }

    // Retrieve and display an entry
    if let Some(record) = memory_store.get(collection_name, "1").await
        .map_err(|e| anyhow::anyhow!("Failed to get record: {}", e))? {
        println!("\n📖 Retrieved entry:");
        if let Some(description) = &record.metadata.description {
            println!("   Term: {}", description);
        }
        println!("   Definition: {}", record.text);
    }

    Ok(())
}

/// Demonstrate batch ingestion with embedding generation
async fn batch_ingestion_with_embeddings() -> Result<()> {
    // Create memory store and collection
    let memory_store = InMemoryMemoryStore::new();
    let collection_name = "skglossary_embeddings";
    
    if !memory_store.collection_exists(collection_name).await
        .map_err(|e| anyhow::anyhow!("Failed to check collection: {}", e))? {
        memory_store.create_collection(collection_name).await
            .map_err(|e| anyhow::anyhow!("Failed to create collection: {}", e))?;
    }

    // Create embedding service
    let embedding_service = create_embedding_service().await?;

    // Create glossary entries
    let entries = create_glossary_entries();

    // Generate embeddings and create memory records
    println!("🔄 Generating embeddings for {} entries...", entries.len());
    
    let mut memory_records = Vec::new();
    
    for entry in &entries {
        let embedding = if let Some(ref embeddings) = embedding_service {
            // Generate embedding for the definition
            let emb = embeddings.generate_embeddings(&[entry.definition.clone()]).await
                .map_err(|e| anyhow::anyhow!("Failed to generate embedding: {}", e))?
                .into_iter()
                .next()
                .unwrap_or_else(|| vec![0.0; 1536]);
            println!("   ✅ Generated embedding for: {}", entry.term);
            emb
        } else {
            // Mock embedding for demonstration
            println!("   📊 Using mock embedding for: {}", entry.term);
            vec![0.1; 1536] // 1536 dimensions for OpenAI
        };
        
        let record = MemoryRecord::with_embedding(&entry.key, &entry.definition, embedding)
            .with_source(&entry.category)
            .with_tag(&entry.category)
            .with_description(&entry.term)
            .with_attribute("term", &entry.term);
        
        memory_records.push(record);
    }

    // Batch insert all entries
    memory_store.upsert_batch(collection_name, memory_records).await
        .map_err(|e| anyhow::anyhow!("Failed to upsert batch: {}", e))?;
    
    println!("\n✅ Batch ingested {} entries with embeddings", entries.len());

    Ok(())
}

/// Demonstrate category-based data organization
async fn category_based_ingestion() -> Result<()> {
    let memory_store = InMemoryMemoryStore::new();
    
    // Create separate collections for different categories
    let categories = vec!["Software", "SK", "AI"];
    
    for category in &categories {
        let collection_name = format!("glossary_{}", category.to_lowercase());
        
        if !memory_store.collection_exists(&collection_name).await
            .map_err(|e| anyhow::anyhow!("Failed to check collection: {}", e))? {
            memory_store.create_collection(&collection_name).await
                .map_err(|e| anyhow::anyhow!("Failed to create collection: {}", e))?;
        }
        
        // Get entries for this category
        let category_entries: Vec<GlossaryEntry> = create_glossary_entries()
            .into_iter()
            .filter(|e| &e.category == category)
            .collect();
        
        if !category_entries.is_empty() {
            let mut records = Vec::new();
            
            for entry in &category_entries {
                let record = MemoryRecord::with_embedding(&entry.key, &entry.definition, vec![0.1; 1536])
                    .with_source(&entry.category)
                    .with_tag(&entry.category)
                    .with_description(&entry.term)
                    .with_attribute("term", &entry.term);
                    
                records.push(record);
            }
            
            memory_store.upsert_batch(&collection_name, records).await
                .map_err(|e| anyhow::anyhow!("Failed to upsert batch: {}", e))?;
            println!("📁 Category '{}': Ingested {} entries", category, category_entries.len());
            
            for entry in &category_entries {
                println!("   - {}: {}", entry.term, &entry.definition[..50.min(entry.definition.len())]);
            }
        }
    }

    // Demonstrate listing collections
    let collections = memory_store.get_collections().await
        .map_err(|e| anyhow::anyhow!("Failed to get collections: {}", e))?;
    println!("\n🔍 Collections created:");
    for collection in collections {
        println!("   - {}", collection);
    }

    Ok(())
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