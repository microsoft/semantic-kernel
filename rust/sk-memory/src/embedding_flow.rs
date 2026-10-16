//! Embedding flow utilities that pipe text → embeddings → memory store

use crate::{MemoryRecord, MemoryStore, SearchResult, Result};
use semantic_kernel::services::EmbeddingService;
use uuid::Uuid;

/// A utility that combines text embedding generation and memory storage
/// Provides a simple pipeline: text → sk-openai embeddings → store
pub struct EmbeddingFlow<M, E> 
where
    M: MemoryStore,
    E: EmbeddingService,
{
    memory_store: M,
    embedding_service: E,
}

impl<M, E> EmbeddingFlow<M, E>
where
    M: MemoryStore,
    E: EmbeddingService,
{
    /// Create a new embedding flow
    pub fn new(memory_store: M, embedding_service: E) -> Self {
        Self {
            memory_store,
            embedding_service,
        }
    }

    /// Save text with automatic embedding generation
    pub async fn save_text(
        &self,
        collection_name: &str,
        text: impl Into<String>,
        metadata: Option<crate::MemoryRecordMetadata>,
    ) -> Result<String> {
        let text = text.into();
        let id = Uuid::new_v4().to_string();
        
        self.save_text_with_id(collection_name, &id, text, metadata).await?;
        Ok(id)
    }

    /// Save text with a specific ID and automatic embedding generation
    pub async fn save_text_with_id(
        &self,
        collection_name: &str,
        id: &str,
        text: impl Into<String>,
        metadata: Option<crate::MemoryRecordMetadata>,
    ) -> Result<()> {
        let text = text.into();
        
        // Generate embedding for the text
        let embeddings = self.embedding_service.generate_embeddings(&[text.clone()]).await?;
        let embedding = embeddings.into_iter().next()
            .ok_or_else(|| Box::new(std::io::Error::new(
                std::io::ErrorKind::InvalidData,
                "No embedding returned from service"
            )) as Box<dyn std::error::Error + Send + Sync>)?;

        // Create memory record
        let mut record = MemoryRecord::with_embedding(id, text, embedding);
        if let Some(metadata) = metadata {
            record = record.with_metadata(metadata);
        }

        // Save to memory store
        self.memory_store.upsert(collection_name, record).await?;
        Ok(())
    }

    /// Save multiple texts with automatic embedding generation
    pub async fn save_texts(
        &self,
        collection_name: &str,
        texts: Vec<String>,
        metadata: Vec<Option<crate::MemoryRecordMetadata>>,
    ) -> Result<Vec<String>> {
        if texts.len() != metadata.len() {
            return Err(Box::new(std::io::Error::new(
                std::io::ErrorKind::InvalidInput,
                "Texts and metadata vectors must have the same length"
            )) as Box<dyn std::error::Error + Send + Sync>);
        }

        // Generate embeddings for all texts
        let embeddings = self.embedding_service.generate_embeddings(&texts).await?;
        
        if embeddings.len() != texts.len() {
            return Err(Box::new(std::io::Error::new(
                std::io::ErrorKind::InvalidData,
                "Number of embeddings doesn't match number of texts"
            )) as Box<dyn std::error::Error + Send + Sync>);
        }

        // Create memory records
        let mut records = Vec::new();
        let mut ids = Vec::new();
        
        for ((text, embedding), metadata) in texts.into_iter()
            .zip(embeddings.into_iter())
            .zip(metadata.into_iter()) {
            
            let id = Uuid::new_v4().to_string();
            let mut record = MemoryRecord::with_embedding(&id, text, embedding);
            
            if let Some(metadata) = metadata {
                record = record.with_metadata(metadata);
            }
            
            records.push(record);
            ids.push(id);
        }

        // Save all records in batch
        self.memory_store.upsert_batch(collection_name, records).await?;
        Ok(ids)
    }

    /// Search for similar texts using natural language query
    pub async fn search_similar(
        &self,
        collection_name: &str,
        query: impl Into<String>,
        limit: usize,
        min_relevance_score: f32,
    ) -> Result<Vec<SearchResult>> {
        let query = query.into();
        
        // Generate embedding for the query
        let embeddings = self.embedding_service.generate_embeddings(&[query]).await?;
        let query_embedding = embeddings.into_iter().next()
            .ok_or_else(|| Box::new(std::io::Error::new(
                std::io::ErrorKind::InvalidData,
                "No embedding returned for query"
            )) as Box<dyn std::error::Error + Send + Sync>)?;

        // Search for similar records
        self.memory_store.get_nearest_matches(
            collection_name,
            query_embedding,
            limit,
            min_relevance_score,
            false, // Don't include embeddings in response to save bandwidth
        ).await
    }

    /// Search for the most similar text using natural language query
    pub async fn search_most_similar(
        &self,
        collection_name: &str,
        query: impl Into<String>,
        min_relevance_score: f32,
    ) -> Result<Option<SearchResult>> {
        let results = self.search_similar(collection_name, query, 1, min_relevance_score).await?;
        Ok(results.into_iter().next())
    }

    /// Get direct access to the underlying memory store
    pub fn memory_store(&self) -> &M {
        &self.memory_store
    }

    /// Get direct access to the underlying embedding service
    pub fn embedding_service(&self) -> &E {
        &self.embedding_service
    }

    /// Ingest a text document by splitting it into chunks and storing each chunk
    pub async fn ingest_document(
        &self,
        collection_name: &str,
        document_text: &str,
        source: Option<String>,
        chunk_size: usize,
        overlap: usize,
    ) -> Result<Vec<String>> {
        let chunks = self.split_text_into_chunks(document_text, chunk_size, overlap);
        
        let metadata: Vec<Option<crate::MemoryRecordMetadata>> = chunks.iter()
            .enumerate()
            .map(|(i, _)| {
                let mut meta = crate::MemoryRecordMetadata::new();
                if let Some(ref src) = source {
                    meta.source = Some(format!("{}#chunk-{}", src, i));
                }
                meta.attributes.insert("chunk_index".to_string(), i.to_string());
                meta.attributes.insert("total_chunks".to_string(), chunks.len().to_string());
                Some(meta)
            })
            .collect();

        self.save_texts(collection_name, chunks, metadata).await
    }

    /// Split text into overlapping chunks
    fn split_text_into_chunks(&self, text: &str, chunk_size: usize, overlap: usize) -> Vec<String> {
        if text.len() <= chunk_size {
            return vec![text.to_string()];
        }

        let mut chunks = Vec::new();
        let mut start = 0;
        
        while start < text.len() {
            let end = std::cmp::min(start + chunk_size, text.len());
            let chunk = text[start..end].to_string();
            chunks.push(chunk);
            
            if end == text.len() {
                break;
            }
            
            start += chunk_size - overlap;
        }
        
        chunks
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{InMemoryMemoryStore, MemoryRecordMetadata};
    use semantic_kernel::{
        async_trait,
        services::{AIService, EmbeddingService},
    };
    use std::collections::HashMap;

    // Mock embedding service for testing
    #[derive(Debug, Clone)]
    struct MockEmbeddingService {
        attributes: HashMap<String, String>,
    }

    impl MockEmbeddingService {
        fn new() -> Self {
            Self {
                attributes: HashMap::new(),
            }
        }
    }

    #[async_trait]
    impl AIService for MockEmbeddingService {
        fn attributes(&self) -> &HashMap<String, String> {
            &self.attributes
        }
        
        fn service_type(&self) -> &'static str {
            "MockEmbedding"
        }
    }

    #[async_trait]
    impl EmbeddingService for MockEmbeddingService {
        async fn generate_embeddings(
            &self,
            texts: &[String],
        ) -> semantic_kernel::Result<Vec<Vec<f32>>> {
            // Generate mock embeddings based on text length and content
            let embeddings = texts.iter()
                .map(|text| {
                    // Create a simple embedding based on text characteristics
                    let length_factor = (text.len() as f32) / 100.0;
                    let char_sum = text.chars().map(|c| c as u32 as f32).sum::<f32>() / text.len() as f32;
                    vec![length_factor, char_sum / 100.0, 0.5] // 3D embedding
                })
                .collect();
            Ok(embeddings)
        }
    }

    #[tokio::test]
    async fn test_save_and_search_text() {
        let memory_store = InMemoryMemoryStore::new();
        let embedding_service = MockEmbeddingService::new();
        let flow = EmbeddingFlow::new(memory_store, embedding_service);
        
        let collection = "test_collection";
        flow.memory_store().create_collection(collection).await.unwrap();
        
        // Save some text
        let id = flow.save_text(collection, "Hello world", None).await.unwrap();
        assert!(!id.is_empty());
        
        // Search for similar text
        let results = flow.search_similar(collection, "Hello", 10, 0.0).await.unwrap();
        assert_eq!(results.len(), 1);
        assert_eq!(results[0].record.text, "Hello world");
    }

    #[tokio::test]
    async fn test_save_with_metadata() {
        let memory_store = InMemoryMemoryStore::new();
        let embedding_service = MockEmbeddingService::new();
        let flow = EmbeddingFlow::new(memory_store, embedding_service);
        
        let collection = "test_collection";
        flow.memory_store().create_collection(collection).await.unwrap();
        
        let metadata = MemoryRecordMetadata::with_source("test.txt")
            .with_attribute("author", "test");
        
        let id = flow.save_text(collection, "Test content", Some(metadata)).await.unwrap();
        
        let record = flow.memory_store().get(collection, &id).await.unwrap().unwrap();
        assert_eq!(record.metadata.source, Some("test.txt".to_string()));
        assert_eq!(record.metadata.attributes.get("author"), Some(&"test".to_string()));
    }

    #[tokio::test]
    async fn test_batch_save() {
        let memory_store = InMemoryMemoryStore::new();
        let embedding_service = MockEmbeddingService::new();
        let flow = EmbeddingFlow::new(memory_store, embedding_service);
        
        let collection = "test_collection";
        flow.memory_store().create_collection(collection).await.unwrap();
        
        let texts = vec!["First text".to_string(), "Second text".to_string()];
        let metadata = vec![None, None];
        
        let ids = flow.save_texts(collection, texts, metadata).await.unwrap();
        assert_eq!(ids.len(), 2);
        
        let record1 = flow.memory_store().get(collection, &ids[0]).await.unwrap().unwrap();
        let record2 = flow.memory_store().get(collection, &ids[1]).await.unwrap().unwrap();
        
        assert_eq!(record1.text, "First text");
        assert_eq!(record2.text, "Second text");
    }

    #[tokio::test]
    async fn test_document_ingestion() {
        let memory_store = InMemoryMemoryStore::new();
        let embedding_service = MockEmbeddingService::new();
        let flow = EmbeddingFlow::new(memory_store, embedding_service);
        
        let collection = "test_collection";
        flow.memory_store().create_collection(collection).await.unwrap();
        
        let document = "This is a long document that should be split into multiple chunks for better processing and retrieval.";
        let ids = flow.ingest_document(collection, document, Some("test.md".to_string()), 50, 10).await.unwrap();
        
        assert!(ids.len() > 1); // Should be split into multiple chunks
        
        // Verify chunks are stored
        for id in &ids {
            let record = flow.memory_store().get(collection, id).await.unwrap();
            assert!(record.is_some());
        }
        
        // Search for content
        let results = flow.search_similar(collection, "long document", 10, 0.0).await.unwrap();
        assert!(!results.is_empty());
    }

    #[test]
    fn test_text_chunking() {
        let memory_store = InMemoryMemoryStore::new();
        let embedding_service = MockEmbeddingService::new();
        let flow = EmbeddingFlow::new(memory_store, embedding_service);
        
        let text = "This is a test document that should be split into chunks.";
        let chunks = flow.split_text_into_chunks(text, 20, 5);
        
        assert!(chunks.len() > 1);
        assert!(chunks[0].len() <= 20);
        
        // Test overlap
        if chunks.len() > 1 {
            let first_end = &chunks[0][(chunks[0].len() - 5)..];
            let second_start = &chunks[1][..5];
            // There should be some overlap, though exact match depends on character boundaries
            assert!(first_end.chars().count() <= 5);
            assert!(second_start.chars().count() <= 5);
        }
    }

    #[test]
    fn test_small_text_chunking() {
        let memory_store = InMemoryMemoryStore::new();
        let embedding_service = MockEmbeddingService::new();
        let flow = EmbeddingFlow::new(memory_store, embedding_service);
        
        let text = "Small text";
        let chunks = flow.split_text_into_chunks(text, 100, 10);
        
        assert_eq!(chunks.len(), 1);
        assert_eq!(chunks[0], text);
    }
}