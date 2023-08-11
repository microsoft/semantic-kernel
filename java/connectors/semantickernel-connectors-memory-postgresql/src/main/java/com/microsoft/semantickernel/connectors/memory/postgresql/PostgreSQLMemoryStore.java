// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.postgresql;

import com.microsoft.semantickernel.connectors.memory.jdbc.JDBCMemoryStore;
import com.microsoft.semantickernel.memory.MemoryStore;
import reactor.core.publisher.Mono;

import javax.annotation.Nonnull;
import java.sql.SQLException;

public class PostgreSQLMemoryStore extends JDBCMemoryStore {

    public PostgreSQLMemoryStore() {
        this.dbConnector = new PostgreSQLConnector();
    }

    public Mono<Void> connectAsync(@Nonnull String url) throws SQLException {
        return super.connectAsync(url);
    }

    public static class Builder implements MemoryStore.Builder {
        @Override
        public MemoryStore build() {
            return new PostgreSQLMemoryStore();
        }
    }
}
