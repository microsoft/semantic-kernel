// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.jdbc;

import com.microsoft.semantickernel.memory.MemoryException;
import com.microsoft.semantickernel.memory.MemoryException.ErrorCodes;
import java.io.Closeable;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import javax.annotation.Nullable;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

public class JDBCConnector implements SQLConnector, Closeable {
    protected final Connection connection;

    public JDBCConnector(Connection connection) {
        this.connection = connection;
    }

    // Convenience method to format a ZonedDateTime in a format acceptable to SQL
    protected static String formatDatetime(@Nullable ZonedDateTime datetime) {
        if (datetime == null) return "";
        return datetime.format(DateTimeFormatter.ISO_OFFSET_DATE_TIME);
    }

    // Convenience method to parse a SQL datetime string into a ZonedDateTime
    protected static ZonedDateTime parseDatetime(@Nullable String datetime) {
        if (datetime == null || datetime.isEmpty()) return null;
        return ZonedDateTime.parse(datetime, DateTimeFormatter.ISO_OFFSET_DATE_TIME);
    }

    protected static final String COLLECTIONS_TABLE_NAME = "SKCollectionTable";
    protected static final String TABLE_NAME = "SKMemoryTable";
    protected static final String INDEX_NAME = "SKMemoryIndex";

    /**
     * Returns the name of the table that stores the collection names.
     *
     * @return The name of the table that stores the collection names.
     */
    protected static String DEFAULT_COLLECTIONS_TABLE_NAME() {
        return COLLECTIONS_TABLE_NAME;
    }

    /**
     * Returns the name of the Semantic Kernel table.
     *
     * @return The name of the Semantic Kernel table.
     */
    protected static String DEFAULT_TABLE_NAME() {
        return TABLE_NAME;
    }

    /**
     * Returns the name of the index on the Semantic Kernel table.
     *
     * @return The name of the index on the Semantic Kernel table.
     */
    protected static String DEFAULT_INDEX_NAME() {
        return INDEX_NAME;
    }

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
                                            + "collectionId TEXT NOT NULL, "
                                            + "id TEXT NOT NULL, "
                                            + "metadata TEXT, "
                                            + "embedding TEXT, "
                                            + "timestamp TEXT, "
                                            + "PRIMARY KEY (collectionId, id), "
                                            + "FOREIGN KEY (collectionId) REFERENCES "
                                            + COLLECTIONS_TABLE_NAME
                                            + "(id)"
                                            + " )";

                            String createIndex =
                                    "CREATE INDEX IF NOT EXISTS "
                                            + INDEX_NAME
                                            + " ON "
                                            + TABLE_NAME
                                            + "(collectionId)";

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

