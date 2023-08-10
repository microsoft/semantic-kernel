// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.memory;

import com.microsoft.semantickernel.ai.embeddings.EmbeddingGeneration;
import java.util.List;
import javax.annotation.CheckReturnValue;
import javax.annotation.Nullable;
import reactor.core.publisher.Mono;

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
            String collection,
            String text,
            String externalId,
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
            String collection,
            String text,
            String externalId,
            String externalSourceName,
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
    public Mono<MemoryQueryResult> getAsync(String collection, String key, boolean withEmbedding);

    /**
     * Remove a memory by key. For local memories the key is the "id" used when saving the record.
     * For external reference, the key is the "URI" used when saving the record.
     *
     * @param collection Collection to search.
     * @param key Unique memory record identifier.
     * @return Mono completion.
     */
    public Mono<Void> removeAsync(String collection, String key);

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
            String collection,
            String query,
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
        Builder setStorage(MemoryStore storage);

        Builder setEmbeddingGenerator(EmbeddingGeneration<String> embeddingGenerator);

        SemanticTextMemory build();
    }
}
