//! Qdrant implementation of the MemoryStore trait

use crate::{MemoryRecord, MemoryStore, SearchResult, Result};
use qdrant_client::{
    qdrant::{
        CreateCollectionBuilder, Distance, VectorParamsBuilder,
        PointStruct, SearchPointsBuilder, UpsertPointsBuilder, 
        PointId, DeletePointsBuilder, PointsIdsList,
        ScoredPoint, RetrievedPoint, GetPointsBuilder,
    },
    Qdrant, Payload,
};
use serde_json::{json, Value};
use std::collections::HashMap;

/// Qdrant implementation of MemoryStore
/// Provides vector similarity search using the Qdrant vector database
#[derive(Clone)]
pub struct QdrantMemoryStore {
    /// Qdrant client
    client: Qdrant,
    /// Vector dimension (must be consistent across all embeddings)
    vector_dimension: u64,
}

impl QdrantMemoryStore {
    /// Create a new Qdrant memory store
    pub async fn new(url: impl Into<String>) -> Result<Self> {
        let client = Qdrant::from_url(&url.into()).build()?;
        
        Ok(Self {
            client,
            vector_dimension: 1536, // Default to OpenAI embedding size
        })
    }

    /// Create a new Qdrant memory store with API key authentication
    pub async fn with_api_key(
        url: impl Into<String>,
        api_key: impl Into<String>,
    ) -> Result<Self> {
        let client = Qdrant::from_url(&url.into())
            .api_key(api_key.into())
            .build()?;
        
        Ok(Self {
            client,
            vector_dimension: 1536, // Default to OpenAI embedding size
        })
    }

    /// Set the vector dimension
    pub fn with_dimension(mut self, dimension: u64) -> Self {
        self.vector_dimension = dimension;
        self
    }

    /// Convert MemoryRecord to Qdrant PointStruct
    fn memory_record_to_point(&self, record: &MemoryRecord) -> Result<PointStruct> {
        let embedding = record.embedding.as_ref()
            .ok_or_else(|| Box::new(std::io::Error::new(
                std::io::ErrorKind::InvalidData,
                "Memory record missing embedding"
            )) as Box<dyn std::error::Error + Send + Sync>)?;

        let mut payload = Payload::new();
        payload.insert("text", Value::String(record.text.clone()));
        
        if let Some(source) = &record.metadata.source {
            payload.insert("source", Value::String(source.clone()));
        }
        
        if let Some(description) = &record.metadata.description {
            payload.insert("description", Value::String(description.clone()));
        }
        
        if !record.metadata.tags.is_empty() {
            payload.insert("tags", json!(record.metadata.tags));
        }
        
        if !record.metadata.attributes.is_empty() {
            for (key, value) in &record.metadata.attributes {
                payload.insert(key, Value::String(value.clone()));
            }
        }
        
        if let Some(timestamp) = record.timestamp {
            payload.insert("timestamp", json!(timestamp));
        }

        Ok(PointStruct::new(
            record.id.clone(),
            embedding.clone(),
            payload,
        ))
    }

    /// Convert Qdrant scored point to MemoryRecord
    fn scored_point_to_memory_record(&self, point: &ScoredPoint, with_embedding: bool) -> Result<MemoryRecord> {
        let id = match &point.id {
            Some(point_id) => match &point_id.point_id_options {
                Some(qdrant_client::qdrant::point_id::PointIdOptions::Uuid(uuid)) => uuid.clone(),
                Some(qdrant_client::qdrant::point_id::PointIdOptions::Num(num)) => num.to_string(),
                None => return Err(Box::new(std::io::Error::new(
                    std::io::ErrorKind::InvalidData,
                    "Point missing ID"
                )) as Box<dyn std::error::Error + Send + Sync>),
            },
            None => return Err(Box::new(std::io::Error::new(
                std::io::ErrorKind::InvalidData,
                "Point missing ID"
            )) as Box<dyn std::error::Error + Send + Sync>),
        };

        let payload = &point.payload;
        
        let text = payload.get("text")
            .and_then(|v| v.as_str())
            .map(|s| s.to_string())
            .unwrap_or_default();

        let source = payload.get("source")
            .and_then(|v| v.as_str())
            .map(|s| s.to_string());

        let description = payload.get("description")
            .and_then(|v| v.as_str())
            .map(|s| s.to_string());

        let tags = payload.get("tags")
            .and_then(|v| v.as_list())
            .map(|list| list.iter()
                .filter_map(|v| v.as_str())
                .map(|s| s.to_string())
                .collect())
            .unwrap_or_default();

        let mut attributes = HashMap::new();
        for (key, value) in payload {
            if key != "text" && key != "source" && key != "description" && key != "tags" && key != "timestamp" {
                if let Some(str_value) = value.as_str() {
                    attributes.insert(key.clone(), str_value.to_string());
                }
            }
        }

        let timestamp = payload.get("timestamp")
            .and_then(|v| v.as_integer())
            .map(|i| i as u64);

        let embedding = if with_embedding && !point.vectors.is_none() {
            // Extract embedding from vectors
            None // Simplified for now - vectors field structure is complex
        } else {
            None
        };

        let mut record = MemoryRecord::new(id, text);
        record.metadata.source = source;
        record.metadata.description = description;
        record.metadata.tags = tags;
        record.metadata.attributes = attributes;
        record.timestamp = timestamp;
        record.embedding = embedding;

        Ok(record)
    }

