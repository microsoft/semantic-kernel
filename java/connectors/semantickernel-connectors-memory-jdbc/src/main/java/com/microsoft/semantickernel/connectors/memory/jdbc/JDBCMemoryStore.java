// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.jdbc;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.microsoft.semantickernel.ai.embeddings.Embedding;
import com.microsoft.semantickernel.memory.MemoryException;
import com.microsoft.semantickernel.memory.MemoryException.ErrorCodes;
import com.microsoft.semantickernel.memory.MemoryRecord;
import com.microsoft.semantickernel.memory.MemoryStore;
import java.sql.Connection;
import java.util.*;
import java.util.stream.Collectors;
import javax.annotation.Nonnull;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.util.function.Tuple2;
import reactor.util.function.Tuples;

public class JDBCMemoryStore implements MemoryStore {
    protected final SQLConnector dbConnector;

    public JDBCMemoryStore(SQLConnector connector) {
        this.dbConnector = connector;
    }

    /**
     * Establishes an asynchronous connection to the database.
     *
     * @return A Mono representing the completion of the table creation operation, indicating the
     *     successful establishment of the database connection.
     */
    public Mono<Void> connectAsync() {
        return this.dbConnector.createTableAsync();
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

    private Mono<String> internalUpsertAsync(String collectionName, MemoryRecord record) {
        try {
            Mono<Void> update =
                    this.dbConnector.updateAsync(
                            collectionName,
                            record.getMetadata().getId(),
                            record.getSerializedMetadata(),
                            record.getSerializedEmbedding(),
                            record.getTimestamp());

            Mono<Void> insert =
                    this.dbConnector.insertOrIgnoreAsync(
                            collectionName,
                            record.getMetadata().getId(),
                            record.getSerializedMetadata(),
                            record.getSerializedEmbedding(),
                            record.getTimestamp());

            return update.then(insert).then(Mono.just(record.getMetadata().getId()));
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
                        Flux.fromIterable(records)
                                .concatMap(record -> internalUpsertAsync(collectionName, record))
                                .collect(Collectors.toCollection(ArrayList::new)));
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
                                            throw new SQLConnectorException(
                                                    SQLConnectorException.ErrorCodes.SQL_ERROR,
                                                    "Error deserializing database entry",
                                                    e);
                                        }
                                    });
                        });
    }

    @Override
    public Mono<Collection<MemoryRecord>> getBatchAsync(
            @Nonnull String collectionName,
            @Nonnull Collection<String> keys,
            boolean withEmbeddings) {
        Objects.requireNonNull(collectionName);
        Objects.requireNonNull(keys);
        return Flux.fromIterable(keys)
                .flatMap(key -> internalGetAsync(collectionName, key, withEmbeddings))
                .collect(Collectors.toCollection(ArrayList::new));
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
        return Flux.fromIterable(keys)
                .flatMap(key -> this.dbConnector.deleteAsync(collectionName, key))
                .then();
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

    /** Builds an JDBCMemoryStore. */
    public static class Builder implements SQLMemoryStoreBuilder {
        private Connection connection;

        /**
         * Builds and returns a MemoryStore instance with the specified database connection.
         *
         * @return A MemoryStore instance configured with the provided database connection.
         */
        @Override
        public MemoryStore build() {
            return new JDBCMemoryStore(new JDBCConnector(connection));
        }

        /**
         * Sets the database connection to be used by the JDBCMemoryStore being built.
         *
         * @param connection The Connection object representing the database connection.
         * @return The updated Builder instance to continue the building process.
         */
        @Override
        public Builder withConnection(Connection connection) {
            this.connection = connection;
            return this;
        }
    }
}
