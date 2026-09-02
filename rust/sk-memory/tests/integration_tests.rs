//! Integration tests for cosine similarity recall within tolerance

use sk_memory::{InMemoryMemoryStore, MemoryRecord, MemoryStore};

/// Test that cosine similarity recall meets expected tolerances
#[tokio::test]
async fn test_cosine_similarity_recall_tolerance() {
    let store = InMemoryMemoryStore::new();
    let collection = "similarity_test";
    
    // Create collection
    store.create_collection(collection).await.unwrap();
    
    // Create test vectors with known similarities
    let base_vector = vec![1.0, 0.0, 0.0]; // Reference vector
    
    // Vector with high similarity (same direction)
    let high_sim_vector = vec![0.8, 0.1, 0.1]; // Should have high cosine similarity
    
    // Vector with medium similarity (45 degree angle)
    let med_sim_vector = vec![0.707, 0.707, 0.0]; // Should have medium cosine similarity
    
    // Vector with low similarity (orthogonal)
    let low_sim_vector = vec![0.0, 1.0, 0.0]; // Should have low cosine similarity
    
    // Vector with very low similarity (opposite direction)
    let very_low_sim_vector = vec![-1.0, 0.0, 0.0]; // Should have very low cosine similarity
    
    // Create memory records
    let records = vec![
        MemoryRecord::with_embedding("high_sim", "High similarity content", high_sim_vector),
        MemoryRecord::with_embedding("med_sim", "Medium similarity content", med_sim_vector),
        MemoryRecord::with_embedding("low_sim", "Low similarity content", low_sim_vector),
        MemoryRecord::with_embedding("very_low_sim", "Very low similarity content", very_low_sim_vector),
    ];
    
    // Insert records
    store.upsert_batch(collection, records).await.unwrap();
    
    // Test 1: High threshold should only return highly similar items
    let high_threshold_results = store.get_nearest_matches(
        collection,
        base_vector.clone(),
        10,
        0.8, // High threshold
        false,
    ).await.unwrap();
    
    // Should return items with score >= 0.8
    assert!(!high_threshold_results.is_empty(), "Should find at least one high similarity item");
    assert_eq!(high_threshold_results[0].record.id, "high_sim");
    assert!(high_threshold_results[0].score >= 0.8);
    
    // Test 2: Medium threshold should return high and medium similarity items
    let med_threshold_results = store.get_nearest_matches(
        collection,
        base_vector.clone(),
        10,
        0.6, // Medium threshold
        false,
    ).await.unwrap();
    
    // Should return high and medium similarity items
    assert_eq!(med_threshold_results.len(), 2);
    
    // Results should be sorted by score (highest first)
    assert!(med_threshold_results[0].score >= med_threshold_results[1].score);
    assert_eq!(med_threshold_results[0].record.id, "high_sim");
    assert_eq!(med_threshold_results[1].record.id, "med_sim");
    
    // Test 3: Lower threshold should return more items
    let low_threshold_results = store.get_nearest_matches(
        collection,
        base_vector.clone(),
        10,
        0.4, // Low threshold
        false,
    ).await.unwrap();
    
    // Should return high, medium, and low similarity items
    assert!(low_threshold_results.len() >= 2); // At least high and medium
    
    // Verify order is maintained (highest score first)
    for i in 1..low_threshold_results.len() {
        assert!(low_threshold_results[i-1].score >= low_threshold_results[i].score);
    }
    
    // Test 4: Very low threshold should return all items
    let very_low_threshold_results = store.get_nearest_matches(
        collection,
        base_vector,
        10,
        0.0, // Very low threshold
        false,
    ).await.unwrap();
    
    // Should return all items
    assert_eq!(very_low_threshold_results.len(), 4);
    
    // Verify the cosine similarity calculations are within expected tolerance
    let high_sim_score = very_low_threshold_results.iter()
        .find(|r| r.record.id == "high_sim")
        .unwrap()
        .score;
    
    let med_sim_score = very_low_threshold_results.iter()
        .find(|r| r.record.id == "med_sim")
        .unwrap()
        .score;
        
    let low_sim_score = very_low_threshold_results.iter()
        .find(|r| r.record.id == "low_sim")
        .unwrap()
        .score;
    
    // Based on actual calculations:
    // High similarity should be very high (> 0.9)
    assert!(high_sim_score > 0.9, "High similarity score {} should be > 0.9", high_sim_score);
    
    // Medium similarity should be around 0.8-0.9 (45-degree angle gives ~0.707 cosine, normalized to ~0.85)
    assert!(med_sim_score > 0.8 && med_sim_score < 0.9, 
           "Medium similarity score {} should be between 0.8 and 0.9", med_sim_score);
    
    // Low similarity should be around 0.5 (orthogonal vectors have cosine similarity 0, normalized to 0.5)
    assert!(low_sim_score > 0.4 && low_sim_score < 0.6,
           "Low similarity score {} should be between 0.4 and 0.6", low_sim_score);
}

