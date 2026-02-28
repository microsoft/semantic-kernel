//! Step 4: Use Dynamic Data Model
//! 
//! This example demonstrates how to use dynamic data modeling with vector stores.
//! It shows:
//! - Using HashMap<String, Value> for flexible schema definition
//! - Runtime schema definition instead of compile-time structs
//! - Ingesting and searching data without predefined types
//! - Converting between static and dynamic data models
//! - Schema validation and type safety with dynamic data
//! 
//! Dynamic data modeling is useful when:
//! - Schema needs to be determined at runtime
//! - Working with data from external sources with varying schemas
//! - Building generic tools that work with any data structure
//! - Schema is loaded from configuration or external services

use anyhow::Result;
use sk_memory::{MemoryStore, InMemoryMemoryStore, MemoryRecord};
use serde_json::{json, Value};
use std::collections::HashMap;

/// Schema definition that can be determined at runtime
#[derive(Debug, Clone)]
struct DynamicSchema {
    key_field: String,
    text_field: String,
    embedding_field: String,
    metadata_fields: Vec<(String, String)>, // (field_name, field_type)
}

impl DynamicSchema {
    fn new() -> Self {
        Self {
            key_field: "id".to_string(),
            text_field: "text".to_string(),
            embedding_field: "embedding".to_string(),
            metadata_fields: vec![],
        }
    }

    fn with_metadata_field(mut self, name: &str, field_type: &str) -> Self {
        self.metadata_fields.push((name.to_string(), field_type.to_string()));
        self
    }
}

/// Dynamic record type using HashMap
type DynamicRecord = HashMap<String, Value>;

#[tokio::main]
async fn main() -> Result<()> {
    println!("🤖 Semantic Kernel Rust - Step 4: Dynamic Data Model");
    println!("==================================================\n");

    // Example 1: Basic dynamic data model
    println!("Example 1: Basic Dynamic Data Model");
    println!("==================================");
    
    basic_dynamic_model_example().await?;

    // Example 2: Schema from configuration
    println!("\nExample 2: Schema from Configuration");
    println!("===================================");
    
    schema_from_config_example().await?;

    // Example 3: Converting between static and dynamic models
    println!("\nExample 3: Static to Dynamic Conversion");
    println!("======================================");
    
    static_to_dynamic_conversion().await?;

    println!("\n✅ Step04 Dynamic Data Model example completed!");

    Ok(())
}

/// Demonstrate basic dynamic data modeling
async fn basic_dynamic_model_example() -> Result<()> {
    // Define schema at runtime
    let schema = DynamicSchema::new()
        .with_metadata_field("category", "string")
        .with_metadata_field("term", "string")
        .with_metadata_field("definition", "string");
    
    println!("📋 Dynamic Schema:");
    println!("   Key field: {}", schema.key_field);
    println!("   Text field: {}", schema.text_field);
    println!("   Metadata fields: {:?}", schema.metadata_fields);
    
    // Create memory store
    let memory_store = InMemoryMemoryStore::new();
    let collection_name = "dynamic_glossary";
    
    if !memory_store.collection_exists(collection_name).await
        .map_err(|e| anyhow::anyhow!("Failed to check collection: {}", e))? {
        memory_store.create_collection(collection_name).await
            .map_err(|e| anyhow::anyhow!("Failed to create collection: {}", e))?;
    }
    
    // Create dynamic records
    let records = create_dynamic_records(&schema)?;
    
    // Ingest dynamic records
    ingest_dynamic_records(&memory_store, collection_name, &records).await?;
    
    // Search with dynamic model
    let search_query = "What is an SDK?";
    let result = search_dynamic_records(&memory_store, collection_name, search_query).await?;
    
    if let Some((record, score)) = result {
        println!("\n🔍 Search result for: \"{}\"", search_query);
        println!("   Score: {:.3}", score);
        
        // Access dynamic fields
        for (key, value) in &record {
            if key != "embedding" && key != "timestamp" {
                println!("   {}: {}", key, value);
            }
        }
    }
    
    Ok(())
}

