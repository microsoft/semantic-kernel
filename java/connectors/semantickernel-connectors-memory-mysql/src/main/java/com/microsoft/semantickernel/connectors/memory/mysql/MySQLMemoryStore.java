// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.mysql;

import com.microsoft.semantickernel.connectors.memory.jdbc.JDBCMemoryStore;
import com.microsoft.semantickernel.connectors.memory.jdbc.SQLConnector;
import com.microsoft.semantickernel.connectors.memory.jdbc.SQLMemoryStore;
import java.sql.Connection;
import javax.annotation.CheckReturnValue;
import reactor.core.publisher.Mono;

public class MySQLMemoryStore extends JDBCMemoryStore {
    private MySQLMemoryStore(SQLConnector connector) {
        super(connector);
    }

    /** Builds a MySQLMemoryStore. */
    public static class Builder implements SQLMemoryStore.Builder<MySQLMemoryStore> {
        private Connection connection;

        /**
         * Builds and returns a MySQLMemoryStore instance with the specified database connection.
         * The build process will connect to the database and create the required tables.
         *
         * @return A MySQLMemoryStore instance configured with the provided database connection.
         * @deprecated Use {@link #buildAsync()} instead.
         */
        @Override
        @Deprecated
        public MySQLMemoryStore build() {
            return this.buildAsync().block();
        }

        /**
         * Asynchronously builds and returns a MySQLMemoryStore instance with the specified database
         * connection.
         *
         * @return A Mono with a MySQLMemoryStore instance configured with the provided database
         *     connection.
         */
        @Override
        @CheckReturnValue
        public Mono<MySQLMemoryStore> buildAsync() {
            MySQLConnector connector = new MySQLConnector(connection);
            MySQLMemoryStore memoryStore = new MySQLMemoryStore(connector);
            return connector.createTableAsync().thenReturn(memoryStore);
        }

        /**
         * Sets the MySQL database connection to be used by the MySQL memory store being built.
         *
         * @param connection The Connection object representing the MySQL database connection.
         * @return The updated Builder instance to continue the building process for a
         *     MySQLMemoryStore.
         */
        @Override
        public Builder withConnection(Connection connection) {
            this.connection = connection;
            return this;
        }
    }
}
