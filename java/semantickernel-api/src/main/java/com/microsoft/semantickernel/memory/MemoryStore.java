// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.memory;

import com.microsoft.semantickernel.ai.embeddings.Embedding;
import java.util.Collection;
import java.util.List;
import javax.annotation.Nonnull;
import reactor.core.publisher.Mono;
import reactor.util.function.Tuple2;

/** An interface for storing and retrieving indexed {@link MemoryRecord} objects in a data store. */
public interface MemoryStore {

    /**
     * Creates a new collection in the data store.
     *
     * @param collectionName The name associated with a collection of embeddings
     * @return A future that completes when the collection is created.
     */
    Mono<Void> createCollectionAsync(@Nonnull String collectionName);

    /**
     * Gets all collection names in the data store.
     *
     * @return An unmodifiable group of collection names.
     */
    Mono<List<String>> getCollectionsAsync();

    /**
     * Determines if a collection exists in the data store.
     *
     * @param collectionName The name associated with a collection of embeddings.
     * @return A future that completes with a boolean indicating whether the collection exists.
     */
    Mono<Boolean> doesCollectionExistAsync(@Nonnull String collectionName);

    /**
     * Deletes a collection from the data store.
     *
     * @param collectionName The name associated with a collection of embeddings.
     * @return A future that completes when the collection is deleted.
     */
    Mono<Void> deleteCollectionAsync(@Nonnull String collectionName);

    /**
     * Upserts a memory record into the data store. Does not guarantee that the collection exists.
     * If the record already exists, it will be updated. If the record does not exist, it will be
     * created.
     *
     * @param collectionName The name associated with a collection of embeddings.
     * @param record The memory record to upsert.
     * @return The unique identifier for the memory record.
     */
    Mono<String> upsertAsync(@Nonnull String collectionName, @Nonnull MemoryRecord record);

    /**
     * Upserts a group of memory records into the data store. Does not guarantee that the collection
     * exists. If the record already exists, it will be updated. If the record does not exist, it
     * will be created.
     *
     * @param collectionName The name associated with a collection of vectors.
     * @param records The memory records to upsert.
     * @return The unique identifiers for the memory records.
     */
    Mono<Collection<String>> upsertBatchAsync(
            @Nonnull String collectionName, @Nonnull Collection<MemoryRecord> records);

    /**
     * Gets a memory record from the data store. Does not guarantee that the collection exists.
     *
     * @param collectionName The name associated with a collection of embeddings.
     * @param key The unique id associated with the memory record to get.
     * @param withEmbedding If true, the embedding will be returned in the memory record.
     * @return The memory record if found, otherwise null.
     */
    Mono<MemoryRecord> getAsync(
            @Nonnull String collectionName, @Nonnull String key, boolean withEmbedding);

    /**
     * Gets a batch of memory records from the data store. Does not guarantee that the collection
     * exists.
     *
     * @param collectionName The name associated with a collection of embedding.
     * @param keys The unique ids associated with the memory record to get.
     * @param withEmbeddings If true, the embeddings will be returned in the memory records.
     * @return The memory records associated with the unique keys provided.
     */
    Mono<Collection<MemoryRecord>> getBatchAsync(
            @Nonnull String collectionName,
            @Nonnull Collection<String> keys,
            boolean withEmbeddings);

    /**
     * Removes a memory record from the data store. Does not guarantee that the collection exists.
     *
     * @param collectionName The name associated with a collection of embeddings.
     * @param key The unique id associated with the memory record to remove.
     * @return A {@link Mono} that completes when the operation is done.
     */
    Mono<Void> removeAsync(@Nonnull String collectionName, @Nonnull String key);

    /**
     * Removes a batch of memory records from the data store. Does not guarantee that the collection
     * exists.
     *
     * @param collectionName The name associated with a collection of embeddings.
     * @param keys The unique ids associated with the memory record to remove.
     * @return A {@link Mono} that completes when the operation is done.
     */
    Mono<Void> removeBatchAsync(@Nonnull String collectionName, @Nonnull Collection<String> keys);

    /**
     * Gets the nearest matches to the {@link Embedding} of type {@code Float}. Does not guarantee
     * that the collection exists.
     *
     * @param collectionName The name associated with a collection of embeddings.
     * @param embedding The {@link Embedding} to compare the collection's embeddings with.
     * @param limit The maximum number of similarity results to return.
     * @param minRelevanceScore The minimum relevance threshold for returned results.
     * @param withEmbeddings If true, the embeddings will be returned in the memory records.
     * @return A collection of tuples where item1 is a {@link MemoryRecord} and item2 is its
     *     similarity score as a {@code double}.
     */
    Mono<Collection<Tuple2<MemoryRecord, Float>>> getNearestMatchesAsync(
            @Nonnull String collectionName,
            @Nonnull Embedding embedding,
            int limit,
            double minRelevanceScore,
            boolean withEmbeddings);

    /**
     * Gets the nearest match to the {@link Embedding} of type {@code Float}. Does not guarantee
     * that the collection exists.
     *
     * @param collectionName The name associated with a collection of embeddings.
     * @param embedding The {@link Embedding} to compare the collection's embeddings with.
     * @param minRelevanceScore The minimum relevance threshold for returned results.
     * @param withEmbedding If true, the embedding will be returned in the memory record.
     * @return A tuple consisting of the {@link MemoryRecord} and item2 is its similarity score as a
     *     {@code float}. Null if no nearest match found.
     */
    Mono<Tuple2<MemoryRecord, Float>> getNearestMatchAsync(
            @Nonnull String collectionName,
            @Nonnull Embedding embedding,
            double minRelevanceScore,
            boolean withEmbedding);

    interface Builder {
        MemoryStore build();
    }
}
