// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.memory;

import com.microsoft.semantickernel.ai.EmbeddingVector;
import com.microsoft.semantickernel.ai.embeddings.Embedding;

import reactor.core.publisher.Mono;
import reactor.util.function.Tuple2;
import reactor.util.function.Tuples;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.ToDoubleFunction;
import java.util.stream.Collectors;

import javax.annotation.Nonnull;

/** A simple volatile memory embeddings store. */
public class VolatileMemoryStore implements MemoryStore {

    private final Map<String, Map<String, MemoryRecord>> _store = new ConcurrentHashMap<>();

    /** Constructs a new {@link VolatileMemoryStore} object. */
    public VolatileMemoryStore() {}

    @Override
    public Mono<Void> createCollectionAsync(@Nonnull String collectionName) {
        if (this._store.containsKey(collectionName)) {
            throw new MemoryException(
                    MemoryException.ErrorCodes.FAILED_TO_CREATE_COLLECTION, collectionName);
        }
        this._store.putIfAbsent(collectionName, new ConcurrentHashMap<>());
        return Mono.empty();
    }

    @Override
    public Mono<Boolean> doesCollectionExistAsync(@Nonnull String collectionName) {
        return Mono.just(this._store.containsKey(collectionName));
    }

    @Override
    public Mono<List<String>> getCollectionsAsync() {
        List<String> keys = new ArrayList<>(this._store.keySet());
        return Mono.just(Collections.unmodifiableList(keys));
    }

    @Override
    public Mono<Void> deleteCollectionAsync(@Nonnull String collectionName) {
        if (!this._store.containsKey(collectionName)) {
            throw new MemoryException(
                    MemoryException.ErrorCodes.FAILED_TO_DELETE_COLLECTION, collectionName);
        }
        this._store.remove(collectionName);
        return Mono.empty();
    }

    @Override
    public Mono<String> upsertAsync(@Nonnull String collectionName, @Nonnull MemoryRecord record) {
        // Contract:
        //    Does not guarantee that the collection exists.
        Map<String, MemoryRecord> collection = null;
        try {
            // getCollection throws MemoryException if the collection does not exist.
            collection = getCollection(collectionName);
        } catch (MemoryException e) {
            return Mono.error(e);
        }

        String key = record.getMetadata().getId();
        // Assumption is that MemoryRecord will always have a non-null id.
        assert key != null;
        // Contract:
        //     If the record already exists, it will be updated.
        //     If the record does not exist, it will be created.
        collection.put(key, record);
        return Mono.just(key);
    }

    @Override
    public Mono<Collection<String>> upsertBatchAsync(
            @Nonnull String collectionName, @Nonnull Collection<MemoryRecord> records) {
        Map<String, MemoryRecord> collection = getCollection(collectionName);
        Set<String> keys = new HashSet<>();
        records.forEach(
                record -> {
                    String key = record.getMetadata().getId();
                    // Assumption is that MemoryRecord will always have a non-null id.
                    assert key != null;
                    // Contract:
                    //     If the record already exists, it will be updated.
                    //     If the record does not exist, it will be created.
                    collection.put(key, record);
                    keys.add(key);
                });
        return Mono.just(keys);
    }

    @Override
    public Mono<MemoryRecord> getAsync(
            @Nonnull String collectionName, @Nonnull String key, boolean withEmbedding) {
        Map<String, MemoryRecord> collection = this._store.get(collectionName);
        MemoryRecord record = collection != null ? collection.get(key) : null;
        if (record != null) {
            if (withEmbedding) {
                return Mono.just(record);
            } else {
                return Mono.just(
                        MemoryRecord.fromMetadata(
                                record.getMetadata(),
                                null,
                                record.getMetadata().getId(),
                                record.getTimestamp()));
            }
        }
        return Mono.empty();
    }

    @Override
    public Mono<Collection<MemoryRecord>> getBatchAsync(
            @Nonnull String collectionName,
            @Nonnull Collection<String> keys,
            boolean withEmbeddings) {
        Map<String, MemoryRecord> collection = getCollection(collectionName);
        Set<MemoryRecord> records = new HashSet<>();
        keys.forEach(
                key -> {
                    MemoryRecord record = collection.get(key);
                    if (record != null) {
                        if (withEmbeddings) {
                            records.add(record);
                        } else {
                            records.add(
                                    MemoryRecord.fromMetadata(
                                            record.getMetadata(),
                                            null,
                                            record.getMetadata().getId(),
                                            record.getTimestamp()));
                        }
                    }
                });
        return Mono.just(records);
    }