/// Test embedding recall with realistic text-like vectors
#[tokio::test]
async fn test_realistic_embedding_recall() {
    let store = InMemoryMemoryStore::new();
    let collection = "realistic_test";
    
    store.create_collection(collection).await.unwrap();
    
    // Simulate realistic embeddings (384 dimensions like OpenAI text-embedding-ada-002)
    let create_realistic_embedding = |seed: f32| -> Vec<f32> {
        (0..384)
            .map(|i| ((i as f32 * seed).sin() * 0.1).tanh())
            .collect()
    };
    
    // Create embeddings with varying similarities
    let query_embedding = create_realistic_embedding(1.0);
    let similar_embedding = create_realistic_embedding(1.1); // Very similar
    let somewhat_similar_embedding = create_realistic_embedding(2.0); // Somewhat similar
    let different_embedding = create_realistic_embedding(10.0); // Different
    
    let records = vec![
        MemoryRecord::with_embedding("similar", "Similar document content", similar_embedding),
        MemoryRecord::with_embedding("somewhat", "Somewhat related content", somewhat_similar_embedding),
        MemoryRecord::with_embedding("different", "Completely different content", different_embedding),
    ];
    
    store.upsert_batch(collection, records).await.unwrap();
    
    // Test recall with reasonable threshold
    let results = store.get_nearest_matches(
        collection,
        query_embedding,
        10,
        0.5, // Reasonable threshold for realistic embeddings
        true, // Include embeddings in response
    ).await.unwrap();
    
    // Should return at least the most similar items
    assert!(!results.is_empty(), "Should find at least some similar items");
    
    // Verify embeddings are included when requested
    for result in &results {
        assert!(result.record.embedding.is_some(), "Embedding should be included when requested");
        assert_eq!(result.record.embedding.as_ref().unwrap().len(), 384, "Embedding should have correct dimensions");
    }
    
    // Test recall precision - first result should be most similar
    if results.len() > 1 {
        assert!(results[0].score >= results[1].score, "Results should be sorted by similarity");
    }
    
    // Test that similarity scores are reasonable (not all 0 or 1)
    for result in &results {
        assert!(result.score >= 0.0 && result.score <= 1.0, 
               "Similarity score {} should be between 0 and 1", result.score);
        assert!(result.score >= 0.5, 
               "With threshold 0.5, all results should have score >= 0.5, got {}", result.score);
    }
}

