// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.jdbc;

import com.microsoft.semantickernel.memory.DataEntryBase;
import java.time.ZonedDateTime;

/** Represents an entry in the Semantic Kernel Memory Table. */
public class DatabaseEntry extends DataEntryBase {
    private final String embedding; // JSON with the embedding information
    private final String metadata; // JSON with the metadata associated

    /**
     * Creates a new instance of DatabaseEntry.
     *
     * @param key The key identifying the entry.
     * @param metadata The metadata associated.
     * @param embedding The embedding information associated.
     * @param timestamp The timestamp indicating when the entry was created or modified.
     */
    public DatabaseEntry(String key, String metadata, String embedding, ZonedDateTime timestamp) {
        super(key, timestamp);
        this.metadata = metadata;
        this.embedding = embedding;
    }

    /**
     * Gets the metadata associated with the entry.
     *
     * @return The metadata associated with the entry.
     */
    public String getMetadata() {
        return metadata;
    }

    /**
     * Gets the embedding information associated with the entry.
     *
     * @return The embedding information associated with the entry.
     */
    public String getEmbedding() {
        return embedding;
    }
}
