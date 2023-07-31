// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.sqlite;

import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;

public class Database {

    static class DatabaseEntry {
        private final String key;
        private final String metadata;
        private final String embedding;
        private final String timestamp;

        public DatabaseEntry(String key, String metadata, String embedding, String timestamp) {
            this.key = key;
            this.metadata = metadata;
            this.embedding = embedding;
            this.timestamp = timestamp;
        }

        public String getKey() {
            return key;
        }

        public String getMetadata() {
            return metadata;
        }

        public String getEmbedding() {
            return embedding;
        }

        public String getTimestamp() {
            return timestamp;
        }
    }

    private static final String TABLE_NAME = "SKMemoryTable";

    public Mono<Void> createTableAsync(Connection connection) {
        return Mono.fromRunnable(
                        () -> {
                            String query =
                                    "CREATE TABLE IF NOT EXISTS "
                                            + TABLE_NAME
                                            + " ("
                                            + "collection TEXT, "
                                            + "key TEXT, "
                                            + "metadata TEXT, "
                                            + "embedding TEXT, "
                                            + "timestamp TEXT, "
                                            + "PRIMARY KEY(collection, key))";
                            try (PreparedStatement statement = connection.prepareStatement(query)) {
                                statement.executeUpdate();
                            } catch (SQLException e) {
                                Mono.error(new SQLConnectorException("\"CREATE TABLE\" failed", e));
                            }
                        })
                .subscribeOn(Schedulers.boundedElastic())
                .then();
    }

