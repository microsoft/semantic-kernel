// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.sqlite;

import com.microsoft.semantickernel.memory.DataEntryBase;
import com.microsoft.semantickernel.memory.MemoryException;
import com.microsoft.semantickernel.memory.MemoryException.ErrorCodes;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import org.sqlite.SQLiteErrorCode;
import org.sqlite.SQLiteException;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

public class Database {

    static class DatabaseEntry extends DataEntryBase {
        private final String metadata;
        private final String embedding;

        public DatabaseEntry(
                String key, String metadata, String embedding, ZonedDateTime timestamp) {
            super(key, timestamp);
            this.metadata = metadata;
            this.embedding = embedding;
        }

        public String getMetadata() {
            return metadata;
        }

        public String getEmbedding() {
            return embedding;
        }
    }

    // Convenience method to format a ZonedDateTime in a format acceptable to SQLite
    private static String formatDatetime(ZonedDateTime datetime) {
        if (datetime == null) return "";
        return datetime.format(DateTimeFormatter.ISO_OFFSET_DATE_TIME);
    }

    // Convenience method to parse a SQLite datetime string into a ZonedDateTime
    private static ZonedDateTime parseDatetime(String datetime) {
        if (datetime == null || datetime.isEmpty()) return null;
        return ZonedDateTime.parse(datetime, DateTimeFormatter.ISO_OFFSET_DATE_TIME);
    }

    private static final String COLLECTIONS_TABLE_NAME = "SKCollectionTable";
    private static final String TABLE_NAME = "SKMemoryTable";
    private static final String INDEX_NAME = "SKMemoryIndex";

