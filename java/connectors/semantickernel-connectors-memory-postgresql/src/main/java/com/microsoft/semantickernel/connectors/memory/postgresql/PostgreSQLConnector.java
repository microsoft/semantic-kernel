package com.microsoft.semantickernel.connectors.memory.postgresql;

import com.microsoft.semantickernel.connectors.memory.jdbc.Connector;
import com.microsoft.semantickernel.connectors.memory.jdbc.JDBCConnector;
import com.microsoft.semantickernel.connectors.memory.jdbc.SQLConnectorException;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.sql.Statement;
import java.time.ZonedDateTime;

public class PostgreSQLConnector extends JDBCConnector implements Connector {
    @Override
    public Mono<Void> createTableAsync(Connection connection) {
        return Mono.fromRunnable(
                        () -> {
                            String createCollectionKeyTable =
                                    "CREATE TABLE IF NOT EXISTS "
                                            + COLLECTIONS_TABLE_NAME
                                            + " ("
                                            + "id SERIAL PRIMARY KEY, "
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
                                            + "UNIQUE (collection, key), "
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
                                        "\"CREATE TABLE\" failed", e);
                            }
                        })
                .subscribeOn(Schedulers.boundedElastic())
                .then();
    }

    @Override
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
                                    "INSERT INTO "
                                            + TABLE_NAME
                                            + " (collection, key, metadata, embedding, timestamp)"
                                            + " VALUES ((SELECT id FROM "
                                            + COLLECTIONS_TABLE_NAME
                                            + " WHERE name = ?), ?, ?, ?, ?)"
                                            + " ON CONFLICT (collection, key) DO NOTHING";
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
                                        "\"INSERT INTO\" failed", e);
                            }
                        })
                .subscribeOn(Schedulers.boundedElastic())
                .then();
    }
}
