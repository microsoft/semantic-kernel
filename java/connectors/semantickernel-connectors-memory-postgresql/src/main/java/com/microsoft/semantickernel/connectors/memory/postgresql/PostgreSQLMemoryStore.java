// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.postgresql;

import com.microsoft.semantickernel.connectors.memory.jdbc.SQLConnector;
import com.microsoft.semantickernel.connectors.memory.jdbc.JDBCMemoryStore;
import com.microsoft.semantickernel.connectors.memory.jdbc.SQLMemoryStoreBuilder;
import com.microsoft.semantickernel.memory.MemoryStore;
import reactor.core.publisher.Mono;

import java.sql.Connection;

public class PostgreSQLMemoryStore extends JDBCMemoryStore {
    public PostgreSQLMemoryStore(SQLConnector connector) {
        super(connector);
    }
    public Mono<Void> connectAsync() {
        return super.connectAsync();
    }

    /**
     * Builds an PostgreSQLMemoryStore.
     */
    public static class Builder implements SQLMemoryStoreBuilder {
        private Connection connection;

        /**
         * Builds and returns a PostgreSQLMemoryStore instance with the specified database connection.
         *
         * @return A PostgreSQLMemoryStore instance configured with the provided PostgreSQL database connection.
         */
        @Override
        public MemoryStore build() {
            return new PostgreSQLMemoryStore(new PostgreSQLConnector(connection));
        }

        /**
         * Sets the PostgreSQL database connection to be used by the PostgreSQL memory store being built.
         *
         * @param connection The Connection object representing the PostgreSQL database connection.
         * @return The updated Builder instance to continue the building process for a PostgreSQLMemoryStore.
         */
        @Override
        public Builder withConnection(Connection connection) {
            this.connection = connection;
            return this;
        }
    }
}
