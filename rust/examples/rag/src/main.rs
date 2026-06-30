//! RAG (Retrieval-Augmented Generation) Example
//! 
//! This example demonstrates the complete memory store and embedding flow:
//! 1. Ingests a markdown file by splitting it into chunks
//! 2. Generates embeddings for each chunk using OpenAI
//! 3. Stores the chunks with embeddings in a memory store
//! 4. Retrieves relevant chunks based on a query
//! 5. Uses the retrieved context to generate an answer

use anyhow::Result;
use clap::{Parser, Subcommand};
use sk_memory::{EmbeddingFlow, InMemoryMemoryStore, MemoryStore};
use sk_openai::OpenAIClient;
use std::fs;
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "rag")]
#[command(about = "A RAG example using Semantic Kernel Rust")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Ingest a markdown file into the memory store
    Ingest {
        /// Path to the markdown file to ingest
        #[arg(short, long)]
        file: PathBuf,
        /// Collection name to store the chunks in
        #[arg(short, long, default_value = "documents")]
        collection: String,
        /// Chunk size for splitting the document
        #[arg(long, default_value = "1000")]
        chunk_size: usize,
        /// Overlap between chunks
        #[arg(long, default_value = "100")]
        overlap: usize,
    },
    /// Query the memory store for relevant chunks
    Query {
        /// The question or query to search for
        #[arg(short, long)]
        query: String,
        /// Collection name to search in
        #[arg(short, long, default_value = "documents")]
        collection: String,
        /// Number of results to return
        #[arg(short, long, default_value = "3")]
        limit: usize,
        /// Minimum relevance score (0.0 to 1.0)
        #[arg(long, default_value = "0.7")]
        min_score: f32,
    },
    /// Demonstrate both ingestion and querying with a sample document
    Demo {
        /// Collection name to use for the demo
        #[arg(short, long, default_value = "demo")]
        collection: String,
    },
}

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize tracing
    tracing_subscriber::fmt::init();

    let cli = Cli::parse();

    // Initialize OpenAI client for embeddings
    let openai_client = match std::env::var("OPENAI_API_KEY") {
        Ok(api_key) => OpenAIClient::new(api_key)?,
        Err(_) => {
            eprintln!("Error: OPENAI_API_KEY environment variable not set");
            eprintln!("Please set your OpenAI API key:");
            eprintln!("  export OPENAI_API_KEY=your_api_key_here");
            std::process::exit(1);
        }
    };

    // Initialize in-memory store (in production, you might use Qdrant)
    let memory_store = InMemoryMemoryStore::new();
    
    // Create the embedding flow
    let embedding_flow = EmbeddingFlow::new(memory_store, openai_client);

    match cli.command {
        Commands::Ingest { file, collection, chunk_size, overlap } => {
            ingest_file(&embedding_flow, &file, &collection, chunk_size, overlap).await?;
        }
        Commands::Query { query, collection, limit, min_score } => {
            query_collection(&embedding_flow, &query, &collection, limit, min_score).await?;
        }
        Commands::Demo { collection } => {
            demo(&embedding_flow, &collection).await?;
        }
    }

    Ok(())
}

async fn ingest_file(
    flow: &EmbeddingFlow<InMemoryMemoryStore, OpenAIClient>,
    file_path: &PathBuf,
    collection: &str,
    chunk_size: usize,
    overlap: usize,
) -> Result<()> {
    println!("📖 Reading file: {}", file_path.display());
    
    let content = fs::read_to_string(file_path)?;
    let source = file_path.to_string_lossy().to_string();

    println!("🧠 Creating collection '{}'...", collection);
    flow.memory_store().create_collection(collection).await
        .map_err(|e| anyhow::anyhow!("Failed to create collection: {}", e))?;

    println!("✂️  Splitting document into chunks (size: {}, overlap: {})...", chunk_size, overlap);
    println!("🔄 Generating embeddings and storing chunks...");

    let chunk_ids = flow.ingest_document(
        collection,
        &content,
        Some(source),
        chunk_size,
        overlap,
    ).await.map_err(|e| anyhow::anyhow!("Failed to ingest document: {}", e))?;

    println!("✅ Successfully ingested {} chunks into collection '{}'", chunk_ids.len(), collection);
    
    // Show some statistics
    let total_records = flow.memory_store().collection_size(collection).await;
    println!("📊 Collection '{}' now contains {} records", collection, total_records);

    Ok(())
}

