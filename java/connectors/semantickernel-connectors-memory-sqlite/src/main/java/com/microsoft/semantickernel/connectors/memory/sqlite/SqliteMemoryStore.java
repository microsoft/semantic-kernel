// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.sqlite;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.microsoft.semantickernel.ai.embeddings.Embedding;
import com.microsoft.semantickernel.ai.embeddings.EmbeddingVector;
import com.microsoft.semantickernel.memory.MemoryRecord;
import com.microsoft.semantickernel.memory.MemoryStore;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.util.function.Tuple2;
import reactor.util.function.Tuples;

import java.sql.*;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.stream.Collectors;

import javax.annotation.Nonnull;

public class SqliteMemoryStore implements MemoryStore {

    private final Database dbConnector;
    private Connection dbConnection;

    public SqliteMemoryStore() {
        this.dbConnector = new Database();
    }

    public Mono<Void> connectAsync(String filename) throws SQLException {
        this.dbConnection = DriverManager.getConnection("jdbc:sqlite:" + filename);
        return this.dbConnector.createTableAsync(this.dbConnection);
    }

    @Override
    public Mono<Void> createCollectionAsync(@Nonnull String collectionName) {
        return this.dbConnector.createCollectionAsync(this.dbConnection, collectionName);
    }

    @Override
    public Mono<List<String>> getCollectionsAsync() {
        return this.dbConnector.getCollectionsAsync(this.dbConnection);
    }

    @Override
    public Mono<Boolean> doesCollectionExistAsync(@Nonnull String collectionName) {
        return this.dbConnector.doesCollectionExistsAsync(this.dbConnection, collectionName);
    }

    @Override
    public Mono<Void> deleteCollectionAsync(@Nonnull String collectionName) {
        return this.dbConnector.deleteCollectionAsync(this.dbConnection, collectionName);
    }

    @Override
    public Mono<String> upsertAsync(@Nonnull String collectionName, @Nonnull MemoryRecord record) {
        return this.internalUpsertAsync(collectionName, record);
    }

    private Mono<String> internalUpsertAsync(
            @Nonnull String collectionName, @Nonnull MemoryRecord record) {
        try {
            Mono<Void> update =
                    this.dbConnector.updateAsync(
                            this.dbConnection,
                            collectionName,
                            record.getKey(),
                            record.getSerializedMetadata(),
                            record.getSerializedEmbedding(),
                            record.getTimestamp());

            Mono<Void> insert =
                    this.dbConnector.insertOrIgnoreAsync(
                            this.dbConnection,
                            collectionName,
                            record.getKey(),
                            record.getSerializedMetadata(),
                            record.getSerializedEmbedding(),
                            record.getTimestamp());

            return update.then(insert).then(Mono.just(record.getKey()));
        } catch (JsonProcessingException e) {
            throw new RuntimeException(e);
        }
    }

    @Override
    public Mono<Collection<String>> upsertBatchAsync(
            @Nonnull String collectionName, @Nonnull Collection<MemoryRecord> records) {
        return Flux.fromIterable(records)
                .flatMap(record -> internalUpsertAsync(collectionName, record))
                .collect(Collectors.toCollection(ArrayList::new));
    }

    @Override
    public Mono<MemoryRecord> getAsync(
            @Nonnull String collectionName, @Nonnull String key, boolean withEmbedding) {
        return this.internalGetAsync(collectionName, key, withEmbedding);
    }

    private Mono<MemoryRecord> internalGetAsync(
            @Nonnull String collectionName, @Nonnull String key, boolean withEmbedding) {
        Mono<Database.DatabaseEntry> entry =
                this.dbConnector.readAsync(this.dbConnection, collectionName, key);

        return entry.hasElement()
                .flatMap(
                        hasElement -> {
                            if (!hasElement) {
                                return Mono.empty();
                            }

                            return entry.map(
                                    databaseEntry -> {
                                        try {
                                            if (withEmbedding) {
                                                return MemoryRecord.fromJsonMetadata(
                                                        databaseEntry.getMetadata(),
                                                        new ObjectMapper()
                                                                .readValue(
                                                                        databaseEntry
                                                                                .getEmbedding(),
                                                                        Embedding.class),
                                                        databaseEntry.getKey(),
                                                        databaseEntry.getTimestamp());
                                            }
                                            return MemoryRecord.fromJsonMetadata(
                                                    databaseEntry.getMetadata(),
                                                    Embedding.empty(),
                                                    databaseEntry.getKey(),
                                                    databaseEntry.getTimestamp());
                                        } catch (JsonProcessingException e) {
                                            throw new RuntimeException(e);
                                        }
                                    });
                        });
    }

    @Override
    public Mono<Collection<MemoryRecord>> getBatchAsync(
            @Nonnull String collectionName,
            @Nonnull Collection<String> keys,
            boolean withEmbeddings) {
        return Flux.fromIterable(keys)
                .flatMap(key -> internalGetAsync(collectionName, key, withEmbeddings))
                .collect(Collectors.toCollection(ArrayList::new));
    }

    @Override
    public Mono<Void> removeAsync(@Nonnull String collectionName, @Nonnull String key) {
        return this.dbConnector.deleteAsync(this.dbConnection, collectionName, key);
    }

    @Override
    public Mono<Void> removeBatchAsync(
            @Nonnull String collectionName, @Nonnull Collection<String> keys) {
        return Flux.fromIterable(keys)
                .flatMap(
                        key -> this.dbConnector.deleteAsync(this.dbConnection, collectionName, key))
                .then();
    }

    @Override
    public Mono<Collection<Tuple2<MemoryRecord, Float>>> getNearestMatchesAsync(
            @Nonnull String collectionName,
            @Nonnull Embedding embedding,
            int limit,
            double minRelevanceScore,
            boolean withEmbeddings) {

        Mono<List<Database.DatabaseEntry>> entries =
                this.dbConnector.readAllAsync(this.dbConnection, collectionName);

        return entries.flatMap(
                databaseEntries -> {
                    EmbeddingVector embeddingVector = embedding.getVector();
                    List<Tuple2<MemoryRecord, Float>> results = new ArrayList<>();
                    for (Database.DatabaseEntry entry : databaseEntries) {
                        if (entry.getEmbedding() == null || entry.getEmbedding().isEmpty()) {
                            continue;
                        }
                        try {
                            Embedding recordEmbedding =
                                    new ObjectMapper()
                                            .readValue(entry.getEmbedding(), Embedding.class);
                            float relevanceScore = embeddingVector.cosineSimilarity(recordEmbedding.getVector());
                            if (relevanceScore >= minRelevanceScore) {
                                MemoryRecord record =
                                        MemoryRecord.fromJsonMetadata(
                                                entry.getMetadata(),
                                                recordEmbedding,
                                                entry.getKey(),
                                                entry.getTimestamp());
                                results.add(Tuples.of(record, relevanceScore));
                            }
                        } catch (JsonProcessingException e) {
                            throw new RuntimeException(e);
                        }
                    }
                    return Mono.just(results);
                });
    }

    @Override
    public Mono<Tuple2<MemoryRecord, Float>> getNearestMatchAsync(
            @Nonnull String collectionName,
            @Nonnull Embedding embedding,
            double minRelevanceScore,
            boolean withEmbedding) {
        return null;
    }

    public static class Builder implements MemoryStore.Builder {
        @Override
        public MemoryStore build() {
            return new SqliteMemoryStore();
        }
    }
}
