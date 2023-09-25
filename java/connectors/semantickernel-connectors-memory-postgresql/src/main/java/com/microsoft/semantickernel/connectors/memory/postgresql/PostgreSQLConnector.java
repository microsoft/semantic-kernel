// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.postgresql;

import com.microsoft.semantickernel.connectors.memory.jdbc.DatabaseEntry;
import com.microsoft.semantickernel.connectors.memory.jdbc.JDBCConnector;
import com.microsoft.semantickernel.connectors.memory.jdbc.SQLConnector;
import com.microsoft.semantickernel.connectors.memory.jdbc.SQLConnectorException;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.sql.Statement;
import java.time.ZonedDateTime;
import java.util.ArrayList;
import java.util.Collection;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

public class PostgreSQLConnector extends JDBCConnector implements SQLConnector {
    public PostgreSQLConnector(Connection connection) {
        super(connection);
    }

    @Override
    public Mono<Void> createTableAsync() {
        return Mono.fromRunnable(
                        () -> {
                            String createCollectionKeyTable =
                                    "CREATE TABLE IF NOT EXISTS "
                                            + COLLECTIONS_TABLE_NAME
                                            + " ("
                                            + "id TEXT PRIMARY KEY"
                                            + " )";

                            String createSKMemoryTable =
                                    "CREATE TABLE IF NOT EXISTS "
                                            + TABLE_NAME
                                            + " ("
                                            + "collection TEXT NOT NULL, "
                                            + "key TEXT NOT NULL, "
                                            + "metadata TEXT, "
                                            + "embedding TEXT, "
                                            + "timestamp TEXT, "
                                            + "PRIMARY KEY (collection, key), "
                                            + "FOREIGN KEY (collection) REFERENCES "
                                            + COLLECTIONS_TABLE_NAME
                                            + "(id)"
                                            + " )";

                            String createIndex =
                                    "CREATE INDEX IF NOT EXISTS "
                                            + INDEX_NAME
                                            + " ON "
                                            + TABLE_NAME
                                            + "(collection)";

                            try (Statement statement = this.connection.createStatement()) {
                                statement.addBatch(createCollectionKeyTable);
                                statement.addBatch(createSKMemoryTable);
                                statement.addBatch(createIndex);
                                statement.executeBatch();
                            } catch (SQLException e) {
                                throw new SQLConnectorException(
                                        SQLConnectorException.ErrorCodes.SQL_ERROR,
                                        "\"CREATE TABLE\" failed",
                                        e);
                            }
                        })
                .subscribeOn(Schedulers.boundedElastic())
                .then();
    }

    @Override
    public Mono<String> upsertAsync(
            String collection,
            String key,
            String metadata,
            String embedding,
            ZonedDateTime timestamp) {
        final String upsertKey = resolveKey(key);
        return Mono.fromRunnable(
                        () -> {
                            String query =
                                    "INSERT INTO "
                                            + TABLE_NAME
                                            + " (collection, key, metadata, embedding, timestamp)"
                                            + " VALUES (?, ?, ?, ?, ?) ON CONFLICT (collection,"
                                            + " key) DO UPDATE SET metadata = ?, embedding = ?,"
                                            + " timestamp = ?";
                            try (PreparedStatement statement =
                                    this.connection.prepareStatement(query)) {
                                String metadataString = metadata != null ? metadata : "";
                                String embeddingString = embedding != null ? embedding : "";
                                String timestampString = formatDatetime(timestamp);
                                statement.setString(1, collection);
                                statement.setString(2, upsertKey);
                                statement.setString(3, metadataString);
                                statement.setString(4, embeddingString);
                                statement.setString(5, timestampString);
                                statement.setString(6, metadataString);
                                statement.setString(7, embeddingString);
                                statement.setString(8, timestampString);
                                statement.executeUpdate();
                            } catch (SQLException e) {
                                throw new SQLConnectorException(
                                        SQLConnectorException.ErrorCodes.SQL_ERROR,
                                        "\"INSERT INTO\" failed",
                                        e);
                            }
                        })
                .subscribeOn(Schedulers.boundedElastic())
                .thenReturn(upsertKey);
    }

    @Override
    public Mono<Collection<String>> upsertBatchAsync(
            String collection, Collection<DatabaseEntry> records) {
        Collection<String> keys = new ArrayList<>();
        return Mono.fromRunnable(
                        () -> {
                            String query =
                                    "INSERT INTO "
                                            + TABLE_NAME
                                            + " (collection, key, metadata, embedding, timestamp)"
                                            + " VALUES (?, ?, ?, ?, ?) ON CONFLICT (collection,"
                                            + " key) DO UPDATE SET metadata = ?, embedding = ?,"
                                            + " timestamp = ?";
                            try (PreparedStatement statement =
                                    this.connection.prepareStatement(query)) {
                                for (DatabaseEntry entry : records) {
                                    final String upsertKey = resolveKey(entry.getKey());
                                    String metadataString =
                                            entry.getMetadata() != null ? entry.getMetadata() : "";
                                    String embeddingString =
                                            entry.getEmbedding() != null
                                                    ? entry.getEmbedding()
                                                    : "";
                                    String timestampString = formatDatetime(entry.getTimestamp());
                                    statement.setString(1, collection);
                                    statement.setString(2, upsertKey);
                                    statement.setString(3, metadataString);
                                    statement.setString(4, embeddingString);
                                    statement.setString(5, timestampString);
                                    statement.setString(6, metadataString);
                                    statement.setString(7, embeddingString);
                                    statement.setString(8, timestampString);
                                    statement.addBatch();
                                    keys.add(upsertKey);
                                }

                                statement.executeBatch();
                            } catch (SQLException e) {
                                throw new SQLConnectorException(
                                        SQLConnectorException.ErrorCodes.SQL_ERROR,
                                        "\"INSERT INTO\" failed",
                                        e);
                            }
                        })
                .subscribeOn(Schedulers.boundedElastic())
                .thenReturn(keys);
    }
}
