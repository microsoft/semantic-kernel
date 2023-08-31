// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.postgresql;

import com.microsoft.semantickernel.connectors.memory.jdbc.JDBCMemoryStore;
import com.microsoft.semantickernel.connectors.memory.jdbc.SQLConnector;
import com.microsoft.semantickernel.connectors.memory.jdbc.SQLMemoryStore;
import java.sql.Connection;
import javax.annotation.CheckReturnValue;
import reactor.core.publisher.Mono;

public class PostgreSQLMemoryStore extends JDBCMemoryStore {
    private PostgreSQLMemoryStore(SQLConnector connector) {
        super(connector);
    }

    /** Builds a PostgreSQLMemoryStore. */
    public static class Builder implements SQLMemoryStore.Builder<PostgreSQLMemoryStore> {
        private Connection connection;

        /**
         * Builds and returns a PostgreSQLMemoryStore instance with the specified database
         * connection. The build process will connect to the database and create the required
         * tables.
         *
         * @return A PostgreSQLMemoryStore instance configured with the provided database
         *     connection.
         * @deprecated Use {@link #buildAsync()} instead.
         */
        @Override
        @Deprecated
        public PostgreSQLMemoryStore build() {
            return this.buildAsync().block();
        }

        /**
         * Asynchronously builds and returns a PostgreSQLMemoryStore instance with the specified
         * database connection.
         *
         * @return A Mono with a PostgreSQLMemoryStore instance configured with the provided
         *     database connection.
         */
        @Override
        @CheckReturnValue
        public Mono<PostgreSQLMemoryStore> buildAsync() {
            PostgreSQLConnector connector = new PostgreSQLConnector(connection);
            PostgreSQLMemoryStore memoryStore = new PostgreSQLMemoryStore(connector);
            return connector.createTableAsync().thenReturn(memoryStore);
        }

        /**
         * Sets the PostgreSQL database connection to be used by the PostgreSQL memory store being
         * built.
         *
         * @param connection The Connection object representing the PostgreSQL database connection.
         * @return The updated Builder instance to continue the building process for a
         *     PostgreSQLMemoryStore.
         */
        @Override
        public Builder withConnection(Connection connection) {
            this.connection = connection;
            return this;
        }
    }
}