    /// Convert Qdrant retrieved point to MemoryRecord
    fn retrieved_point_to_memory_record(&self, point: &RetrievedPoint, with_embedding: bool) -> Result<MemoryRecord> {
        let id = match &point.id {
            Some(point_id) => match &point_id.point_id_options {
                Some(qdrant_client::qdrant::point_id::PointIdOptions::Uuid(uuid)) => uuid.clone(),
                Some(qdrant_client::qdrant::point_id::PointIdOptions::Num(num)) => num.to_string(),
                None => return Err(Box::new(std::io::Error::new(
                    std::io::ErrorKind::InvalidData,
                    "Point missing ID"
                )) as Box<dyn std::error::Error + Send + Sync>),
            },
            None => return Err(Box::new(std::io::Error::new(
                std::io::ErrorKind::InvalidData,
                "Point missing ID"
            )) as Box<dyn std::error::Error + Send + Sync>),
        };

        let payload = &point.payload;
        
        let text = payload.get("text")
            .and_then(|v| v.as_str())
            .map(|s| s.to_string())
            .unwrap_or_default();

        let source = payload.get("source")
            .and_then(|v| v.as_str())
            .map(|s| s.to_string());

        let description = payload.get("description")
            .and_then(|v| v.as_str())
            .map(|s| s.to_string());

        let tags = payload.get("tags")
            .and_then(|v| v.as_list())
            .map(|list| list.iter()
                .filter_map(|v| v.as_str())
                .map(|s| s.to_string())
                .collect())
            .unwrap_or_default();

        let mut attributes = HashMap::new();
        for (key, value) in payload {
            if key != "text" && key != "source" && key != "description" && key != "tags" && key != "timestamp" {
                if let Some(str_value) = value.as_str() {
                    attributes.insert(key.clone(), str_value.to_string());
                }
            }
        }

        let timestamp = payload.get("timestamp")
            .and_then(|v| v.as_integer())
            .map(|i| i as u64);

        let embedding = if with_embedding && !point.vectors.is_none() {
            // Extract embedding from vectors
            None // Simplified for now - vectors field structure is complex
        } else {
            None
        };

        let mut record = MemoryRecord::new(id, text);
        record.metadata.source = source;
        record.metadata.description = description;
        record.metadata.tags = tags;
        record.metadata.attributes = attributes;
        record.timestamp = timestamp;
        record.embedding = embedding;

        Ok(record)
    }
}

#[semantic_kernel::async_trait]
impl MemoryStore for QdrantMemoryStore {
    async fn create_collection(&self, collection_name: &str) -> Result<()> {
        self.client
            .create_collection(
                CreateCollectionBuilder::new(collection_name)
                    .vectors_config(VectorParamsBuilder::new(self.vector_dimension, Distance::Cosine))
            )
            .await?;
        Ok(())
    }

    async fn delete_collection(&self, collection_name: &str) -> Result<()> {
        self.client.delete_collection(collection_name).await?;
        Ok(())
    }

    async fn collection_exists(&self, collection_name: &str) -> Result<bool> {
        match self.client.collection_info(collection_name).await {
            Ok(_) => Ok(true),
            Err(_) => Ok(false),
        }
    }

    async fn get_collections(&self) -> Result<Vec<String>> {
        let response = self.client.list_collections().await?;
        Ok(response.collections.into_iter()
            .map(|c| c.name)
            .collect())
    }

    async fn upsert(&self, collection_name: &str, record: MemoryRecord) -> Result<()> {
        let point = self.memory_record_to_point(&record)?;
        
        self.client
            .upsert_points(
                UpsertPointsBuilder::new(collection_name, vec![point])
            )
            .await?;
        Ok(())
    }