/// Test that cosine similarity calculation accuracy meets tolerance requirements
#[test]
fn test_cosine_similarity_mathematical_accuracy() {
    // Test known mathematical relationships with tight tolerances
    
    // Test 1: Identical vectors should have similarity 1.0
    let vec1 = vec![1.0, 2.0, 3.0];
    let vec2 = vec![1.0, 2.0, 3.0];
    let record = MemoryRecord::with_embedding("test", "test", vec1);
    let similarity = record.cosine_similarity(&vec2).unwrap();
    assert!((similarity - 1.0).abs() < 1e-6, "Identical vectors should have similarity ~1.0, got {}", similarity);
    
    // Test 2: Orthogonal vectors should have similarity 0.0
    let vec1 = vec![1.0, 0.0, 0.0];
    let vec2 = vec![0.0, 1.0, 0.0];
    let record = MemoryRecord::with_embedding("test", "test", vec1);
    let similarity = record.cosine_similarity(&vec2).unwrap();
    assert!(similarity.abs() < 1e-6, "Orthogonal vectors should have similarity ~0.0, got {}", similarity);
    
    // Test 3: Opposite vectors should have similarity -1.0
    let vec1 = vec![1.0, 0.0, 0.0];
    let vec2 = vec![-1.0, 0.0, 0.0];
    let record = MemoryRecord::with_embedding("test", "test", vec1);
    let similarity = record.cosine_similarity(&vec2).unwrap();
    assert!((similarity - (-1.0)).abs() < 1e-6, "Opposite vectors should have similarity ~-1.0, got {}", similarity);
    
    // Test 4: 45-degree angle vectors should have similarity ~0.707
    let vec1 = vec![1.0, 0.0];
    let vec2 = vec![1.0, 1.0];
    let record = MemoryRecord::with_embedding("test", "test", vec1);
    let similarity = record.cosine_similarity(&vec2).unwrap();
    let expected = std::f32::consts::FRAC_1_SQRT_2; // ~0.707
    assert!((similarity - expected).abs() < 1e-3, 
           "45-degree vectors should have similarity ~{}, got {}", expected, similarity);
    
    // Test 5: Scaled vectors should have same similarity
    let vec1 = vec![1.0, 1.0, 1.0];
    let vec2 = vec![2.0, 2.0, 2.0]; // Scaled version
    let record = MemoryRecord::with_embedding("test", "test", vec1);
    let similarity = record.cosine_similarity(&vec2).unwrap();
    assert!((similarity - 1.0).abs() < 1e-6, "Scaled vectors should have similarity 1.0, got {}", similarity);
}

/// Test memory store recall performance under different conditions
#[tokio::test]
async fn test_recall_performance_and_accuracy() {
    let store = InMemoryMemoryStore::new();
    let collection = "performance_test";
    
    store.create_collection(collection).await.unwrap();
    
    // Create a larger dataset for performance testing
    let mut records = Vec::new();
    let dimension = 128;
    
    // Create query vector
    let query_vector: Vec<f32> = (0..dimension).map(|i| (i as f32).sin()).collect();
    
    // Create records with known similarity patterns
    for i in 0..100 {
        let similarity_factor = (i as f32) / 100.0; // 0.0 to 0.99
        
        // Create vector with controlled similarity to query
        let mut vector = query_vector.clone();
        for (j, val) in vector.iter_mut().enumerate() {
            *val = *val * similarity_factor + (j as f32).cos() * (1.0 - similarity_factor);
        }
        
        let record = MemoryRecord::with_embedding(
            format!("record_{}", i),
            format!("Content {}", i),
            vector,
        );
        records.push(record);
    }
    
    // Insert all records
    store.upsert_batch(collection, records).await.unwrap();
    
    // Test recall with different limits and thresholds
    let test_cases = vec![
        (5, 0.9),   // Top 5, high threshold
        (10, 0.8),  // Top 10, medium-high threshold  
        (20, 0.6),  // Top 20, medium threshold
        (50, 0.3),  // Top 50, low threshold
    ];
    
    for (limit, threshold) in test_cases {
        let results = store.get_nearest_matches(
            collection,
            query_vector.clone(),
            limit,
            threshold,
            false,
        ).await.unwrap();
        
        // Verify we don't exceed the limit
        assert!(results.len() <= limit, "Results should not exceed limit {}, got {}", limit, results.len());
        
        // Verify all results meet the threshold
        for result in &results {
            assert!(result.score >= threshold, 
                   "Result score {} should be >= threshold {}", result.score, threshold);
        }
        
        // Verify results are sorted by score (descending)
        for i in 1..results.len() {
            assert!(results[i-1].score >= results[i].score,
                   "Results should be sorted by score (descending)");
        }
        
        // With our controlled similarity pattern, higher indices should generally have higher scores
        // (since similarity_factor increases with i)
        if !results.is_empty() {
            let first_result_id = &results[0].record.id;
            let first_index: usize = first_result_id.strip_prefix("record_").unwrap().parse().unwrap();
            
            // The first result should be from the higher indices (more similar)
            assert!(first_index >= 70, 
                   "With threshold {}, first result should be from higher indices, got index {}", 
                   threshold, first_index);
        }
    }
}