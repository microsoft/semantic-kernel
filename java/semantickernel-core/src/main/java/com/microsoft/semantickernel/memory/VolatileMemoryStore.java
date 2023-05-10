// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.memory;

import com.microsoft.semantickernel.ai.embeddings.Embedding;
import com.microsoft.semantickernel.exceptions.NotSupportedException;

import reactor.core.publisher.Mono;
import reactor.util.function.Tuple2;

import java.util.Collection;
import java.util.Collections;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

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
                    MemoryException.ErrorCodes.FAILED_TO_CREATE_COLLECTION,
                    String.format("Could not create collection %s", collectionName));
        }
        this._store.putIfAbsent(collectionName, new ConcurrentHashMap<>());
        return Mono.empty();
    }

    @Override
    public Mono<Boolean> doesCollectionExistAsync(@Nonnull String collectionName) {
        return Mono.just(this._store.containsKey(collectionName));
    }

    @Override
    public Mono<Collection<String>> getCollectionsAsync() {
        return Mono.just(Collections.unmodifiableCollection(this._store.keySet()));
    }

    @Override
    public Mono<Void> deleteCollectionAsync(@Nonnull String collectionName) {
        if (!this._store.containsKey(collectionName)) {
            throw new MemoryException(
                    MemoryException.ErrorCodes.FAILED_TO_DELETE_COLLECTION,
                    String.format("Could not delete collection %s", collectionName));
        }
        this._store.remove(collectionName);
        return Mono.empty();
    }

    @Override
    public Mono<String> upsertAsync(@Nonnull String collectionName, @Nonnull MemoryRecord record) {
        // Contract:
        //    Does not guarantee that the collection exists.
        Map<String, MemoryRecord> collection = getCollection(collectionName);

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
        Map<String, MemoryRecord> collection = getCollection(collectionName);
        MemoryRecord record = collection.get(key);
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
        Map<String, MemoryRecord> collection = getCollection(collectionName);
        collection.remove(key);
        return Mono.empty();
    }

    @Override
    public Mono<Void> removeBatchAsync(
            @Nonnull String collectionName, @Nonnull Collection<String> keys) {
        Map<String, MemoryRecord> collection = getCollection(collectionName);
        keys.forEach(key -> collection.remove(key));
        return Mono.empty();
    }

    @Override
    public Mono<Collection<Tuple2<MemoryRecord, Double>>> getNearestMatchesAsync(
            @Nonnull String collectionName,
            @Nonnull Embedding<Float> embedding,
            int limit,
            double minRelevanceScore,
            boolean withEmbeddings) {

        return Mono.error(new NotSupportedException("Pending implementation"));
        //        if (limit <= 0) {
        //            return Mono.just(Collections.emptyList());
        //        }
        //
        //        Map<String,MemoryRecord> collection = getCollection(collectionName);
        //        Collection<MemoryRecord> embeddingCollection = collection.values();
        //        if (embeddingCollection == null || embeddingCollection.isEmpty()) {
        //            return Mono.just(Collections.emptyList());
        //        }
        //
        //        List<Tuple2<MemoryRecord, Double>> nearestMatches = new ArrayList<>();
        //        embeddingCollection.forEach(record -> {
        //            if (record != null) {
        //                double similarity = embedding.cosineSimilarity(record.getEmbedding());
        //                if (similarity >= minRelevanceScore) {
        //                    if (withEmbeddings) {
        //                        nearestMatches.add(new Tuple2<>(record, similarity));
        //                    } else {
        //                        nearestMatches.add(new
        // Tuple2<>(MemoryRecord.fromMetadata(record.getMetadata(), null,
        // record.getMetadata().getId(), record.getTimestamp()), similarity));
        //                    }
        //                }
        //            }
        //        });
        //
        //
        //        EmbeddingReadOnlySpan<Float> embeddingSpan = new(embedding.AsReadOnlySpan());
        //
        //        TopNCollection<MemoryRecord> embeddings = new(limit);
        //
        //        foreach (var record in embeddingCollection)
        //        {
        //            if (record != null)
        //            {
        //                double similarity = embedding
        //                    .AsReadOnlySpan()
        //                    .CosineSimilarity(record.Embedding.AsReadOnlySpan());
        //                if (similarity >= minRelevanceScore)
        //                {
        //                    var entry = withEmbeddings ? record :
        // MemoryRecord.FromMetadata(record.Metadata, Embedding<Float>.Empty, record.Key,
        // record.Timestamp);
        //                    embeddings.Add(new(entry, similarity));
        //                }
        //            }
        //        }
        //
        //        embeddings.SortByScore();
        //
        //        return embeddings.Select(x => (x.Value, x.Score.Value)).ToAsyncEnumerable();
    }

    @Override
    public Mono<Tuple2<MemoryRecord, Double>> getNearestMatchAsync(
            @Nonnull String collectionName,
            @Nonnull Embedding<Float> embedding,
            double minRelevanceScore,
            boolean withEmbedding) {
        return Mono.error(new NotSupportedException("Pending implementation"));
        //        return await this.GetNearestMatchesAsync(
        //            collectionName: collectionName,
        //            embedding: embedding,
        //            limit: 1,
        //            minRelevanceScore: minRelevanceScore,
        //            withEmbeddings: withEmbedding,
        //            cancellationToken:
        // cancellationToken).FirstOrDefaultAsync(cancellationToken).ConfigureAwait(false);
    }

    protected Map<String, MemoryRecord> getCollection(@Nonnull String collectionName) {
        Map<String, MemoryRecord> collection = this._store.get(collectionName);
        if (collection == null) {
            throw new MemoryException(
                    MemoryException.ErrorCodes.ATTEMPTED_TO_ACCESS_NONEXISTENT_COLLECTION,
                    String.format(
                            "Attempted to access a memory collection that does not exist: %s",
                            collectionName));
        }
        return collection;
    }

    /*
    protected boolean TryGetCollection(
        String name,
        [NotNullWhen(true)] out ConcurrentDictionary<String,
            MemoryRecord>? collection,
        boolean create)
    {
        if (this._store.TryGetValue(name, out collection))
        {
            return true;
        }

        if (create)
        {
            collection = new ConcurrentDictionary<String, MemoryRecord>();
            return this._store.TryAdd(name, collection);
        }

        collection = null;
        return false;
    }

    private readonly ConcurrentDictionary<String,
        ConcurrentDictionary<String, MemoryRecord>> _store = new();
    */
}
