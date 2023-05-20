// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.memory;

import javax.annotation.Nonnull;

/** Class representing the metadata associated with a Semantic Kernel memory. */
public class MemoryRecordMetadata {

    @Nonnull private final boolean isReference;
    @Nonnull private final String externalSourceName;
    @Nonnull private final String id;
    @Nonnull private final String description;
    @Nonnull private final String text;
    @Nonnull private final String additionalMetadata;

    /**
     * Whether the source data used to calculate embeddings are stored in the local storage provider
     * or is available through and external service, such as web site, MS Graph, etc.
     */
    public boolean isReference() {
        return isReference;
    }

    /**
     * A value used to understand which external service owns the data, to avoid storing the
     * information inside the URI. E.g. this could be "MSTeams", "WebSite", "GitHub", etc.
     *
     * @return Name of the external service if isReference is true.
     */
    public String getExternalSourceName() {
        return externalSourceName;
    }

    /**
     * Unique identifier. The format of the value is domain specific, so it can be a URL, a GUID,
     * etc.
     *
     * @return Unique string used to identify the {@code MemoryRecord}.
     */
    public String getId() {
        return id;
    }

    /**
     * Optional title describing the content. Note: the title is not indexed.
     *
     * @return the optional title describing the content.
     */
    public String getDescription() {
        return description;
    }

    /**
     * Source text, available only when the memory is not an external source.
     *
     * @return Source text when the memory is not an external source.
     */
    public String getText() {
        return text;
    }

    /**
     * Custom metadata associated with a memory.
     *
     * @return Custom metadata associated with a memory.
     */
    public String getAdditionalMetadata() {
        return additionalMetadata;
    }

    /**
     * Constructor.
     *
     * @param isReference True if source data is local, false if source data comes from an external
     *     service.
     * @param id Unique string used to identify the {@code MemoryRecord}.
     * @param text Local source data associated with a {@code MemoryRecord} embedding.
     * @param description {@code MemoryRecord} description.
     * @param externalSourceName Name of the external source if isReference is true.
     * @param additionalMetadata Field for saving custom metadata with a memory.
     */
    public MemoryRecordMetadata(
            boolean isReference,
            @Nonnull String id,
            @Nonnull String text,
            @Nonnull String description,
            @Nonnull String externalSourceName,
            @Nonnull String additionalMetadata) {
        this.isReference = isReference;
        this.id = id;
        this.text = text;
        this.description = description;
        this.externalSourceName = externalSourceName;
        this.additionalMetadata = additionalMetadata;
    }
}