/// Demonstrate loading schema from configuration
async fn schema_from_config_example() -> Result<()> {
    // Simulate loading schema from JSON configuration
    let schema_json = json!({
        "key_field": "document_id",
        "text_field": "content",
        "embedding_field": "vector",
        "metadata_fields": [
            {"name": "title", "type": "string"},
            {"name": "author", "type": "string"},
            {"name": "date", "type": "string"},
            {"name": "tags", "type": "array"},
            {"name": "word_count", "type": "number"}
        ]
    });
    
    let schema = parse_schema_from_json(&schema_json)?;
    println!("📋 Schema loaded from configuration:");
    println!("   {}", serde_json::to_string_pretty(&schema_json)?);
    
    // Create sample documents using the schema
    let documents = vec![
        create_document(&schema, "doc1", "Understanding AI", 
            "AI is transforming how we work...", 
            "John Doe", "2024-01-15", vec!["AI", "Technology"], 150),
        create_document(&schema, "doc2", "Machine Learning Basics", 
            "Machine learning is a subset of AI...", 
            "Jane Smith", "2024-01-20", vec!["ML", "AI", "Tutorial"], 200),
    ];
    
    // Store and search documents
    let memory_store = InMemoryMemoryStore::new();
    let collection_name = "documents";
    
    if !memory_store.collection_exists(collection_name).await
        .map_err(|e| anyhow::anyhow!("Failed to check collection: {}", e))? {
        memory_store.create_collection(collection_name).await
            .map_err(|e| anyhow::anyhow!("Failed to create collection: {}", e))?;
    }
    
    // Ingest documents
    for doc in &documents {
        let record = dynamic_record_to_memory_record(&schema, doc)?;
        memory_store.upsert(collection_name, record).await
            .map_err(|e| anyhow::anyhow!("Failed to upsert: {}", e))?;
    }
    
    println!("\n✅ Ingested {} documents with dynamic schema", documents.len());
    
    Ok(())
}

/// Demonstrate converting between static and dynamic models
async fn static_to_dynamic_conversion() -> Result<()> {
    // Static model (compile-time)
    #[derive(Debug)]
    struct Product {
        id: String,
        name: String,
        description: String,
        price: f64,
        category: String,
    }
    
    let product = Product {
        id: "prod123".to_string(),
        name: "Semantic Kernel Book".to_string(),
        description: "A comprehensive guide to building AI applications".to_string(),
        price: 49.99,
        category: "Books".to_string(),
    };
    
    println!("📦 Static Product: {:?}", product);
    
    // Convert to dynamic model
    let mut dynamic_product = DynamicRecord::new();
    dynamic_product.insert("id".to_string(), json!(product.id));
    dynamic_product.insert("name".to_string(), json!(product.name));
    dynamic_product.insert("description".to_string(), json!(product.description));
    dynamic_product.insert("price".to_string(), json!(product.price));
    dynamic_product.insert("category".to_string(), json!(product.category));
    
    println!("\n🔄 Converted to Dynamic:");
    for (key, value) in &dynamic_product {
        println!("   {}: {}", key, value);
    }
    
    // Store in memory store
    let memory_store = InMemoryMemoryStore::new();
    let collection_name = "products";
    
    if !memory_store.collection_exists(collection_name).await
        .map_err(|e| anyhow::anyhow!("Failed to check collection: {}", e))? {
        memory_store.create_collection(collection_name).await
            .map_err(|e| anyhow::anyhow!("Failed to create collection: {}", e))?;
    }
    
    // Create record from dynamic data
    let embedding = generate_mock_embedding(&product.description);
    let record = MemoryRecord::with_embedding(
        &product.id,
        &product.description,
        embedding,
    )
    .with_source(&product.category)
    .with_attribute("name", &product.name)
    .with_attribute("price", &product.price.to_string());
    
    memory_store.upsert(collection_name, record).await
        .map_err(|e| anyhow::anyhow!("Failed to upsert: {}", e))?;
    
    // Retrieve and convert back
    if let Some(retrieved) = memory_store.get(collection_name, "prod123").await
        .map_err(|e| anyhow::anyhow!("Failed to get: {}", e))? {
        println!("\n📥 Retrieved from store:");
        println!("   ID: {}", retrieved.id);
        println!("   Text: {}", retrieved.text);
        println!("   Category: {}", retrieved.metadata.source.as_ref().unwrap_or(&"Unknown".to_string()));
        
        // Convert back to static (with validation)
        if let (Some(name), Some(price_str)) = (
            retrieved.metadata.attributes.get("name"),
            retrieved.metadata.attributes.get("price")
        ) {
            if let Ok(price) = price_str.parse::<f64>() {
                println!("\n📦 Converted back to static:");
                println!("   Name: {}", name);
                println!("   Price: ${:.2}", price);
            }
        }
    }
    
    Ok(())
}

