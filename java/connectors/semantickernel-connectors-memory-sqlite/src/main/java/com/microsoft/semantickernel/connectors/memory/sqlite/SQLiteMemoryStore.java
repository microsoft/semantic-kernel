// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.sqlite;

import com.microsoft.semantickernel.connectors.memory.jdbc.JDBCConnector;
import com.microsoft.semantickernel.connectors.memory.jdbc.JDBCMemoryStore;
import com.microsoft.semantickernel.connectors.memory.jdbc.SQLConnector;
import com.microsoft.semantickernel.connectors.memory.jdbc.SQLMemoryStoreBuilder;
import com.microsoft.semantickernel.memory.MemoryStore;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import reactor.core.publisher.Mono;

public class SQLiteMemoryStore extends JDBCMemoryStore {
    public SQLiteMemoryStore(SQLConnector connector) {
        super(connector);
    }

    public Mono<Void> connectAsync() {
        return super.connectAsync();
    }

    /** Builds an SQLiteMemoryStore. */
    public static class Builder implements SQLMemoryStoreBuilder {
        private Connection connection;

        /**
         * Builds and returns an SQLiteMemoryStore instance with the specified database connection.
         *
         * @return An SQLiteMemoryStore instance configured with the provided SQLite database
         *     connection.
         */
        @Override
        public MemoryStore build() {
            return new SQLiteMemoryStore(new JDBCConnector(connection));
        }

        /**
         * Sets the SQLite database connection to be used by the SQLite memory store being built.
         *
         * @param connection The Connection object representing the SQLite database connection.
         * @return The updated Builder instance to continue the building process for an
         *     SQLiteMemoryStore.
         */
        @Override
        public Builder withConnection(Connection connection) {
            this.connection = connection;
            return this;
        }

        /**
         * Creates and sets an SQLite database connection using the specified filename.
         *
         * @param filename The filename of the SQLite database.
         * @return The updated Builder instance with the SQLite database connection set.
         * @throws SQLException If there is an issue with establishing the database connection.
         */
        public Builder withFilename(String filename) throws SQLException {
            return withConnection(DriverManager.getConnection("jdbc:sqlite:" + filename));
        }
    }
}