    async fn upsert_batch(&self, collection_name: &str, records: Vec<MemoryRecord>) -> Result<()> {
        let points: Result<Vec<_>> = records.iter()
            .map(|record| self.memory_record_to_point(record))
            .collect();
        
        self.client
            .upsert_points(
                UpsertPointsBuilder::new(collection_name, points?)
            )
            .await?;
        Ok(())
    }

    async fn get(&self, collection_name: &str, id: &str) -> Result<Option<MemoryRecord>> {
        let points = self.client
            .get_points(
                GetPointsBuilder::new(collection_name, vec![PointId::from(id.to_string())])
                    .with_payload(true)
                    .with_vectors(false)
            )
            .await?;

        if let Some(point) = points.result.into_iter().next() {
            let record = self.retrieved_point_to_memory_record(&point, false)?;
            Ok(Some(record))
        } else {
            Ok(None)
        }
    }

    async fn get_batch(&self, collection_name: &str, ids: Vec<String>) -> Result<Vec<MemoryRecord>> {
        let point_ids: Vec<PointId> = ids.into_iter()
            .map(PointId::from)
            .collect();

        let points = self.client
            .get_points(
                GetPointsBuilder::new(collection_name, point_ids)
                    .with_payload(true)
                    .with_vectors(false)
            )
            .await?;

        let mut records = Vec::new();
        for point in points.result {
            let record = self.retrieved_point_to_memory_record(&point, false)?;
            records.push(record);
        }

        Ok(records)
    }

    async fn remove(&self, collection_name: &str, id: &str) -> Result<()> {
        self.client
            .delete_points(
                DeletePointsBuilder::new(collection_name)
                    .points(PointsIdsList {
                        ids: vec![PointId::from(id.to_string())],
                    })
            )
            .await?;
        Ok(())
    }

    async fn remove_batch(&self, collection_name: &str, ids: Vec<String>) -> Result<()> {
        let point_ids: Vec<PointId> = ids.into_iter()
            .map(PointId::from)
            .collect();

        self.client
            .delete_points(
                DeletePointsBuilder::new(collection_name)
                    .points(PointsIdsList {
                        ids: point_ids,
                    })
            )
            .await?;
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
        let response = self.client
            .search_points(
                SearchPointsBuilder::new(collection_name, embedding, limit as u64)
                    .with_payload(true)
                    .with_vectors(with_embeddings)
                    .score_threshold(min_relevance_score)
            )
            .await?;

        let mut results = Vec::new();
        for scored_point in response.result {
            let record = self.scored_point_to_memory_record(&scored_point, with_embeddings)?;
            results.push(SearchResult {
                record,
                score: scored_point.score,
            });
        }

        Ok(results)
    }

    async fn get_nearest_match(
        &self,
        collection_name: &str,
        embedding: Vec<f32>,
        min_relevance_score: f32,
        with_embedding: bool,
    ) -> Result<Option<SearchResult>> {
        let matches = self.get_nearest_matches(
            collection_name,
            embedding,
            1,
            min_relevance_score,
            with_embedding,
        ).await?;

        Ok(matches.into_iter().next())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_qdrant_memory_store() {
        // This test requires a running Qdrant instance
        // Skip if not available
        let store = match QdrantMemoryStore::new("http://localhost:6333").await {
            Ok(store) => store,
            Err(_) => {
                eprintln!("Skipping Qdrant tests - no server available");
                return;
            }
        };

        let collection_name = "test_collection";
        
        // Clean up any existing collection
        let _ = store.delete_collection(collection_name).await;

        // Create collection
        store.create_collection(collection_name).await.unwrap();
        
        // Check it exists
        assert!(store.collection_exists(collection_name).await.unwrap());

        // Create a test record
        let record = MemoryRecord::with_embedding(
            "test_id",
            "This is test content",
            vec![0.1; 1536], // Mock embedding
        )
        .with_source("test_source")
        .with_description("Test Description");

        // Upsert the record
        store.upsert(collection_name, record.clone()).await.unwrap();

        // Get the record back
        let retrieved = store.get(collection_name, "test_id").await.unwrap();
        assert!(retrieved.is_some());
        
        let retrieved_record = retrieved.unwrap();
        assert_eq!(retrieved_record.id, "test_id");
        assert_eq!(retrieved_record.text, "This is test content");

        // Clean up
        store.delete_collection(collection_name).await.unwrap();
    }
}