// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.jdbc;

import com.microsoft.semantickernel.memory.MemoryStore;
import java.sql.Connection;
import reactor.core.publisher.Mono;

public interface SQLMemoryStore extends MemoryStore {
    interface Builder<T extends SQLMemoryStore> extends MemoryStore.Builder<T> {
        /**
         * Asynchronously builds the SQLMemoryStore.
         *
         * @return A Mono with the SQLMemoryStore.
         */
        Mono<T> buildAsync();

        /**
         * Sets the database connection to be used by the SQL memory store.
         *
         * @param connection The Connection object representing the database connection.
         * @return The updated SQLMemoryStoreBuilder instance.
         */
        Builder<T> withConnection(Connection connection);
    }
}
