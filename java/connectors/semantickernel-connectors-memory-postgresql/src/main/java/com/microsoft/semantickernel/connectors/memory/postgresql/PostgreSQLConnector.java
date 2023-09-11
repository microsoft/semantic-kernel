// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.postgresql;

import com.microsoft.semantickernel.connectors.memory.jdbc.JDBCConnector;
import com.microsoft.semantickernel.connectors.memory.jdbc.SQLConnector;
import com.microsoft.semantickernel.connectors.memory.jdbc.SQLConnectorException;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.sql.Statement;
import java.time.ZonedDateTime;
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
                                            + "collection TEXT, "
                                            + "key TEXT, "
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
    public Mono<Void> insertOrIgnoreAsync(
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
                                            + " (collection, key, metadata, embedding, timestamp)"
                                            + " VALUES (?, ?, ?, ?, ?)"
                                            + " ON CONFLICT (collection, key) DO NOTHING";
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
                                        "\"INSERT INTO\" failed",
                                        e);
                            }
                        })
                .subscribeOn(Schedulers.boundedElastic())
                .then();
    }
}
