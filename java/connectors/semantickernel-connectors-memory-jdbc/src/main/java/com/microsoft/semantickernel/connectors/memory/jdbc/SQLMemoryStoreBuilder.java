// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.jdbc;

import com.microsoft.semantickernel.memory.MemoryStore;
import java.sql.Connection;

/**
 * An interface representing a builder for constructing an SQL memory store in the context of a
 * MemoryStore.
 */
public interface SQLMemoryStoreBuilder extends MemoryStore.Builder {

    /**
     * Sets the database connection to be used by the SQL memory store.
     *
     * @param connection The Connection object representing the database connection.
     * @return The updated SQLMemoryStoreBuilder instance.
     */
    SQLMemoryStoreBuilder withConnection(Connection connection);
}
