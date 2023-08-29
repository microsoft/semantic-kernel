// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.postgresql;

import com.microsoft.semantickernel.connectors.memory.jdbc.JDBCMemoryStore;
import com.microsoft.semantickernel.connectors.memory.jdbc.SQLConnector;
import com.microsoft.semantickernel.connectors.memory.jdbc.SQLMemoryStore;
import java.sql.Connection;
import reactor.core.publisher.Mono;

public class PostgreSQLMemoryStore extends JDBCMemoryStore {
    public PostgreSQLMemoryStore(SQLConnector connector) {
        super(connector);
    }

    /** Builds a PostgreSQLMemoryStore. */
    public static class Builder implements SQLMemoryStore.Builder<PostgreSQLMemoryStore> {
        private Connection connection;

        /**
         * Builds and returns a PostgreSQLMemoryStore instance with the specified database
         * connection.
         *
         * @return A PostgreSQLMemoryStore instance configured with the provided PostgreSQL database
         *     connection.
         */
        @Override
        public PostgreSQLMemoryStore build() {
            return new PostgreSQLMemoryStore(new PostgreSQLConnector(connection));
        }

        /**
         * Asynchronously builds and returns a PostgreSQLMemoryStore instance with the specified
         * database connection.
         *
         * @return A Mono with a PostgreSQLMemoryStore instance configured with the provided
         *     database connection.
         */
        @Override
        public Mono<PostgreSQLMemoryStore> buildAsync() {
            PostgreSQLMemoryStore memoryStore = this.build();
            return memoryStore.initialiseDatabase().thenReturn(memoryStore);
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