    public Mono<Void> createTableAsync(Connection connection) {
        return Mono.fromRunnable(
                        () -> {
                            String createCollectionKeyTable =
                                    "CREATE TABLE IF NOT EXISTS "
                                            + COLLECTIONS_TABLE_NAME
                                            + " ("
                                            + "id INTEGER PRIMARY KEY, "
                                            + "name TEXT NOT NULL UNIQUE"
                                            + " )";

                            String createSKMemoryTable =
                                    "CREATE TABLE IF NOT EXISTS "
                                            + TABLE_NAME
                                            + " ("
                                            + "collection INTEGER, "
                                            + "key TEXT, "
                                            + "metadata TEXT, "
                                            + "embedding TEXT, "
                                            + "timestamp TEXT, "
                                            + "FOREIGN KEY(collection) REFERENCES "
                                            + COLLECTIONS_TABLE_NAME
                                            + "(id)"
                                            + " )";

                            String createIndex =
                                    "CREATE INDEX IF NOT EXISTS "
                                            + INDEX_NAME
                                            + " ON "
                                            + TABLE_NAME
                                            + "(collection)";

                            try (Statement statement = connection.createStatement()) {
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

    public Mono<Void> createCollectionAsync(Connection connection, String collectionName) {
        return Mono.fromRunnable(
                        () -> {
                            String query =
                                    "INSERT INTO " + COLLECTIONS_TABLE_NAME + " (name) VALUES (?)";
                            try (PreparedStatement statement = connection.prepareStatement(query)) {
                                statement.setString(1, collectionName);
                                statement.executeUpdate();
                            } catch (SQLiteException e) {
                                if (e.getResultCode() != SQLiteErrorCode.SQLITE_CONSTRAINT_UNIQUE) {
                                    throw new SQLConnectorException(
                                            SQLConnectorException.ErrorCodes.SQL_ERROR,
                                            "\"INSERT INTO\" failed",
                                            e);
                                }
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

    public Mono<Void> updateAsync(
            Connection connection,
            String collection,
            String key,
            String metadata,
            String embedding,
            ZonedDateTime timestamp) {

        return Mono.fromRunnable(
                        () -> {
                            String query =
                                    "UPDATE "
                                            + TABLE_NAME
                                            + " SET metadata = ?, embedding = ?, timestamp = ?"
                                            + " WHERE collection = (SELECT id FROM "
                                            + COLLECTIONS_TABLE_NAME
                                            + " WHERE name = ?)"
                                            + " AND key = ?";
                            try (PreparedStatement statement = connection.prepareStatement(query)) {
                                statement.setString(1, metadata != null ? metadata : "");
                                statement.setString(2, embedding != null ? embedding : "");
                                statement.setString(3, formatDatetime(timestamp));
                                statement.setString(4, collection);
                                statement.setString(5, key != null && !key.isEmpty() ? key : null);
                                statement.executeUpdate();
                            } catch (SQLException e) {
                                throw new SQLConnectorException(
                                        SQLConnectorException.ErrorCodes.SQL_ERROR,
                                        "\"UPDATE\" failed",
                                        e);
                            }
                        })
                .subscribeOn(Schedulers.boundedElastic())
                .then();
    }

    public Mono<Void> insertOrIgnoreAsync(
            Connection connection,
            String collection,
            String key,
            String metadata,
            String embedding,
            ZonedDateTime timestamp) {
        return Mono.fromRunnable(
                        () -> {
                            String query =
                                    "INSERT OR IGNORE INTO "
                                            + TABLE_NAME
                                            + " (collection, key, metadata, embedding, timestamp)"
                                            + " VALUES ((SELECT id FROM "
                                            + COLLECTIONS_TABLE_NAME
                                            + " WHERE name = ?), ?, ?, ?, ?)";
                            try (PreparedStatement statement = connection.prepareStatement(query)) {
                                statement.setString(1, collection);
                                statement.setString(2, key);
                                statement.setString(3, metadata != null ? metadata : "");
                                statement.setString(4, embedding != null ? embedding : "");
                                statement.setString(5, formatDatetime(timestamp));
                                statement.executeUpdate();
                            } catch (SQLException e) {
                                throw new SQLConnectorException(
                                        SQLConnectorException.ErrorCodes.SQL_ERROR,
                                        "\"INSERT OR IGNORE INTO\" failed",
                                        e);
                            }
                        })
                .subscribeOn(Schedulers.boundedElastic())
                .then();
    }

    public Mono<Boolean> doesCollectionExistsAsync(Connection connection, String collectionName) {
        return Mono.fromCallable(() -> doesCollectionExists(connection, collectionName))
                .subscribeOn(Schedulers.boundedElastic());
    }

    private boolean doesCollectionExists(Connection connection, String collectionName)
            throws SQLException {
        String query = "SELECT name FROM " + COLLECTIONS_TABLE_NAME + " WHERE name = ?";
        try (PreparedStatement statement = connection.prepareStatement(query)) {
            statement.setString(1, collectionName);
            ResultSet resultSet = statement.executeQuery();
            return resultSet.next();
        }
    }

    public Mono<List<String>> getCollectionsAsync(Connection connection) {
        return Mono.defer(
                        () -> {
                            List<String> collections = new ArrayList<>();
                            String query = "SELECT name FROM " + COLLECTIONS_TABLE_NAME;
                            try (PreparedStatement statement = connection.prepareStatement(query)) {
                                ResultSet resultSet = statement.executeQuery();
                                while (resultSet.next()) {
                                    String collection = resultSet.getString("name");
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

    public Mono<List<DatabaseEntry>> readAllAsync(Connection connection, String collectionName) {
        return Mono.defer(
                        () -> {
                            List<DatabaseEntry> entries = new ArrayList<>();
                            String query =
                                    "SELECT * FROM "
                                            + TABLE_NAME
                                            + " WHERE collection ="
                                            + " (SELECT id FROM "
                                            + COLLECTIONS_TABLE_NAME
                                            + " WHERE name = ?)";
                            try (PreparedStatement statement = connection.prepareStatement(query)) {
                                statement.setString(1, collectionName);
                                ResultSet resultSet = statement.executeQuery();
                                while (resultSet.next()) {
                                    String key = resultSet.getString("key");
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

    public Mono<DatabaseEntry> readAsync(Connection connection, String collectionName, String key) {
        return Mono.defer(
                        () -> {
                            String query =
                                    "SELECT * FROM "
                                            + TABLE_NAME
                                            + " WHERE collection ="
                                            + " (SELECT id FROM "
                                            + COLLECTIONS_TABLE_NAME
                                            + " WHERE name = ?)"
                                            + " AND key = ?";
                            try (PreparedStatement statement = connection.prepareStatement(query)) {
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

    public Mono<Void> deleteCollectionAsync(Connection connection, String collectionName) {
        return Mono.fromRunnable(
                        () -> {
                            String query1 =
                                    "DELETE FROM "
                                            + TABLE_NAME
                                            + " WHERE collection ="
                                            + " (SELECT id FROM "
                                            + COLLECTIONS_TABLE_NAME
                                            + " WHERE name = ?)";
                            String query2 =
                                    "DELETE FROM " + COLLECTIONS_TABLE_NAME + " WHERE name = ?";
                            try (PreparedStatement statement = connection.prepareStatement(query1);
                                    PreparedStatement statement2 =
                                            connection.prepareStatement(query2)) {
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

    public Mono<Void> deleteAsync(Connection connection, String collectionName, String key) {
        return Mono.fromRunnable(
                        () -> {
                            String query =
                                    "DELETE FROM "
                                            + TABLE_NAME
                                            + " WHERE collection ="
                                            + " (SELECT id FROM "
                                            + COLLECTIONS_TABLE_NAME
                                            + " WHERE name = ?)"
                                            + " AND key = ?";
                            try (PreparedStatement statement = connection.prepareStatement(query)) {
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

    public Mono<Void> deleteEmptyAsync(Connection connection, String collectionName) {
        return Mono.fromRunnable(
                        () -> {
                            String query =
                                    "DELETE FROM "
                                            + TABLE_NAME
                                            + " WHERE collection ="
                                            + " (SELECT id FROM "
                                            + COLLECTIONS_TABLE_NAME
                                            + " WHERE name = ?)"
                                            + " AND key is NULL";
                            try (PreparedStatement statement = connection.prepareStatement(query)) {
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
