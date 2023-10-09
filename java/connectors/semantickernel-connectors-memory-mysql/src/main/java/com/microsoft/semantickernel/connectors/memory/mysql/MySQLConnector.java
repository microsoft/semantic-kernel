// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.mysql;

import com.microsoft.semantickernel.connectors.memory.jdbc.DatabaseEntry;
import com.microsoft.semantickernel.connectors.memory.jdbc.JDBCConnector;
import com.microsoft.semantickernel.connectors.memory.jdbc.SQLConnector;
import com.microsoft.semantickernel.connectors.memory.jdbc.SQLConnectorException;
import java.sql.*;
import java.time.ZonedDateTime;
import java.util.ArrayList;
import java.util.Collection;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

public class MySQLConnector extends JDBCConnector implements SQLConnector {
    public MySQLConnector(Connection connection) {
        super(connection);
    }

    @Override
    public Mono<Void> createTableAsync() {
        return Mono.fromRunnable(
                        () -> {
                            try (Statement statement = connection.createStatement()) {
                                String createCollectionKeyTable =
                                        "CREATE TABLE IF NOT EXISTS "
                                                + COLLECTIONS_TABLE_NAME
                                                + " (id VARCHAR(255) PRIMARY KEY);";

                                String createSKMemoryTable =
                                        "CREATE TABLE IF NOT EXISTS "
                                                + TABLE_NAME
                                                + " ("
                                                + "collectionId VARCHAR(255) NOT NULL, "
                                                + "id VARCHAR(255) NOT NULL, "
                                                + "metadata TEXT, "
                                                + "embedding TEXT, "
                                                + "timestamp TEXT, "
                                                + "PRIMARY KEY (collectionId, id), "
                                                + "FOREIGN KEY (collectionId) REFERENCES "
                                                + COLLECTIONS_TABLE_NAME
                                                + "(id));";

                                statement.addBatch(createCollectionKeyTable);
                                statement.addBatch(createSKMemoryTable);

                                boolean indexExists = doesIndexExist(statement);

                                if (!indexExists) {
                                    String createIndex =
                                            "CREATE INDEX "
                                                    + INDEX_NAME
                                                    + " ON "
                                                    + TABLE_NAME
                                                    + "(collectionId)";
                                    statement.addBatch(createIndex);
                                }

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

    private boolean doesIndexExist(Statement statement) throws SQLException {
        DatabaseMetaData meta = connection.getMetaData();
        try (ResultSet indexes = meta.getIndexInfo(null, null, TABLE_NAME, false, false)) {
            while (indexes.next()) {
                String existingIndexName = indexes.getString("INDEX_NAME");
                if (existingIndexName != null && existingIndexName.equalsIgnoreCase(INDEX_NAME)) {
                    return true;
                }
            }
        }
        return false;
    }

    @Override
    public Mono<String> upsertAsync(
            String collection,
            String key,
            String metadata,
            String embedding,
            ZonedDateTime timestamp) {
        return Mono.fromRunnable(
                        () -> {
                            String query =
                                    "INSERT INTO "
                                            + TABLE_NAME
                                            + " (collectionId, id, metadata, embedding, timestamp)"
                                            + " VALUES (?, ?, ?, ?, ?) ON DUPLICATE KEY UPDATE"
                                            + " metadata = VALUES(metadata), embedding ="
                                            + " VALUES(embedding), timestamp = VALUES(timestamp)";
                            try (PreparedStatement statement =
                                    this.connection.prepareStatement(query)) {
                                String metadataString = metadata != null ? metadata : "";
                                String embeddingString = embedding != null ? embedding : "";
                                String timestampString = formatDatetime(timestamp);
                                statement.setString(1, collection);
                                statement.setString(2, key);
                                statement.setString(3, metadataString);
                                statement.setString(4, embeddingString);
                                statement.setString(5, timestampString);
                                statement.executeUpdate();
                            } catch (SQLException e) {
                                throw new SQLConnectorException(
                                        SQLConnectorException.ErrorCodes.SQL_ERROR,
                                        "\"INSERT INTO\" failed",
                                        e);
                            }
                        })
                .subscribeOn(Schedulers.boundedElastic())
                .thenReturn(key);
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
                                            + " (collectionId, id, metadata, embedding, timestamp)"
                                            + " VALUES (?, ?, ?, ?, ?) ON DUPLICATE KEY UPDATE"
                                            + " metadata = VALUES(metadata), embedding ="
                                            + " VALUES(embedding), timestamp = VALUES(timestamp)";
                            try (PreparedStatement statement =
                                    this.connection.prepareStatement(query)) {
                                for (DatabaseEntry entry : records) {
                                    String metadataString =
                                            entry.getMetadata() != null ? entry.getMetadata() : "";
                                    String embeddingString =
                                            entry.getEmbedding() != null
                                                    ? entry.getEmbedding()
                                                    : "";
                                    String timestampString = formatDatetime(entry.getTimestamp());
                                    statement.setString(1, collection);
                                    statement.setString(2, entry.getKey());
                                    statement.setString(3, metadataString);
                                    statement.setString(4, embeddingString);
                                    statement.setString(5, timestampString);
                                    statement.addBatch();
                                    keys.add(entry.getKey());
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
