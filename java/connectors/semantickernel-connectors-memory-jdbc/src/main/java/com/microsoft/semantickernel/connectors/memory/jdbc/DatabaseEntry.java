package com.microsoft.semantickernel.connectors.memory.jdbc;

import com.microsoft.semantickernel.memory.DataEntryBase;

import java.time.ZonedDateTime;

public class DatabaseEntry extends DataEntryBase {
    private final String metadata;
    private final String embedding;

    public DatabaseEntry(
            String key, String metadata, String embedding, ZonedDateTime timestamp) {
        super(key, timestamp);
        this.metadata = metadata;
        this.embedding = embedding;
    }

    public String getMetadata() {
        return metadata;
    }

    public String getEmbedding() {
        return embedding;
    }
}

