//! Memory record data structures

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// A memory record containing text, embeddings, and metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryRecord {
    /// Unique identifier for the memory record
    pub id: String,
    /// The original text content
    pub text: String,
    /// Additional metadata about the record
    pub metadata: MemoryRecordMetadata,
    /// The embedding vector for the text
    pub embedding: Option<Vec<f32>>,
    /// Timestamp when the record was created (Unix timestamp)
    pub timestamp: Option<u64>,
}

/// Metadata associated with a memory record
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryRecordMetadata {
    /// Source information (e.g., filename, URL)
    pub source: Option<String>,
    /// Additional tags for categorization
    pub tags: Vec<String>,
    /// Custom attributes as key-value pairs
    pub attributes: HashMap<String, String>,
    /// Description of the content
    pub description: Option<String>,
}

impl MemoryRecord {
    /// Create a new memory record
    pub fn new(
        id: impl Into<String>,
        text: impl Into<String>,
    ) -> Self {
        Self {
            id: id.into(),
            text: text.into(),
            metadata: MemoryRecordMetadata::default(),
            embedding: None,
            timestamp: Some(std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap_or_default()
                .as_secs()),
        }
    }

    /// Create a new memory record with embedding
    pub fn with_embedding(
        id: impl Into<String>,
        text: impl Into<String>,
        embedding: Vec<f32>,
    ) -> Self {
        let mut record = Self::new(id, text);
        record.embedding = Some(embedding);
        record
    }

    /// Set the metadata for this record
    pub fn with_metadata(mut self, metadata: MemoryRecordMetadata) -> Self {
        self.metadata = metadata;
        self
    }

    /// Set the source metadata
    pub fn with_source(mut self, source: impl Into<String>) -> Self {
        self.metadata.source = Some(source.into());
        self
    }

    /// Add a tag to the metadata
    pub fn with_tag(mut self, tag: impl Into<String>) -> Self {
        self.metadata.tags.push(tag.into());
        self
    }

    /// Add a custom attribute
    pub fn with_attribute(mut self, key: impl Into<String>, value: impl Into<String>) -> Self {
        self.metadata.attributes.insert(key.into(), value.into());
        self
    }

    /// Set the description
    pub fn with_description(mut self, description: impl Into<String>) -> Self {
        self.metadata.description = Some(description.into());
        self
    }

    /// Get the relevance score based on cosine similarity
    /// Returns a score between -1.0 and 1.0, where 1.0 is most similar
    pub fn cosine_similarity(&self, other_embedding: &[f32]) -> Option<f32> {
        let embedding = self.embedding.as_ref()?;
        if embedding.len() != other_embedding.len() {
            return None;
        }

        let dot_product: f32 = embedding.iter()
            .zip(other_embedding.iter())
            .map(|(a, b)| a * b)
            .sum();

        let norm_a: f32 = embedding.iter().map(|x| x * x).sum::<f32>().sqrt();
        let norm_b: f32 = other_embedding.iter().map(|x| x * x).sum::<f32>().sqrt();

        if norm_a == 0.0 || norm_b == 0.0 {
            Some(0.0)
        } else {
            Some(dot_product / (norm_a * norm_b))
        }
    }
}

impl MemoryRecordMetadata {
    /// Create new empty metadata
    pub fn new() -> Self {
        Self {
            source: None,
            tags: Vec::new(),
            attributes: HashMap::new(),
            description: None,
        }
    }

    /// Create metadata with a source
    pub fn with_source(source: impl Into<String>) -> Self {
        Self {
            source: Some(source.into()),
            tags: Vec::new(),
            attributes: HashMap::new(),
            description: None,
        }
    }

    /// Add a custom attribute
    pub fn with_attribute(mut self, key: impl Into<String>, value: impl Into<String>) -> Self {
        self.attributes.insert(key.into(), value.into());
        self
    }
}

impl Default for MemoryRecordMetadata {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_memory_record_creation() {
        let record = MemoryRecord::new("test-id", "test content");
        assert_eq!(record.id, "test-id");
        assert_eq!(record.text, "test content");
        assert!(record.embedding.is_none());
        assert!(record.timestamp.is_some());
    }

    #[test]
    fn test_memory_record_with_embedding() {
        let embedding = vec![0.1, 0.2, 0.3];
        let record = MemoryRecord::with_embedding("test-id", "test content", embedding.clone());
        assert_eq!(record.id, "test-id");
        assert_eq!(record.text, "test content");
        assert_eq!(record.embedding, Some(embedding));
    }

    #[test]
    fn test_memory_record_builder() {
        let record = MemoryRecord::new("test-id", "test content")
            .with_source("test.txt")
            .with_tag("tag1")
            .with_tag("tag2")
            .with_attribute("key1", "value1")
            .with_description("Test description");

        assert_eq!(record.metadata.source, Some("test.txt".to_string()));
        assert_eq!(record.metadata.tags, vec!["tag1", "tag2"]);
        assert_eq!(record.metadata.attributes.get("key1"), Some(&"value1".to_string()));
        assert_eq!(record.metadata.description, Some("Test description".to_string()));
    }

    #[test]
    fn test_cosine_similarity() {
        let embedding1 = vec![1.0, 0.0, 0.0];
        let embedding2 = vec![1.0, 0.0, 0.0]; // Identical
        let embedding3 = vec![0.0, 1.0, 0.0]; // Orthogonal
        let embedding4 = vec![-1.0, 0.0, 0.0]; // Opposite

        let record = MemoryRecord::with_embedding("test", "test", embedding1);

        // Identical vectors should have similarity 1.0
        assert_eq!(record.cosine_similarity(&embedding2), Some(1.0));
        
        // Orthogonal vectors should have similarity 0.0
        assert_eq!(record.cosine_similarity(&embedding3), Some(0.0));
        
        // Opposite vectors should have similarity -1.0
        assert_eq!(record.cosine_similarity(&embedding4), Some(-1.0));
    }

    #[test]
    fn test_cosine_similarity_no_embedding() {
        let record = MemoryRecord::new("test", "test");
        let other = vec![1.0, 0.0, 0.0];
        assert_eq!(record.cosine_similarity(&other), None);
    }

    #[test]
    fn test_cosine_similarity_different_dimensions() {
        let embedding1 = vec![1.0, 0.0];
        let embedding2 = vec![1.0, 0.0, 0.0]; // Different dimension

        let record = MemoryRecord::with_embedding("test", "test", embedding1);
        assert_eq!(record.cosine_similarity(&embedding2), None);
    }
}