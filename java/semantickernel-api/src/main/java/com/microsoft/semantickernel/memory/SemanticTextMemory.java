// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.memory;

import com.microsoft.semantickernel.ai.embeddings.EmbeddingGeneration;

import reactor.core.publisher.Mono;

import java.util.List;

import javax.annotation.CheckReturnValue;
import javax.annotation.Nonnull;
import javax.annotation.Nullable;

/** An interface for semantic memory that creates and recalls memories associated with text. */
public interface SemanticTextMemory {

    @CheckReturnValue
    SemanticTextMemory copy();

    /**
     * Save some information into the semantic memory, keeping a copy of the source information.
     *
     * @param collection Collection where to save the information.
     * @param text Information to save.
     * @param externalId Unique identifier, e.g. URL or GUID to the original source.
     * @param description Optional description.
     * @param additionalMetadata Optional string for saving custom metadata.
     * @return Unique identifier of the saved memory record.
     */
    public Mono<String> saveInformationAsync(
            @Nonnull String collection,
            @Nonnull String text,
            @Nonnull String externalId,
            @Nullable String description,
            @Nullable String additionalMetadata);

    /**
     * Save some information into the semantic memory, keeping only a reference to the source
     * information.
     *
     * @param collection Collection where to save the information.
     * @param text Information to save.
     * @param externalId Unique identifier, e.g. URL or GUID to the original source.
     * @param externalSourceName Name of the external service, e.g. "MSTeams", "GitHub", "WebSite",
     *     "Outlook IMAP", etc.
     * @param description Optional description.
     * @param additionalMetadata Optional string for saving custom metadata.
     * @return Unique identifier of the saved memory record.
     */
    public Mono<String> saveReferenceAsync(
            @Nonnull String collection,
            @Nonnull String text,
            @Nonnull String externalId,
            @Nonnull String externalSourceName,
            @Nullable String description,
            @Nullable String additionalMetadata);

    /**
     * Fetch a memory by key. For local memories the key is the "id" used when saving the record.
     * For external reference, the key is the "URI" used when saving the record.
     *
     * @param collection Collection to search.
     * @param key Unique memory record identifier.
     * @param withEmbedding Whether to return the embedding of the memory found.
     * @return Memory record, or null when nothing is found
     */
    public Mono<MemoryQueryResult> getAsync(
            @Nonnull String collection, @Nonnull String key, boolean withEmbedding);

    @Deprecated
    /**
     * @deprecated No longer appears in the C# ISemanticTextMemory interface.
     */
    SemanticTextMemory merge(MemoryQueryResult b);

    /**
     * Remove a memory by key. For local memories the key is the "id" used when saving the record.
     * For external reference, the key is the "URI" used when saving the record.
     *
     * @param collection Collection to search.
     * @param key Unique memory record identifier.
     * @return Mono completion.
     */
    public Mono<Void> removeAsync(@Nonnull String collection, @Nonnull String key);

    /**
     * Find some information in memory
     *
     * @param collection Collection to search
     * @param query What to search for
     * @param limit How many results to return
     * @param minRelevanceScore Minimum relevance score, from 0 to 1, where 1 means exact match.
     * @param withEmbeddings Whether to return the embeddings of the memories found.
     * @return Memories found
     */
    public Mono<List<MemoryQueryResult>> searchAsync(
            @Nonnull String collection,
            @Nonnull String query,
            int limit,
            double minRelevanceScore,
            boolean withEmbeddings);

    /**
     * Gets a group of all available collection names.
     *
     * @return A group of collection names.
     */
    public Mono<List<String>> getCollectionsAsync();

    interface Builder {
        Builder setStorage(@Nonnull MemoryStore storage);

        Builder setEmbeddingGenerator(
                @Nonnull EmbeddingGeneration<String, ? extends Number> embeddingGenerator);

        SemanticTextMemory build();
    }
}