    public Mono<Void> createCollectionAsync(Connection connection, String collectionName) {
        return Mono.fromRunnable(
                        () -> {
                            try {
                                if (doesCollectionExists(connection, collectionName)) {
                                    // Collection already exists
                                    return;
                                }
                            } catch (SQLException e) {
                                Mono.error(new SQLConnectorException(e.getMessage(), e));
                            }

                            String query = "INSERT INTO " + TABLE_NAME + " (collection) VALUES (?)";
                            try (PreparedStatement statement = connection.prepareStatement(query)) {
                                statement.setString(1, collectionName);
                                statement.executeUpdate();
                            } catch (SQLException e) {
                                Mono.error(new SQLConnectorException("\"INSERT INTO\" failed", e));
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
            String timestamp) {
        return Mono.fromRunnable(
                        () -> {
                            String query =
                                    "UPDATE "
                                            + TABLE_NAME
                                            + " SET metadata = ?, embedding = ?, timestamp = ?"
                                            + " WHERE collection = ? AND key = ?";
                            try (PreparedStatement statement = connection.prepareStatement(query)) {
                                statement.setString(1, metadata != null ? metadata : "");
                                statement.setString(2, embedding != null ? embedding : "");
                                statement.setString(3, timestamp != null ? timestamp : "");
                                statement.setString(4, collection);
                                statement.setString(5, key);
                                statement.executeUpdate();
                            } catch (SQLException e) {
                                Mono.error(new SQLConnectorException("\"UPDATE\" failed", e));
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
            String timestamp) {
        return Mono.fromRunnable(
                        () -> {
                            String query =
                                    "INSERT OR IGNORE INTO "
                                            + TABLE_NAME
                                            + " (collection, key, metadata, embedding, timestamp)"
                                            + " VALUES (?, ?, ?, ?, ?)";
                            try (PreparedStatement statement = connection.prepareStatement(query)) {
                                statement.setString(1, collection);
                                statement.setString(2, key);
                                statement.setString(3, metadata != null ? metadata : "");
                                statement.setString(4, embedding != null ? embedding : "");
                                statement.setString(5, timestamp != null ? timestamp : "");
                                statement.executeUpdate();
                            } catch (SQLException e) {
                                Mono.error(new SQLConnectorException("\"INSERT OR IGNORE INTO\" failed", e));
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
        String query = "SELECT DISTINCT(collection) FROM " + TABLE_NAME;
        try (PreparedStatement statement = connection.prepareStatement(query)) {
            ResultSet resultSet = statement.executeQuery();
            while (resultSet.next()) {
                String collection = resultSet.getString("collection");
                if (collectionName.equals(collection)) {
                    return true;
                }
            }
        }
        return false;
    }

    public Mono<List<String>> getCollectionsAsync(Connection connection) {
        return Mono.defer(
                        () -> {
                            List<String> collections = new ArrayList<>();
                            String query = "SELECT DISTINCT(collection) FROM " + TABLE_NAME;
                            try (PreparedStatement statement = connection.prepareStatement(query)) {
                                ResultSet resultSet = statement.executeQuery();
                                while (resultSet.next()) {
                                    String collection = resultSet.getString("collection");
                                    collections.add(collection);
                                }
                            } catch (SQLException e) {
                                Mono.error(new SQLConnectorException("\"SELECT DISTINCT\" failed", e));
                            }
                            return Mono.just(collections);
                        })
                .subscribeOn(Schedulers.boundedElastic());
    }

    public Mono<List<DatabaseEntry>> readAllAsync(Connection connection, String collectionName) {
        return Mono.defer(
                        () -> {
                            List<DatabaseEntry> entries = new ArrayList<>();
                            String query = "SELECT * FROM " + TABLE_NAME + " WHERE collection = ?";
                            try (PreparedStatement statement = connection.prepareStatement(query)) {
                                statement.setString(1, collectionName);
                                ResultSet resultSet = statement.executeQuery();
                                while (resultSet.next()) {
                                    String key = resultSet.getString("key");
                                    String metadata = resultSet.getString("metadata");
                                    String embedding = resultSet.getString("embedding");
                                    String timestamp = resultSet.getString("timestamp");
                                    entries.add(
                                            new DatabaseEntry(key, metadata, embedding, timestamp));
                                }
                            } catch (SQLException e) {
                                Mono.error(new SQLConnectorException("\"SELECT * FROM\" failed", e));
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
                                            + " WHERE collection = ? AND key = ?";
                            try (PreparedStatement statement = connection.prepareStatement(query)) {
                                statement.setString(1, collectionName);
                                statement.setString(2, key);
                                ResultSet resultSet = statement.executeQuery();
                                if (resultSet.next()) {
                                    String metadata = resultSet.getString("metadata");
                                    String embedding = resultSet.getString("embedding");
                                    String timestamp = resultSet.getString("timestamp");
                                    return Mono.just(
                                            new DatabaseEntry(key, metadata, embedding, timestamp));
                                }
                            } catch (SQLException e) {
                                Mono.error(new SQLConnectorException("\"SELECT * FROM\" failed", e));
                            }
                            return Mono.empty();
                        })
                .subscribeOn(Schedulers.boundedElastic());
    }

    public Mono<Void> deleteCollectionAsync(Connection connection, String collectionName) {
        return Mono.fromRunnable(
                        () -> {
                            String query = "DELETE FROM " + TABLE_NAME + " WHERE collection = ?";
                            try (PreparedStatement statement = connection.prepareStatement(query)) {
                                statement.setString(1, collectionName);
                                statement.executeUpdate();
                            } catch (SQLException e) {
                                Mono.error(new SQLConnectorException("\"DELETE FROM\" failed", e));
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
                                            + " WHERE collection = ? AND key = ?";
                            try (PreparedStatement statement = connection.prepareStatement(query)) {
                                statement.setString(1, collectionName);
                                statement.setString(2, key);
                                statement.executeUpdate();
                            } catch (SQLException e) {
                                Mono.error(new SQLConnectorException("\"DELETE FROM\" failed", e));
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
                                            + " WHERE collection = ? AND key IS NULL";
                            try (PreparedStatement statement = connection.prepareStatement(query)) {
                                statement.setString(1, collectionName);
                                statement.executeUpdate();
                            } catch (SQLException e) {
                                Mono.error(new SQLConnectorException("\"DELETE FROM\" failed", e));
                            }
                        })
                .subscribeOn(Schedulers.boundedElastic())
                .then();
    }
}
