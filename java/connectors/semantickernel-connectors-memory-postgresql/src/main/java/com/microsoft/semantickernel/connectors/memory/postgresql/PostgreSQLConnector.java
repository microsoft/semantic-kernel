package com.microsoft.semantickernel.connectors.memory.postgresql;

import com.microsoft.semantickernel.connectors.memory.jdbc.Connector;
import com.microsoft.semantickernel.connectors.memory.jdbc.JDBCConnector;
import com.microsoft.semantickernel.connectors.memory.jdbc.SQLConnectorException;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

import java.sql.Connection;
import java.sql.SQLException;
import java.sql.Statement;

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
                                throw new SQLConnectorException("\"CREATE TABLE\" failed", e);
                            }
                        })
                .subscribeOn(Schedulers.boundedElastic())
                .then();
    }
}
