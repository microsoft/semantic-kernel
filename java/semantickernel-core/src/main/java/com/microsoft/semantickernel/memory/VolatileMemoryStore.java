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
import java.util.Objects;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

import javax.annotation.Nonnull;

/** A simple volatile memory embeddings store. */
public class VolatileMemoryStore implements MemoryStore {

    private final Map<String, Map<String, MemoryRecord>> _store = new ConcurrentHashMap<>();

    /** Constructs a new {@link VolatileMemoryStore} object. */
    public VolatileMemoryStore() {}

    @Override
    public Mono<Void> createCollectionAsync(@Nonnull String collectionName) {
        Objects.requireNonNull(collectionName);
        return Mono.fromRunnable(() -> this._store.putIfAbsent(collectionName, new ConcurrentHashMap<>()));
    }

    @Override
    public Mono<Boolean> doesCollectionExistAsync(@Nonnull String collectionName) {
        Objects.requireNonNull(collectionName);
        return Mono.just(this._store.containsKey(collectionName));
    }

    @Override
    public Mono<List<String>> getCollectionsAsync() {
        return Mono.just(Collections.unmodifiableList(new ArrayList<>(this._store.keySet())));
    }

    @Override
    public Mono<Void> deleteCollectionAsync(@Nonnull String collectionName) {
        Objects.requireNonNull(collectionName);
        return Mono.fromRunnable(() -> {
            if (this._store.containsKey(collectionName)) {
                this._store.remove(collectionName);
            } else {
                throw new MemoryException(MemoryException.ErrorCodes.ATTEMPTED_TO_ACCESS_NONEXISTENT_COLLECTION, collectionName);
            }
        });
    }

    @Override
    public Mono<String> upsertAsync(@Nonnull String collectionName, @Nonnull MemoryRecord record) {
        Objects.requireNonNull(collectionName);
        Objects.requireNonNull(record);

        return Mono.fromCallable(() -> {
            // Contract:
            //    Does not guarantee that the collection exists.

            // getCollection throws MemoryException if the collection does not exist.
            Map<String, MemoryRecord> collection = getCollection(collectionName);

            String key = record.getMetadata().getId();
            // Assumption is that MemoryRecord will always have a non-null id.
            assert key != null;

            // Contract:
            //     If the record already exists, it will be updated.
            //     If the record does not exist, it will be created.
            collection.put(key, record);
            return key;
        });
    }

    @Override
    public Mono<Collection<String>> upsertBatchAsync(
            @Nonnull String collectionName, @Nonnull Collection<MemoryRecord> records) {
        Objects.requireNonNull(collectionName);
        Objects.requireNonNull(records);

        return Mono.fromCallable(() -> {
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
            return keys;
        });
    }

    @Override
    public Mono<MemoryRecord> getAsync(
            @Nonnull String collectionName, @Nonnull String key, boolean withEmbedding) {
        Objects.requireNonNull(collectionName);
        Objects.requireNonNull(key);

        return Mono.fromCallable(() -> {
            Map<String, MemoryRecord> collection = this._store.get(collectionName);
            MemoryRecord record = collection != null ? collection.get(key) : null;
            if (record != null) {
                if (withEmbedding) {
                    return record;
                } else {
                    return
                            MemoryRecord.fromMetadata(
                                    record.getMetadata(),
                                    null,
                                    record.getMetadata().getId(),
                                    record.getTimestamp());
                }
            }
            return null;
        });
    }

    @Override
    public Mono<Collection<MemoryRecord>> getBatchAsync(
            @Nonnull String collectionName,
            @Nonnull Collection<String> keys,
            boolean withEmbeddings) {
        Objects.requireNonNull(collectionName);
        Objects.requireNonNull(keys);

        return Mono.fromCallable(() -> {
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
            return records;
        });
    }

    @Override
    public Mono<Void> removeAsync(@Nonnull String collectionName, @Nonnull String key) {
        return Mono.fromRunnable(() -> {
            Map<String, MemoryRecord> collection = this._store.get(collectionName);
            if (collection != null) collection.remove(key);
        });
    }

    @Override
    public Mono<Void> removeBatchAsync(
            @Nonnull String collectionName, @Nonnull Collection<String> keys) {
        return Mono.fromRunnable(() -> {
            Map<String, MemoryRecord> collection = this._store.get(collectionName);
            keys.forEach(collection::remove);
        });
    }

    @Override
    public Mono<Collection<Tuple2<MemoryRecord, Float>>> getNearestMatchesAsync(
            @Nonnull String collectionName,
            @Nonnull Embedding embedding,
            int limit,
            double minRelevanceScore,
            boolean withEmbeddings) {
        Objects.requireNonNull(collectionName);
        Objects.requireNonNull(embedding);

        if (limit <= 0) {
            return Mono.just(Collections.emptyList());
        }

        return Mono.fromCallable(() -> {

        Map<String, MemoryRecord> collection = getCollection(collectionName);
        if (collection == null || collection.isEmpty()) {
            return Collections.emptyList();
        }

        final EmbeddingVector embeddingVector = new EmbeddingVector(embedding.getVector());

        Collection<Tuple2<MemoryRecord, Float>> nearestMatches = new ArrayList<>();
        collection.values().forEach(
                record -> {
                    if (record != null) {
                        EmbeddingVector recordVector =
                                new EmbeddingVector(record.getEmbedding().getVector());
                        float similarity = embeddingVector.cosineSimilarity(recordVector);
                        if (Float.compare(similarity,(float)minRelevanceScore) >= 0) {
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

        List<Tuple2<MemoryRecord, Float>> result =
                nearestMatches.stream()
                        // sort by similarity score, descending
                        .sorted(Comparator.comparing(it -> it.getT2().doubleValue(), (a,b) -> Double.compare(b, a)))
                        .limit(limit)
                        .collect(Collectors.toList());
        return result;
        });

    }

    @Override
    public Mono<Tuple2<MemoryRecord, Float>> getNearestMatchAsync(
            @Nonnull String collectionName,
            @Nonnull Embedding embedding,
            double minRelevanceScore,
            boolean withEmbedding) {
        Objects.requireNonNull(collectionName);
        Objects.requireNonNull(embedding);

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
        Objects.requireNonNull(collectionName);
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
