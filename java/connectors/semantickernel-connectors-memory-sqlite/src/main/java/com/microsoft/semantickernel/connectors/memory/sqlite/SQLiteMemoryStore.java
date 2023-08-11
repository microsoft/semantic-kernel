// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.sqlite;

import com.microsoft.semantickernel.connectors.memory.jdbc.JDBCMemoryStore;
import com.microsoft.semantickernel.memory.MemoryStore;
import java.sql.SQLException;
import javax.annotation.Nonnull;
import reactor.core.publisher.Mono;

public class SQLiteMemoryStore extends JDBCMemoryStore {

    public SQLiteMemoryStore() {
        super();
    }

    public Mono<Void> connectAsync(@Nonnull String filename) throws SQLException {
        return super.connectAsync("jdbc:sqlite:" + filename);
    }

    public static class Builder implements MemoryStore.Builder {
        @Override
        public MemoryStore build() {
            return new SQLiteMemoryStore();
        }
    }
}
