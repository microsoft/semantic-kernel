// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.jdbc;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.microsoft.semantickernel.ai.embeddings.Embedding;
import com.microsoft.semantickernel.memory.MemoryException;
import com.microsoft.semantickernel.memory.MemoryException.ErrorCodes;
import com.microsoft.semantickernel.memory.MemoryRecord;
import java.sql.Connection;
import java.util.*;
import java.util.stream.Collectors;
import javax.annotation.CheckReturnValue;
import javax.annotation.Nonnull;
import reactor.core.publisher.Mono;
import reactor.util.function.Tuple2;
import reactor.util.function.Tuples;

public class JDBCMemoryStore implements SQLMemoryStore {
    protected final SQLConnector dbConnector;

    protected JDBCMemoryStore(SQLConnector connector) {
        this.dbConnector = connector;
    }

    @Override
    public Mono<Void> createCollectionAsync(@Nonnull String collectionName) {
        Objects.requireNonNull(collectionName);
        return this.dbConnector.createCollectionAsync(collectionName);
    }

    @Override
    public Mono<List<String>> getCollectionsAsync() {
        return this.dbConnector.getCollectionsAsync();
    }

    @Override
    public Mono<Boolean> doesCollectionExistAsync(@Nonnull String collectionName) {
        Objects.requireNonNull(collectionName);
        return this.dbConnector.doesCollectionExistsAsync(collectionName);
    }

    @Override
    public Mono<Void> deleteCollectionAsync(@Nonnull String collectionName) {
        Objects.requireNonNull(collectionName);
        return this.dbConnector.deleteCollectionAsync(collectionName);
    }

    @Override
    public Mono<String> upsertAsync(@Nonnull String collectionName, @Nonnull MemoryRecord record) {
        Objects.requireNonNull(collectionName);
        Objects.requireNonNull(record);
        return doesCollectionExistAsync(collectionName)
                .handle(
                        (exists, sink) -> {
                            if (!exists) {
                                sink.error(
                                        new MemoryException(
                                                ErrorCodes
                                                        .ATTEMPTED_TO_ACCESS_NONEXISTENT_COLLECTION,
                                                collectionName));
                                return;
                            }
                            sink.next(exists);
                        })
                .then(internalUpsertAsync(collectionName, record));
    }

    protected DatabaseEntry memoryRecordToDatabaseEntry(MemoryRecord record) {
        try {
            return new DatabaseEntry(
                    record.getKey(),
                    record.getSerializedMetadata(),
                    record.getSerializedEmbedding(),
                    record.getTimestamp());
        } catch (JsonProcessingException e) {
            throw new RuntimeException(e);
        }
    }

    protected MemoryRecord databaseEntryToMemoryRecord(DatabaseEntry entry, boolean withEmbedding) {
        try {
            Embedding embedding =
                    withEmbedding
                            ? new ObjectMapper().readValue(entry.getEmbedding(), Embedding.class)
                            : Embedding.empty();
            return MemoryRecord.fromJsonMetadata(
                    entry.getMetadata(), embedding, entry.getKey(), entry.getTimestamp());
        } catch (JsonProcessingException e) {
            throw new SQLConnectorException(
                    SQLConnectorException.ErrorCodes.SQL_ERROR,
                    "Error deserializing database entry",
                    e);
        }
    }

    private Mono<String> internalUpsertAsync(String collectionName, MemoryRecord record) {
        try {
            return this.dbConnector.upsertAsync(
                    collectionName,
                    record.getMetadata().getId(),
                    record.getSerializedMetadata(),
                    record.getSerializedEmbedding(),
                    record.getTimestamp());
        } catch (JsonProcessingException e) {
            throw new SQLConnectorException(
                    SQLConnectorException.ErrorCodes.SQL_ERROR,
                    "Error serializing MemoryRecord",
                    e);
        }
    }

    @Override
    public Mono<Collection<String>> upsertBatchAsync(
            @Nonnull String collectionName, @Nonnull Collection<MemoryRecord> records) {
        Objects.requireNonNull(collectionName);
        Objects.requireNonNull(records);
        return doesCollectionExistAsync(collectionName)
                .handle(
                        (exists, sink) -> {
                            if (!exists) {
                                sink.error(
                                        new MemoryException(
                                                ErrorCodes
                                                        .ATTEMPTED_TO_ACCESS_NONEXISTENT_COLLECTION,
                                                collectionName));
                                return;
                            }
                            sink.next(exists);
                        })
                .then(
                        dbConnector.upsertBatchAsync(
                                collectionName,
                                records.stream()
                                        .map(this::memoryRecordToDatabaseEntry)
                                        .collect(Collectors.toList())));
    }

    @Override
    public Mono<MemoryRecord> getAsync(
            @Nonnull String collectionName, @Nonnull String key, boolean withEmbedding) {
        Objects.requireNonNull(collectionName);
        Objects.requireNonNull(key);
        return this.internalGetAsync(collectionName, key, withEmbedding);
    }