/// Create dynamic records based on schema
fn create_dynamic_records(schema: &DynamicSchema) -> Result<Vec<DynamicRecord>> {
    let mut records = Vec::new();
    
    // Sample data
    let data = vec![
        ("1", "Software", "API", "Application Programming Interface. A set of rules..."),
        ("2", "Software", "SDK", "Software development kit. A set of libraries..."),
        ("3", "AI", "LLM", "Large language model. A type of AI algorithm..."),
    ];
    
    for (id, category, term, definition) in data {
        let mut record = DynamicRecord::new();
        record.insert(schema.key_field.clone(), json!(id));
        record.insert(schema.text_field.clone(), json!(definition));
        
        // Add metadata fields based on schema
        for (field_name, _field_type) in &schema.metadata_fields {
            match field_name.as_str() {
                "category" => record.insert(field_name.clone(), json!(category)),
                "term" => record.insert(field_name.clone(), json!(term)),
                "definition" => record.insert(field_name.clone(), json!(definition)),
                _ => None,
            };
        }
        
        records.push(record);
    }
    
    Ok(records)
}

/// Ingest dynamic records into memory store
async fn ingest_dynamic_records(
    memory_store: &InMemoryMemoryStore,
    collection_name: &str,
    records: &[DynamicRecord],
) -> Result<()> {
    for record in records {
        let id = record.get("id")
            .and_then(|v| v.as_str())
            .ok_or_else(|| anyhow::anyhow!("Missing id field"))?;
        
        let text = record.get("text")
            .and_then(|v| v.as_str())
            .ok_or_else(|| anyhow::anyhow!("Missing text field"))?;
        
        let embedding = generate_mock_embedding(text);
        
        let mut memory_record = MemoryRecord::with_embedding(id, text, embedding);
        
        // Add all other fields as metadata
        for (key, value) in record {
            if key != "id" && key != "text" && key != "embedding" {
                if let Some(str_value) = value.as_str() {
                    memory_record = memory_record.with_attribute(key, str_value);
                }
            }
        }
        
        memory_store.upsert(collection_name, memory_record).await
            .map_err(|e| anyhow::anyhow!("Failed to upsert: {}", e))?;
    }
    
    println!("✅ Ingested {} dynamic records", records.len());
    Ok(())
}