async fn query_collection(
    flow: &EmbeddingFlow<InMemoryMemoryStore, OpenAIClient>,
    query: &str,
    collection: &str,
    limit: usize,
    min_score: f32,
) -> Result<()> {
    println!("🔍 Searching for: '{}'", query);
    println!("📚 Collection: '{}'", collection);

    // Check if collection exists
    if !flow.memory_store().collection_exists(collection).await
        .map_err(|e| anyhow::anyhow!("Failed to check collection existence: {}", e))? {
        eprintln!("❌ Collection '{}' does not exist. Please ingest some documents first.", collection);
        return Ok(());
    }

    let results = flow.search_similar(collection, query, limit, min_score).await
        .map_err(|e| anyhow::anyhow!("Failed to search: {}", e))?;

    if results.is_empty() {
        println!("❌ No relevant chunks found with minimum score {:.2}", min_score);
        return Ok(());
    }

    println!("✅ Found {} relevant chunks:", results.len());
    println!();

    for (i, result) in results.iter().enumerate() {
        println!("📄 Result {} (Score: {:.3}):", i + 1, result.score);
        println!("   ID: {}", result.record.id);
        
        if let Some(source) = &result.record.metadata.source {
            println!("   Source: {}", source);
        }
        
        // Truncate content for display
        let content = if result.record.text.len() > 200 {
            format!("{}...", &result.record.text[..200])
        } else {
            result.record.text.clone()
        };
        
        println!("   Content: {}", content);
        println!();
    }

    // Combine all results for potential use in RAG
    let combined_context: String = results.iter()
        .map(|r| r.record.text.as_str())
        .collect::<Vec<_>>()
        .join("\n\n");

    println!("🔗 Combined context length: {} characters", combined_context.len());
    println!("💡 This context could be used with a chat completion service for RAG");

    Ok(())
}

async fn demo(
    flow: &EmbeddingFlow<InMemoryMemoryStore, OpenAIClient>,
    collection: &str,
) -> Result<()> {
    println!("🚀 Running RAG Demo");
    println!("==================");

    // Sample markdown content about Rust
    let sample_content = r#"# Rust Programming Language

## Introduction
Rust is a systems programming language that runs blazingly fast, prevents segfaults, and guarantees thread safety. It aims to be as fast as C and C++ while being completely memory safe.

## Memory Safety
Rust achieves memory safety without garbage collection through its ownership system. The ownership system is based on three main rules:

1. Each value in Rust has a variable that's called its owner
2. There can only be one owner at a time
3. When the owner goes out of scope, the value will be dropped

## Concurrency
Rust's approach to concurrency is unique. The language provides several concurrency primitives:

- **Threads**: Rust provides native threads through `std::thread`
- **Message Passing**: Use channels to send data between threads
- **Shared State**: Use mutexes and atomic types for shared state

## Performance
Rust is designed to be as fast as possible. Some key performance features include:

- Zero-cost abstractions
- No garbage collector
- Minimal runtime overhead
- Efficient memory layout

## Web Development
Rust is increasingly popular for web development with frameworks like:

- **Actix Web**: Fast and practical web framework
- **Rocket**: Type-safe web framework
- **Axum**: Modular web framework built on Tokio

## Conclusion
Rust represents a significant advancement in systems programming, offering the performance of low-level languages with the safety of high-level languages.
"#;

    println!("📝 Creating sample document about Rust programming...");
    
    // Create collection
    flow.memory_store().create_collection(collection).await
        .map_err(|e| anyhow::anyhow!("Failed to create collection: {}", e))?;

    // Ingest the sample document
    println!("🔄 Ingesting document into collection '{}'...", collection);
    let chunk_ids = flow.ingest_document(
        collection,
        sample_content,
        Some("rust_guide.md".to_string()),
        400, // Smaller chunks for demo
        50,
    ).await.map_err(|e| anyhow::anyhow!("Failed to ingest document: {}", e))?;

    println!("✅ Ingested {} chunks", chunk_ids.len());
    println!();

    // Demo queries
    let demo_queries = vec![
        "How does Rust ensure memory safety?",
        "What are Rust's concurrency features?",
        "Is Rust good for web development?",
        "What makes Rust fast?",
    ];

    for query in demo_queries {
        println!("🔍 Query: {}", query);
        
        let results = flow.search_similar(collection, query, 2, 0.5).await
            .map_err(|e| anyhow::anyhow!("Failed to search: {}", e))?;
        
        if results.is_empty() {
            println!("   No relevant results found");
        } else {
            for (i, result) in results.iter().enumerate() {
                println!("   {}. (Score: {:.3}) {}", 
                    i + 1, 
                    result.score, 
                    truncate_text(&result.record.text, 100)
                );
            }
        }
        println!();
    }

    println!("✨ Demo completed! In a real application, you would:");
    println!("   1. Use the retrieved context with a chat completion service");
    println!("   2. Generate a comprehensive answer using RAG");
    println!("   3. Potentially use a vector database like Qdrant for production");

    Ok(())
}

fn truncate_text(text: &str, max_len: usize) -> String {
    if text.len() <= max_len {
        text.to_string()
    } else {
        format!("{}...", &text[..max_len])
    }
}