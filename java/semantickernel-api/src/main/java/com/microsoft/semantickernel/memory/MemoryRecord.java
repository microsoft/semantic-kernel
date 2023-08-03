// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.memory;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.microsoft.semantickernel.ai.embeddings.Embedding;
import java.time.ZonedDateTime;
import javax.annotation.Nonnull;
import javax.annotation.Nullable;

/**
 * A record in a Semantic Kernel memory. IMPORTANT: this is a storage schema. Changing the fields
 * will invalidate existing metadata stored in persistent vector DBs.
 */
public class MemoryRecord extends DataEntryBase {
    @Nonnull private final Embedding embedding;

    @Nonnull private final MemoryRecordMetadata metadata;

    /**
     * Creates an instance of a {@code MemoryRecord}.
     *
     * @param metadata The metadata associated with a Semantic Kernel memory.
     * @param embedding The source content embeddings.
     * @param key The key of the data.
     * @param timestamp The timestamp of the data.
     */
    @JsonCreator
    public MemoryRecord(
            @JsonProperty("additional_metadata") @Nonnull MemoryRecordMetadata metadata,
            @JsonProperty("embedding") @Nonnull Embedding embedding,
            @JsonProperty("key") @Nullable String key,
            @JsonProperty("timestamp") @Nullable ZonedDateTime timestamp) {
        super(key, timestamp);
        this.metadata = metadata;
        this.embedding = embedding;
    }

    /**
     * Gets the source content embeddings.
     *
     * @return The source content embeddings.
     */
    public Embedding getEmbedding() {
        return embedding;
    }

    /**
     * Gets the metadata associated with a Semantic Kernel memory.
     *
     * @return The metadata associated with a Semantic Kernel memory.
     */
    public MemoryRecordMetadata getMetadata() {
        return metadata;
    }

    /**
     * Prepare an instance about a memory which source is stored externally. The universal resource
     * identifies points to the URL (or equivalent) to find the original source.
     *
     * @param externalId URL (or equivalent) to find the original source.
     * @param sourceName Name of the external service, e.g. "MSTeams", "GitHub", "WebSite", "Outlook
     *     IMAP", etc.
     * @param description Optional description of the record. Note: the description is not indexed.
     * @param embedding Source content embedding.
     * @param additionalMetadata Optional string for saving custom metadata.
     * @param key Optional existing database key.
     * @param timestamp optional timestamp.
     * @return Memory record
     */
    public static MemoryRecord referenceRecord(
            @Nonnull String externalId,
            @Nonnull String sourceName,
            @Nullable String description,
            @Nonnull Embedding embedding,
            @Nullable String additionalMetadata,
            @Nullable String key,
            @Nullable ZonedDateTime timestamp) {

        MemoryRecordMetadata metadata =
                new MemoryRecordMetadata(
                        true,
                        externalId,
                        "",
                        description != null ? description : "",
                        sourceName,
                        additionalMetadata != null ? additionalMetadata : "");
        return new MemoryRecord(metadata, embedding, key, timestamp);
    }

    /**
     * Prepare an instance for a memory stored in the internal storage provider.
     *
     * @param id Resource identifier within the storage provider, e.g. record ID/GUID/incremental
     *     counter etc.
     * @param text Full text used to generate the embeddings.
     * @param description Optional description of the record. Note: the description is not indexed.
     * @param embedding Source content embedding.
     * @param additionalMetadata Optional string for saving custom metadata.
     * @param key Optional existing database key.
     * @param timestamp optional timestamp.
     * @return Memory record
     */
    public static MemoryRecord localRecord(
            @Nonnull String id,
            @Nonnull String text,
            @Nullable String description,
            @Nonnull Embedding embedding,
            @Nullable String additionalMetadata,
            @Nullable String key,
            @Nullable ZonedDateTime timestamp) {

        boolean isReference = false;
        String emptyString = "";
        MemoryRecordMetadata metadata =
                new MemoryRecordMetadata(
                        isReference,
                        id,
                        text,
                        description != null ? description : emptyString,
                        emptyString,
                        additionalMetadata != null ? additionalMetadata : emptyString);
        return new MemoryRecord(metadata, embedding, key, timestamp);
    }

    /**
     * Create a memory record from a memory record's metadata.
     *
     * @param metadata Metadata associated with a memory.
     * @param embedding Optional embedding associated with a memory record.
     * @param key Optional existing database key.
     * @param timestamp optional timestamp.
     * @return Memory record
     */
    public static MemoryRecord fromMetadata(
            @Nonnull MemoryRecordMetadata metadata,
            @Nullable Embedding embedding,
            @Nullable String key,
            @Nullable ZonedDateTime timestamp) {
        return new MemoryRecord(
                metadata, embedding != null ? embedding : Embedding.empty(), key, timestamp);
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof MemoryRecord)) return false;

        MemoryRecord that = (MemoryRecord) o;

        if (!embedding.equals(that.embedding)) return false;
        return metadata.equals(that.metadata);
    }

    @Override
    public int hashCode() {
        int result = embedding.hashCode();
        result = 31 * result + metadata.hashCode();
        return result;
    }

    @Override
    public String toString() {
        return "MemoryRecord{" + "embedding=" + embedding + ", metadata=" + metadata + '}';
    }

    public String getSerializedMetadata() throws JsonProcessingException {
        return new ObjectMapper().writeValueAsString(this.metadata);
    }

    public String getSerializedEmbedding() throws JsonProcessingException {
        return new ObjectMapper().writeValueAsString(this.embedding);
    }

    public static MemoryRecord fromJsonMetadata(
            String json,
            @Nullable Embedding embedding,
            @Nullable String key,
            @Nullable ZonedDateTime timestamp)
            throws JsonProcessingException {
        MemoryRecordMetadata metadata =
                new ObjectMapper().readValue(json, MemoryRecordMetadata.class);

        if (metadata != null) {
            return new MemoryRecord(
                    metadata, embedding != null ? embedding : Embedding.empty(), key, timestamp);
        }

        throw new MemoryException(
                MemoryException.ErrorCodes.UNABLE_TO_DESERIALIZE_METADATA,
                "Unable to create memory record from serialized metadata");
    }
}
