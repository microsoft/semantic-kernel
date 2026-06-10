//! In-memory implementation of the MemoryStore trait

use crate::{MemoryRecord, MemoryStore, SearchResult, Result};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;

/// In-memory implementation of MemoryStore using HashMap
/// This implementation is suitable for development, testing, and small-scale applications
#[derive(Debug, Clone)]
pub struct InMemoryMemoryStore {
    /// Collections stored as nested HashMaps: collection_name -> record_id -> record
    collections: Arc<RwLock<HashMap<String, HashMap<String, MemoryRecord>>>>,
}

impl InMemoryMemoryStore {
    /// Create a new in-memory memory store
    pub fn new() -> Self {
        Self {
            collections: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    /// Get the total number of records across all collections
    pub async fn total_records(&self) -> usize {
        let collections = self.collections.read().await;
        collections.values().map(|c| c.len()).sum()
    }

    /// Get the number of records in a specific collection
    pub async fn collection_size(&self, collection_name: &str) -> usize {
        let collections = self.collections.read().await;
        collections.get(collection_name).map_or(0, |c| c.len())
    }
}

impl Default for InMemoryMemoryStore {
    fn default() -> Self {
        Self::new()
    }
}

#[semantic_kernel::async_trait]
impl MemoryStore for InMemoryMemoryStore {
    async fn create_collection(&self, collection_name: &str) -> Result<()> {
        let mut collections = self.collections.write().await;
        collections.insert(collection_name.to_string(), HashMap::new());
        Ok(())
    }

    async fn delete_collection(&self, collection_name: &str) -> Result<()> {
        let mut collections = self.collections.write().await;
        collections.remove(collection_name);
        Ok(())
    }

    async fn collection_exists(&self, collection_name: &str) -> Result<bool> {
        let collections = self.collections.read().await;
        Ok(collections.contains_key(collection_name))
    }

    async fn get_collections(&self) -> Result<Vec<String>> {
        let collections = self.collections.read().await;
        Ok(collections.keys().cloned().collect())
    }

    async fn upsert(&self, collection_name: &str, record: MemoryRecord) -> Result<()> {
        let mut collections = self.collections.write().await;
        let collection = collections
            .entry(collection_name.to_string())
            .or_insert_with(HashMap::new);
        
        collection.insert(record.id.clone(), record);
        Ok(())
    }

    async fn upsert_batch(&self, collection_name: &str, records: Vec<MemoryRecord>) -> Result<()> {
        let mut collections = self.collections.write().await;
        let collection = collections
            .entry(collection_name.to_string())
            .or_insert_with(HashMap::new);

        for record in records {
            collection.insert(record.id.clone(), record);
        }
        Ok(())
    }

    async fn get(&self, collection_name: &str, id: &str) -> Result<Option<MemoryRecord>> {
        let collections = self.collections.read().await;
        Ok(collections
            .get(collection_name)
            .and_then(|collection| collection.get(id))
            .cloned())
    }

    async fn get_batch(&self, collection_name: &str, ids: Vec<String>) -> Result<Vec<MemoryRecord>> {
        let collections = self.collections.read().await;
        let collection = collections.get(collection_name);
        
        if let Some(collection) = collection {
            let records = ids
                .into_iter()
                .filter_map(|id| collection.get(&id).cloned())
                .collect();
            Ok(records)
        } else {
            Ok(Vec::new())
        }
    }

    async fn remove(&self, collection_name: &str, id: &str) -> Result<()> {
        let mut collections = self.collections.write().await;
        if let Some(collection) = collections.get_mut(collection_name) {
            collection.remove(id);
        }
        Ok(())
    }

    async fn remove_batch(&self, collection_name: &str, ids: Vec<String>) -> Result<()> {
        let mut collections = self.collections.write().await;
        if let Some(collection) = collections.get_mut(collection_name) {
            for id in ids {
                collection.remove(&id);
            }
        }
        Ok(())
    }

    async fn get_nearest_matches(
        &self,
        collection_name: &str,
        embedding: Vec<f32>,
        limit: usize,
        min_relevance_score: f32,
        with_embeddings: bool,
    ) -> Result<Vec<SearchResult>> {
        let collections = self.collections.read().await;
        let collection = collections.get(collection_name);

        if let Some(collection) = collection {
            let mut results: Vec<SearchResult> = Vec::new();

            // Calculate similarity scores for all records
            for record in collection.values() {
                if let Some(similarity) = record.cosine_similarity(&embedding) {
                    // Convert cosine similarity (-1 to 1) to relevance score (0 to 1)
                    let relevance_score = (similarity + 1.0) / 2.0;
                    
                    if relevance_score >= min_relevance_score {
                        let mut result_record = record.clone();
                        
                        // Optionally remove embeddings to reduce response size
                        if !with_embeddings {
                            result_record.embedding = None;
                        }
                        
                        results.push(SearchResult::new(result_record, relevance_score));
                    }
                }
            }

            // Sort by relevance score in descending order
            results.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap_or(std::cmp::Ordering::Equal));
            
            // Limit the number of results
            results.truncate(limit);
            
            Ok(results)
        } else {
            Ok(Vec::new())
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::MemoryRecordMetadata;

    #[tokio::test]
    async fn test_create_and_list_collections() {
        let store = InMemoryMemoryStore::new();
        
        // Initially no collections
        assert!(store.get_collections().await.unwrap().is_empty());
        
        // Create collections
        store.create_collection("test1").await.unwrap();
        store.create_collection("test2").await.unwrap();
        
        let collections = store.get_collections().await.unwrap();
        assert_eq!(collections.len(), 2);
        assert!(collections.contains(&"test1".to_string()));
        assert!(collections.contains(&"test2".to_string()));
    }

    #[tokio::test]
    async fn test_collection_exists() {
        let store = InMemoryMemoryStore::new();
        
        assert!(!store.collection_exists("test").await.unwrap());
        
        store.create_collection("test").await.unwrap();
        assert!(store.collection_exists("test").await.unwrap());
        
        store.delete_collection("test").await.unwrap();
        assert!(!store.collection_exists("test").await.unwrap());
    }

    #[tokio::test]
    async fn test_upsert_and_get() {
        let store = InMemoryMemoryStore::new();
        store.create_collection("test").await.unwrap();
        
        let record = MemoryRecord::new("test-id", "test content")
            .with_source("test.txt");
            
        // Upsert record
        store.upsert("test", record.clone()).await.unwrap();
        
        // Get record back
        let retrieved = store.get("test", "test-id").await.unwrap();
        assert!(retrieved.is_some());
        let retrieved = retrieved.unwrap();
        assert_eq!(retrieved.id, "test-id");
        assert_eq!(retrieved.text, "test content");
        assert_eq!(retrieved.metadata.source, Some("test.txt".to_string()));
    }

    #[tokio::test]
    async fn test_get_nonexistent() {
        let store = InMemoryMemoryStore::new();
        store.create_collection("test").await.unwrap();
        
        let result = store.get("test", "nonexistent").await.unwrap();
        assert!(result.is_none());
        
        let result = store.get("nonexistent_collection", "test-id").await.unwrap();
        assert!(result.is_none());
    }

    #[tokio::test]
    async fn test_batch_operations() {
        let store = InMemoryMemoryStore::new();
        store.create_collection("test").await.unwrap();
        
        let records = vec![
            MemoryRecord::new("id1", "content 1"),
            MemoryRecord::new("id2", "content 2"),
            MemoryRecord::new("id3", "content 3"),
        ];
        
        // Batch upsert
        store.upsert_batch("test", records).await.unwrap();
        
        // Batch get
        let retrieved = store.get_batch("test", vec!["id1".to_string(), "id3".to_string()]).await.unwrap();
        assert_eq!(retrieved.len(), 2);
        assert!(retrieved.iter().any(|r| r.id == "id1"));
        assert!(retrieved.iter().any(|r| r.id == "id3"));
        
        // Batch remove
        store.remove_batch("test", vec!["id1".to_string(), "id2".to_string()]).await.unwrap();
        
        let remaining = store.get("test", "id3").await.unwrap();
        assert!(remaining.is_some());
        
        let removed = store.get("test", "id1").await.unwrap();
        assert!(removed.is_none());
    }

    #[tokio::test]
    async fn test_nearest_matches() {
        let store = InMemoryMemoryStore::new();
        store.create_collection("test").await.unwrap();
        
        // Create records with different embeddings
        let record1 = MemoryRecord::with_embedding("id1", "content 1", vec![1.0, 0.0, 0.0]);
        let record2 = MemoryRecord::with_embedding("id2", "content 2", vec![0.0, 1.0, 0.0]);
        let record3 = MemoryRecord::with_embedding("id3", "content 3", vec![0.5, 0.5, 0.0]);
        
        store.upsert_batch("test", vec![record1, record2, record3]).await.unwrap();
        
        // Search for similarity to [1.0, 0.0, 0.0] (should match record1 best)
        let query_embedding = vec![1.0, 0.0, 0.0];
        let results = store.get_nearest_matches("test", query_embedding, 3, 0.0, true).await.unwrap();
        
        assert_eq!(results.len(), 3);
        assert_eq!(results[0].record.id, "id1"); // Best match
        assert!(results[0].score > results[1].score); // Score should be highest
    }

    #[tokio::test]
    async fn test_nearest_matches_with_threshold() {
        let store = InMemoryMemoryStore::new();
        store.create_collection("test").await.unwrap();
        
        let record1 = MemoryRecord::with_embedding("id1", "content 1", vec![1.0, 0.0]);
        let record2 = MemoryRecord::with_embedding("id2", "content 2", vec![-1.0, 0.0]);
        
        store.upsert_batch("test", vec![record1, record2]).await.unwrap();
        
        // Search with high threshold - should only return the similar one
        let query_embedding = vec![1.0, 0.0];
        let results = store.get_nearest_matches("test", query_embedding, 10, 0.8, true).await.unwrap();
        
        assert_eq!(results.len(), 1);
        assert_eq!(results[0].record.id, "id1");
    }

    #[tokio::test]
    async fn test_store_statistics() {
        let store = InMemoryMemoryStore::new();
        
        assert_eq!(store.total_records().await, 0);
        assert_eq!(store.collection_size("test").await, 0);
        
        store.create_collection("test1").await.unwrap();
        store.create_collection("test2").await.unwrap();
        
        store.upsert("test1", MemoryRecord::new("id1", "content 1")).await.unwrap();
        store.upsert("test1", MemoryRecord::new("id2", "content 2")).await.unwrap();
        store.upsert("test2", MemoryRecord::new("id3", "content 3")).await.unwrap();
        
        assert_eq!(store.total_records().await, 3);
        assert_eq!(store.collection_size("test1").await, 2);
        assert_eq!(store.collection_size("test2").await, 1);
        assert_eq!(store.collection_size("nonexistent").await, 0);
    }
}