package com.microsoft.semantickernel.connectors.memory.jdbc;

import com.microsoft.semantickernel.memory.DataEntryBase;
import reactor.core.publisher.Mono;

import java.sql.Connection;
import java.time.ZonedDateTime;
import java.util.List;

public interface Connector {
    Mono<Void> createTableAsync(Connection connection);

    Mono<Void> createCollectionAsync(Connection connection, String collectionName);

    Mono<Void> updateAsync(
            Connection connection,
            String collection,
            String key,
            String metadata,
            String embedding,
            ZonedDateTime timestamp);

    Mono<Void> insertOrIgnoreAsync(
            Connection connection,
            String collection,
            String key,
            String metadata,
            String embedding,
            ZonedDateTime timestamp);

    Mono<Boolean> doesCollectionExistsAsync(Connection connection, String collectionName);

    Mono<List<String>> getCollectionsAsync(Connection connection);

    Mono<List<DatabaseEntry>> readAllAsync(Connection connection, String collectionName);

    Mono<DatabaseEntry> readAsync(Connection connection, String collectionName, String key);

    Mono<Void> deleteCollectionAsync(Connection connection, String collectionName);

    Mono<Void> deleteAsync(Connection connection, String collectionName, String key);

    Mono<Void> deleteEmptyAsync(Connection connection, String collectionName);
}