/// Search dynamic records
async fn search_dynamic_records(
    memory_store: &InMemoryMemoryStore,
    collection_name: &str,
    query: &str,
) -> Result<Option<(DynamicRecord, f32)>> {
    let search_embedding = generate_mock_embedding(query);
    
    let result = memory_store.get_nearest_match(
        collection_name,
        search_embedding,
        0.0,
        false,
    ).await
        .map_err(|e| anyhow::anyhow!("Failed to search: {}", e))?;
    
    if let Some(search_result) = result {
        let mut dynamic_record = DynamicRecord::new();
        
        // Convert MemoryRecord back to dynamic record
        dynamic_record.insert("id".to_string(), json!(search_result.record.id));
        dynamic_record.insert("text".to_string(), json!(search_result.record.text));
        
        if let Some(source) = &search_result.record.metadata.source {
            dynamic_record.insert("source".to_string(), json!(source));
        }
        
        for (key, value) in &search_result.record.metadata.attributes {
            dynamic_record.insert(key.clone(), json!(value));
        }
        
        Ok(Some((dynamic_record, search_result.score)))
    } else {
        Ok(None)
    }
}

/// Parse schema from JSON configuration
fn parse_schema_from_json(json: &Value) -> Result<DynamicSchema> {
    let mut schema = DynamicSchema::new();
    
    if let Some(key_field) = json.get("key_field").and_then(|v| v.as_str()) {
        schema.key_field = key_field.to_string();
    }
    
    if let Some(text_field) = json.get("text_field").and_then(|v| v.as_str()) {
        schema.text_field = text_field.to_string();
    }
    
    if let Some(embedding_field) = json.get("embedding_field").and_then(|v| v.as_str()) {
        schema.embedding_field = embedding_field.to_string();
    }
    
    if let Some(metadata_fields) = json.get("metadata_fields").and_then(|v| v.as_array()) {
        for field in metadata_fields {
            if let (Some(name), Some(field_type)) = (
                field.get("name").and_then(|v| v.as_str()),
                field.get("type").and_then(|v| v.as_str())
            ) {
                schema.metadata_fields.push((name.to_string(), field_type.to_string()));
            }
        }
    }
    
    Ok(schema)
}

/// Create a document using dynamic schema
fn create_document(
    schema: &DynamicSchema,
    id: &str,
    title: &str,
    content: &str,
    author: &str,
    date: &str,
    tags: Vec<&str>,
    word_count: u32,
) -> DynamicRecord {
    let mut doc = DynamicRecord::new();
    
    doc.insert(schema.key_field.clone(), json!(id));
    doc.insert(schema.text_field.clone(), json!(content));
    doc.insert("title".to_string(), json!(title));
    doc.insert("author".to_string(), json!(author));
    doc.insert("date".to_string(), json!(date));
    doc.insert("tags".to_string(), json!(tags));
    doc.insert("word_count".to_string(), json!(word_count));
    
    doc
}

/// Convert dynamic record to MemoryRecord
fn dynamic_record_to_memory_record(
    schema: &DynamicSchema,
    record: &DynamicRecord,
) -> Result<MemoryRecord> {
    let id = record.get(&schema.key_field)
        .and_then(|v| v.as_str())
        .ok_or_else(|| anyhow::anyhow!("Missing key field"))?;
    
    let text = record.get(&schema.text_field)
        .and_then(|v| v.as_str())
        .ok_or_else(|| anyhow::anyhow!("Missing text field"))?;
    
    let embedding = generate_mock_embedding(text);
    
    let mut memory_record = MemoryRecord::with_embedding(id, text, embedding);
    
    // Add all metadata fields
    for (key, value) in record {
        if key != &schema.key_field && key != &schema.text_field {
            let str_value = match value {
                Value::String(s) => s.clone(),
                Value::Number(n) => n.to_string(),
                Value::Array(arr) => serde_json::to_string(arr)?,
                _ => value.to_string(),
            };
            memory_record = memory_record.with_attribute(key, &str_value);
        }
    }
    
    Ok(memory_record)
}

/// Generate a mock embedding
fn generate_mock_embedding(text: &str) -> Vec<f32> {
    let mut embedding = vec![0.0; 1536];
    let text_lower = text.to_lowercase();
    let keywords = vec!["api", "sdk", "ai", "llm", "ml", "software", "document", "semantic"];
    
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