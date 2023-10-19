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
import java.util.List;
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
                                                + "collection VARCHAR(255) NOT NULL, "
                                                + "id VARCHAR(255) NOT NULL, "
                                                + "metadata TEXT, "
                                                + "embedding TEXT, "
                                                + "timestamp TEXT, "
                                                + "PRIMARY KEY (collection, id), "
                                                + "FOREIGN KEY (collection) REFERENCES "
                                                + COLLECTIONS_TABLE_NAME
                                                + "(id));";

                                statement.addBatch(createCollectionKeyTable);
                                statement.addBatch(createSKMemoryTable);

                                boolean indexExists = doesIndexExist();

                                if (!indexExists) {
                                    String createIndex =
                                            "CREATE INDEX "
                                                    + INDEX_NAME
                                                    + " ON "
                                                    + TABLE_NAME
                                                    + "(collection)";
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

    private boolean doesIndexExist() throws SQLException {
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
    public Mono<Void> createCollectionAsync(String collectionName) {
        return Mono.fromRunnable(
                        () -> {
                            String query =
                                    "INSERT INTO " + COLLECTIONS_TABLE_NAME + " (id) VALUES (?)";
                            try (PreparedStatement statement =
                                    this.connection.prepareStatement(query)) {
                                statement.setString(1, collectionName);
                                statement.executeUpdate();
                            } catch (SQLException e) {
                                throw new SQLConnectorException(
                                        SQLConnectorException.ErrorCodes.SQL_ERROR,
                                        "\"INSERT INTO\" failed",
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
        return Mono.fromRunnable(
                        () -> {
                            String query =
                                    "INSERT INTO "
                                            + TABLE_NAME
                                            + " (collection, id, metadata, embedding, timestamp)"
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
                                            + " (collection, id, metadata, embedding, timestamp)"
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

    @Override
    public Mono<List<DatabaseEntry>> readAllAsync(String collectionName) {
        return Mono.defer(
                        () -> {
                            List<DatabaseEntry> entries = new ArrayList<>();
                            String query = "SELECT * FROM " + TABLE_NAME + " WHERE collection = ?";
                            try (PreparedStatement statement =
                                    this.connection.prepareStatement(query)) {
                                statement.setString(1, collectionName);
                                ResultSet resultSet = statement.executeQuery();
                                while (resultSet.next()) {
                                    String key = resultSet.getString("id");
                                    String metadata = resultSet.getString("metadata");
                                    String embedding = resultSet.getString("embedding");
                                    String timestamp = resultSet.getString("timestamp");
                                    ZonedDateTime zonedDateTime = parseDatetime(timestamp);
                                    entries.add(
                                            new DatabaseEntry(
                                                    key, metadata, embedding, zonedDateTime));
                                }
                            } catch (SQLException e) {
                                return Mono.error(
                                        new SQLConnectorException(
                                                SQLConnectorException.ErrorCodes.SQL_ERROR,
                                                "\"SELECT * FROM\" failed",
                                                e));
                            }
                            return Mono.just(entries);
                        })
                .subscribeOn(Schedulers.boundedElastic());
    }

    @Override
    public Mono<DatabaseEntry> readAsync(String collectionName, String key) {
        return Mono.defer(
                        () -> {
                            String query =
                                    "SELECT * FROM "
                                            + TABLE_NAME
                                            + " WHERE collection = ?"
                                            + " AND id = ?";
                            try (PreparedStatement statement =
                                    this.connection.prepareStatement(query)) {
                                statement.setString(1, collectionName);
                                statement.setString(2, key != null && !key.isEmpty() ? key : null);
                                ResultSet resultSet = statement.executeQuery();
                                if (resultSet.next()) {
                                    String metadata = resultSet.getString("metadata");
                                    String embedding = resultSet.getString("embedding");
                                    String timestamp = resultSet.getString("timestamp");
                                    ZonedDateTime zonedDateTime = parseDatetime(timestamp);
                                    return Mono.just(
                                            new DatabaseEntry(
                                                    key, metadata, embedding, zonedDateTime));
                                }
                            } catch (SQLException e) {
                                return Mono.error(
                                        new SQLConnectorException(
                                                SQLConnectorException.ErrorCodes.SQL_ERROR,
                                                "\"SELECT * FROM\" failed",
                                                e));
                            }
                            return Mono.empty();
                        })
                .subscribeOn(Schedulers.boundedElastic());
    }

    @Override
    protected String batchQuery(JDBCConnector.BatchOperation operation, Collection<String> keys) {
        String queryPrefix;
        switch (operation) {
            case SELECT:
                queryPrefix = "SELECT * FROM " + TABLE_NAME + " WHERE collection = ?";
                break;
            case DELETE:
                queryPrefix = "DELETE FROM " + TABLE_NAME + " WHERE collection = ?";
                break;
            default:
                throw new IllegalArgumentException("Invalid batch operation");
        }
        StringBuilder queryBuilder = new StringBuilder(queryPrefix);
        queryBuilder.append(" AND id IN (");

        // Add placeholders for each key
        for (int i = 0; i < keys.size(); i++) {
            queryBuilder.append("?");
            if (i < keys.size() - 1) {
                queryBuilder.append(",");
            }
        }

        queryBuilder.append(")");
        return queryBuilder.toString();
    }

    @Override
    public Mono<Collection<DatabaseEntry>> readBatchAsync(
            String collectionName, Collection<String> keys) {
        return Mono.defer(
                        () -> {
                            Collection<DatabaseEntry> entries = new ArrayList<>();
                            String query = batchQuery(JDBCConnector.BatchOperation.SELECT, keys);

                            try (PreparedStatement statement =
                                    this.connection.prepareStatement(query)) {
                                statement.setString(1, collectionName);
                                int index = 2;
                                for (String key : keys) {
                                    statement.setString(index++, key);
                                }
                                ResultSet resultSet = statement.executeQuery();

                                while (resultSet.next()) {
                                    String key = resultSet.getString("id");
                                    String metadata = resultSet.getString("metadata");
                                    String embedding = resultSet.getString("embedding");
                                    String timestamp = resultSet.getString("timestamp");
                                    ZonedDateTime zonedDateTime = parseDatetime(timestamp);
                                    entries.add(
                                            new DatabaseEntry(
                                                    key, metadata, embedding, zonedDateTime));
                                }
                            } catch (SQLException e) {
                                return Mono.error(
                                        new SQLConnectorException(
                                                SQLConnectorException.ErrorCodes.SQL_ERROR,
                                                "\"SELECT * FROM\" failed",
                                                e));
                            }
                            return Mono.just(entries);
                        })
                .subscribeOn(Schedulers.boundedElastic());
    }

    @Override
    public Mono<Void> deleteAsync(String collectionName, String key) {
        return Mono.fromRunnable(
                        () -> {
                            String query =
                                    "DELETE FROM "
                                            + TABLE_NAME
                                            + " WHERE collection = ?"
                                            + " AND id = ?";
                            try (PreparedStatement statement =
                                    this.connection.prepareStatement(query)) {
                                statement.setString(1, collectionName);
                                statement.setString(2, key != null && !key.isEmpty() ? key : null);
                                statement.executeUpdate();
                            } catch (SQLException e) {
                                throw new SQLConnectorException(
                                        SQLConnectorException.ErrorCodes.SQL_ERROR,
                                        "\"DELETE FROM\" failed",
                                        e);
                            }
                        })
                .subscribeOn(Schedulers.boundedElastic())
                .then();
    }

    @Override
    public Mono<Void> deleteEmptyAsync(String collectionName) {
        return Mono.fromRunnable(
                        () -> {
                            String query =
                                    "DELETE FROM "
                                            + TABLE_NAME
                                            + " WHERE collection = ?"
                                            + " AND id is NULL";
                            try (PreparedStatement statement =
                                    this.connection.prepareStatement(query)) {
                                statement.setString(1, collectionName);
                                statement.executeUpdate();
                            } catch (SQLException e) {
                                throw new SQLConnectorException(
                                        SQLConnectorException.ErrorCodes.SQL_ERROR,
                                        "\"DELETE FROM\" failed",
                                        e);
                            }
                        })
                .subscribeOn(Schedulers.boundedElastic())
                .then();
    }
}