    @Override
    public Mono<Void> removeAsync(@Nonnull String collectionName, @Nonnull String key) {
        Map<String, MemoryRecord> collection = this._store.get(collectionName);
        if (collection != null) collection.remove(key);
        return Mono.empty();
    }

    @Override
    public Mono<Void> removeBatchAsync(
            @Nonnull String collectionName, @Nonnull Collection<String> keys) {
        Map<String, MemoryRecord> collection = this._store.get(collectionName);
        keys.forEach(collection::remove);
        return Mono.empty();
    }

    @SuppressWarnings("unchecked")
    private static EmbeddingVector<Number> upcastEmbeddingVector(List<? extends Number> list) {
        return new EmbeddingVector<Number>((List<Number>) list);
    }

    @SuppressWarnings("UnnecessaryLambda")
    private static final ToDoubleFunction<Tuple2<MemoryRecord, ? extends Number>>
            extractSimilarity = tuple -> tuple.getT2().doubleValue();

    @Override
    public Mono<Collection<Tuple2<MemoryRecord, Number>>> getNearestMatchesAsync(
            @Nonnull String collectionName,
            @Nonnull Embedding<? extends Number> embedding,
            int limit,
            double minRelevanceScore,
            boolean withEmbeddings) {

        if (limit <= 0) {
            return Mono.just(Collections.emptyList());
        }

        Map<String, MemoryRecord> collection = getCollection(collectionName);
        if (collection == null || collection.isEmpty()) {
            return Mono.just(Collections.emptyList());
        }

        Collection<MemoryRecord> embeddingCollection = collection.values();

        // Upcast the embedding vector to a Number to get around compiler complaining about type
        // mismatches.
        EmbeddingVector<Number> embeddingVector = upcastEmbeddingVector(embedding.getVector());

        Collection<Tuple2<MemoryRecord, Number>> nearestMatches = new ArrayList<>();
        embeddingCollection.forEach(
                record -> {
                    if (record != null) {
                        EmbeddingVector<Number> recordVector =
                                upcastEmbeddingVector(record.getEmbedding().getVector());
                        double similarity = embeddingVector.cosineSimilarity(recordVector);
                        if (similarity >= minRelevanceScore) {
                            if (withEmbeddings) {
                                nearestMatches.add(Tuples.of(record, similarity));
                            } else {
                                nearestMatches.add(
                                        Tuples.of(
                                                MemoryRecord.fromMetadata(
                                                        record.getMetadata(),
                                                        null,
                                                        record.getMetadata().getId(),
                                                        record.getTimestamp()),
                                                similarity));
                            }
                        }
                    }
                });

        List<Tuple2<MemoryRecord, Number>> result =
                nearestMatches.stream()
                        .sorted(Comparator.comparingDouble(extractSimilarity).reversed())
                        .limit(Math.max(1, limit))
                        .collect(Collectors.toList());

        return Mono.just(result);
    }

    @Override
    public Mono<Tuple2<MemoryRecord, ? extends Number>> getNearestMatchAsync(
            @Nonnull String collectionName,
            @Nonnull Embedding<? extends Number> embedding,
            double minRelevanceScore,
            boolean withEmbedding) {

        return getNearestMatchesAsync(
                        collectionName, embedding, 1, minRelevanceScore, withEmbedding)
                .flatMap(
                        nearestMatches -> {
                            if (nearestMatches.isEmpty()) {
                                return Mono.empty();
                            }
                            return Mono.just(nearestMatches.iterator().next());
                        });
    }

    protected Map<String, MemoryRecord> getCollection(@Nonnull String collectionName) {
        Map<String, MemoryRecord> collection = this._store.get(collectionName);
        if (collection == null) {
            throw new MemoryException(
                    MemoryException.ErrorCodes.ATTEMPTED_TO_ACCESS_NONEXISTENT_COLLECTION,
                    collectionName);
        }
        return collection;
    }

    public static class Builder implements MemoryStore.Builder {

        public Builder() {}

        @Override
        public MemoryStore build() {
            return new VolatileMemoryStore();
        }
    }
}