    public Mono<String> upsertAsync(
            String collection,
            String key,
            String metadata,
            String embedding,
            ZonedDateTime timestamp) {
        return Mono.fromRunnable(
                        () -> {
                            String query =
                                    "INSERT OR REPLACE INTO "
                                            + TABLE_NAME
                                            + " (collectionId, id, metadata, embedding, timestamp)"
                                            + " VALUES (?, ?, ?, ?, ?)";
                            try (PreparedStatement statement =
                                    this.connection.prepareStatement(query)) {
                                statement.setString(1, collection);
                                statement.setString(2, key);
                                statement.setString(3, metadata != null ? metadata : "");
                                statement.setString(4, embedding != null ? embedding : "");
                                statement.setString(5, formatDatetime(timestamp));
                                statement.executeUpdate();
                            } catch (SQLException e) {
                                throw new SQLConnectorException(
                                        SQLConnectorException.ErrorCodes.SQL_ERROR,
                                        "\"INSERT OR REPLACE INTO\" failed",
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
                                    "INSERT OR REPLACE INTO "
                                            + TABLE_NAME
                                            + " (collectionId, id, metadata, embedding, timestamp)"
                                            + " VALUES (?, ?, ?, ?, ?)";
                            try (PreparedStatement statement =
                                    this.connection.prepareStatement(query)) {
                                for (DatabaseEntry entry : records) {
                                    statement.setString(1, collection);
                                    statement.setString(2, entry.getKey());
                                    statement.setString(
                                            3,
                                            entry.getMetadata() != null ? entry.getMetadata() : "");
                                    statement.setString(
                                            4,
                                            entry.getEmbedding() != null
                                                    ? entry.getEmbedding()
                                                    : "");
                                    statement.setString(5, formatDatetime(entry.getTimestamp()));
                                    statement.addBatch();
                                    keys.add(entry.getKey());
                                }

                                statement.executeBatch();
                            } catch (SQLException e) {
                                throw new SQLConnectorException(
                                        SQLConnectorException.ErrorCodes.SQL_ERROR,
                                        "\"INSERT OR REPLACE INTO\" failed",
                                        e);
                            }
                        })
                .subscribeOn(Schedulers.boundedElastic())
                .thenReturn(keys);
    }

    public Mono<Boolean> doesCollectionExistsAsync(String collectionName) {
        return Mono.fromCallable(() -> doesCollectionExists(collectionName))
                .subscribeOn(Schedulers.boundedElastic());
    }

    private boolean doesCollectionExists(String collectionName) throws SQLException {
        String query = "SELECT id FROM " + COLLECTIONS_TABLE_NAME + " WHERE id = ?";
        try (PreparedStatement statement = this.connection.prepareStatement(query)) {
            statement.setString(1, collectionName);
            ResultSet resultSet = statement.executeQuery();
            return resultSet.next();
        }
    }

    public Mono<List<String>> getCollectionsAsync() {
        return Mono.defer(
                        () -> {
                            List<String> collections = new ArrayList<>();
                            String query = "SELECT id FROM " + COLLECTIONS_TABLE_NAME;
                            try (PreparedStatement statement =
                                    this.connection.prepareStatement(query)) {
                                ResultSet resultSet = statement.executeQuery();
                                while (resultSet.next()) {
                                    String collection = resultSet.getString("id");
                                    collections.add(collection);
                                }
                            } catch (SQLException e) {
                                return Mono.error(
                                        new SQLConnectorException(
                                                SQLConnectorException.ErrorCodes.SQL_ERROR,
                                                "\"SELECT\" failed",
                                                e));
                            }
                            return Mono.just(collections);
                        })
                .subscribeOn(Schedulers.boundedElastic());
    }

    public Mono<List<DatabaseEntry>> readAllAsync(String collectionName) {
        return Mono.defer(
                        () -> {
                            List<DatabaseEntry> entries = new ArrayList<>();
                            String query =
                                    "SELECT * FROM " + TABLE_NAME + " WHERE collectionId = ?";
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

    public Mono<DatabaseEntry> readAsync(String collectionName, String key) {
        return Mono.defer(
                        () -> {
                            String query =
                                    "SELECT * FROM "
                                            + TABLE_NAME
                                            + " WHERE collectionId = ?"
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

    enum BatchOperation {
        SELECT,
        DELETE
    }

    protected String batchQuery(BatchOperation operation, Collection<String> keys) {
        String queryPrefix;
        switch (operation) {
            case SELECT:
                queryPrefix = "SELECT * FROM " + TABLE_NAME + " WHERE collectionId = ?";
                break;
            case DELETE:
                queryPrefix = "DELETE FROM " + TABLE_NAME + " WHERE collectionId = ?";
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
                            String query = batchQuery(BatchOperation.SELECT, keys);

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

    public Mono<Void> deleteCollectionAsync(String collectionName) {
        return Mono.fromRunnable(
                        () -> {
                            String query1 = "DELETE FROM " + TABLE_NAME + " WHERE collectionId = ?";
                            String query2 =
                                    "DELETE FROM " + COLLECTIONS_TABLE_NAME + " WHERE id = ?";
                            try (PreparedStatement statement =
                                            this.connection.prepareStatement(query1);
                                    PreparedStatement statement2 =
                                            this.connection.prepareStatement(query2)) {
                                statement.setString(1, collectionName);
                                statement.executeUpdate();
                                statement2.setString(1, collectionName);
                                if (statement2.executeUpdate() == 0) {
                                    throw new MemoryException(
                                            ErrorCodes.ATTEMPTED_TO_ACCESS_NONEXISTENT_COLLECTION);
                                }
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

    public Mono<Void> deleteAsync(String collectionName, String key) {
        return Mono.fromRunnable(
                        () -> {
                            String query =
                                    "DELETE FROM "
                                            + TABLE_NAME
                                            + " WHERE collectionId = ?"
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

    public Mono<Void> deleteBatchAsync(String collectionName, Collection<String> keys) {
        return Mono.fromRunnable(
                        () -> {
                            String query = batchQuery(BatchOperation.DELETE, keys);
                            try (PreparedStatement statement =
                                    this.connection.prepareStatement(query)) {
                                statement.setString(1, collectionName);
                                int index = 2;
                                for (String key : keys) {
                                    statement.setString(index++, key);
                                }
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

    public Mono<Void> deleteEmptyAsync(String collectionName) {
        return Mono.fromRunnable(
                        () -> {
                            String query =
                                    "DELETE FROM "
                                            + TABLE_NAME
                                            + " WHERE collectionId = ?"
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

    @Override
    public void close() {
        try {
            this.connection.close();
        } catch (SQLException e) {
            throw new SQLConnectorException(
                    SQLConnectorException.ErrorCodes.SQL_ERROR,
                    "Database access error while closing connection",
                    e);
        }
    }
}