    private Mono<MemoryRecord> internalGetAsync(
            String collectionName, String key, boolean withEmbedding) {
        Objects.requireNonNull(collectionName);
        Objects.requireNonNull(key);
        Mono<DatabaseEntry> entry = this.dbConnector.readAsync(collectionName, key);

        return entry.hasElement()
                .flatMap(
                        hasElement -> {
                            if (!hasElement) {
                                return Mono.empty();
                            }

                            return entry.map(
                                    databaseEntry ->
                                            databaseEntryToMemoryRecord(
                                                    databaseEntry, withEmbedding));
                        });
    }

    @Override
    public Mono<Collection<MemoryRecord>> getBatchAsync(
            @Nonnull String collectionName,
            @Nonnull Collection<String> keys,
            boolean withEmbeddings) {
        Objects.requireNonNull(collectionName);
        Objects.requireNonNull(keys);
        return this.dbConnector
                .readBatchAsync(collectionName, keys)
                .flatMap(
                        databaseEntries -> {
                            List<MemoryRecord> records = new ArrayList<>();
                            for (DatabaseEntry entry : databaseEntries) {
                                records.add(databaseEntryToMemoryRecord(entry, withEmbeddings));
                            }
                            return Mono.just(records);
                        });
    }

    @Override
    public Mono<Void> removeAsync(@Nonnull String collectionName, @Nonnull String key) {
        Objects.requireNonNull(collectionName);
        Objects.requireNonNull(key);
        return this.dbConnector.deleteAsync(collectionName, key);
    }

    @Override
    public Mono<Void> removeBatchAsync(
            @Nonnull String collectionName, @Nonnull Collection<String> keys) {
        Objects.requireNonNull(collectionName);
        Objects.requireNonNull(keys);
        return this.dbConnector.deleteBatchAsync(collectionName, keys);
    }

    @Override
    public Mono<Collection<Tuple2<MemoryRecord, Float>>> getNearestMatchesAsync(
            @Nonnull String collectionName,
            @Nonnull Embedding embedding,
            int limit,
            float minRelevanceScore,
            boolean withEmbeddings) {
        Objects.requireNonNull(collectionName);
        Objects.requireNonNull(embedding);
        Mono<List<DatabaseEntry>> entries = this.dbConnector.readAllAsync(collectionName);

        return entries.flatMap(
                databaseEntries -> {
                    List<Tuple2<MemoryRecord, Float>> nearestMatches = new ArrayList<>();
                    for (DatabaseEntry entry : databaseEntries) {
                        if (entry.getEmbedding() == null || entry.getEmbedding().isEmpty()) {
                            continue;
                        }
                        try {
                            Embedding recordEmbedding =
                                    new ObjectMapper()
                                            .readValue(entry.getEmbedding(), Embedding.class);
                            float similarity = embedding.cosineSimilarity(recordEmbedding);
                            if (similarity >= (float) minRelevanceScore) {
                                MemoryRecord record =
                                        MemoryRecord.fromJsonMetadata(
                                                entry.getMetadata(),
                                                withEmbeddings ? recordEmbedding : null,
                                                entry.getKey(),
                                                entry.getTimestamp());
                                nearestMatches.add(Tuples.of(record, similarity));
                            }
                        } catch (JsonProcessingException e) {
                            throw new SQLConnectorException(
                                    SQLConnectorException.ErrorCodes.SQL_ERROR,
                                    "Error deserializing database entry",
                                    e);
                        }
                    }
                    List<Tuple2<MemoryRecord, Float>> results =
                            nearestMatches.stream()
                                    .sorted(
                                            Comparator.comparing(
                                                    Tuple2::getT2, (a, b) -> Float.compare(b, a)))
                                    .limit(limit)
                                    .collect(Collectors.toList());

                    return Mono.just(results);
                });
    }

    @Override
    public Mono<Tuple2<MemoryRecord, Float>> getNearestMatchAsync(
            @Nonnull String collectionName,
            @Nonnull Embedding embedding,
            float minRelevanceScore,
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

    /** Builds a JDBCMemoryStore. */
    public static class Builder implements SQLMemoryStore.Builder<JDBCMemoryStore> {
        private Connection connection;

        /**
         * Builds and returns a JDBCMemoryStore instance with the specified database connection. The
         * build process will connect to the database and create the required tables.
         *
         * @return A JDBCMemoryStore instance configured with the provided database connection.
         * @deprecated Use {@link #buildAsync()} instead.
         */
        @Override
        @Deprecated
        public JDBCMemoryStore build() {
            return this.buildAsync().block();
        }

        /**
         * Asynchronously builds and returns a JDBCMemoryStore instance with the specified database
         * connection.
         *
         * @return A Mono with a JDBCMemoryStore instance configured with the provided database
         *     connection.
         */
        @Override
        @CheckReturnValue
        public Mono<JDBCMemoryStore> buildAsync() {
            JDBCConnector connector = new JDBCConnector(connection);
            JDBCMemoryStore memoryStore = new JDBCMemoryStore(connector);
            return connector.createTableAsync().thenReturn(memoryStore);
        }

        /**
         * Sets the database connection to be used by the memory store being built.
         *
         * @param connection The Connection object representing the database connection.
         * @return The updated Builder instance to continue the building process for a
         *     JDBCMemoryStore.
         */
        @Override
        public Builder withConnection(Connection connection) {
            this.connection = connection;
            return this;
        }
    }
}
