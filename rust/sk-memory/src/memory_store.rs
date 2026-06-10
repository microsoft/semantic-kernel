//! Memory store trait and search functionality

use crate::{MemoryRecord, Result};
use serde::{Deserialize, Serialize};

/// Trait for memory storage operations with async CRUD support
#[semantic_kernel::async_trait]
pub trait MemoryStore: Send + Sync {
    /// Create a new collection/index in the memory store
    async fn create_collection(&self, collection_name: &str) -> Result<()>;

    /// Delete a collection/index from the memory store
    async fn delete_collection(&self, collection_name: &str) -> Result<()>;

    /// Check if a collection exists
    async fn collection_exists(&self, collection_name: &str) -> Result<bool>;

    /// List all collections in the store
    async fn get_collections(&self) -> Result<Vec<String>>;

    /// Upsert (insert or update) a memory record
    async fn upsert(&self, collection_name: &str, record: MemoryRecord) -> Result<()>;

    /// Upsert multiple memory records in batch
    async fn upsert_batch(&self, collection_name: &str, records: Vec<MemoryRecord>) -> Result<()>;

    /// Get a memory record by its ID
    async fn get(&self, collection_name: &str, id: &str) -> Result<Option<MemoryRecord>>;

    /// Get multiple memory records by their IDs
    async fn get_batch(&self, collection_name: &str, ids: Vec<String>) -> Result<Vec<MemoryRecord>>;

    /// Delete a memory record by its ID
    async fn remove(&self, collection_name: &str, id: &str) -> Result<()>;

    /// Delete multiple memory records by their IDs
    async fn remove_batch(&self, collection_name: &str, ids: Vec<String>) -> Result<()>;

    /// Search for similar memory records using vector similarity
    async fn get_nearest_matches(
        &self,
        collection_name: &str,
        embedding: Vec<f32>,
        limit: usize,
        min_relevance_score: f32,
        with_embeddings: bool,
    ) -> Result<Vec<SearchResult>>;

    /// Search for similar memory records and return only the nearest match
    async fn get_nearest_match(
        &self,
        collection_name: &str,
        embedding: Vec<f32>,
        min_relevance_score: f32,
        with_embeddings: bool,
    ) -> Result<Option<SearchResult>> {
        let results = self.get_nearest_matches(
            collection_name,
            embedding,
            1,
            min_relevance_score,
            with_embeddings,
        ).await?;
        Ok(results.into_iter().next())
    }
}

/// A search result containing a memory record and its relevance score
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchResult {
    /// The memory record that matched the search
    pub record: MemoryRecord,
    /// Relevance score (typically cosine similarity between 0.0 and 1.0)
    pub score: f32,
}

impl SearchResult {
    /// Create a new search result
    pub fn new(record: MemoryRecord, score: f32) -> Self {
        Self { record, score }
    }

    /// Check if this result meets a minimum relevance threshold
    pub fn meets_threshold(&self, min_score: f32) -> bool {
        self.score >= min_score
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::MemoryRecordMetadata;

    #[test]
    fn test_search_result_creation() {
        let record = MemoryRecord::new("test-id", "test content");
        let result = SearchResult::new(record.clone(), 0.85);
        
        assert_eq!(result.record.id, "test-id");
        assert_eq!(result.score, 0.85);
    }

    #[test]
    fn test_search_result_meets_threshold() {
        let record = MemoryRecord::new("test-id", "test content");
        let result = SearchResult::new(record, 0.85);
        
        assert!(result.meets_threshold(0.8));
        assert!(result.meets_threshold(0.85));
        assert!(!result.meets_threshold(0.9));
    }
}