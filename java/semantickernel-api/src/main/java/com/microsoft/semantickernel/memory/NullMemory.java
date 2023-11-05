// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.memory;

import java.util.Collections;
import java.util.List;
import javax.annotation.CheckReturnValue;
import javax.annotation.Nonnull;
import javax.annotation.Nullable;
import reactor.core.publisher.Mono;

/** Implementation of {@link SemanticTextMemory} that stores nothing. */
public final class NullMemory implements SemanticTextMemory {

    private static final NullMemory DEFAULT = new NullMemory();

    /**
     * Gets the singleton instance of {@code }NullMemory}.
     *
     * @return The singleton instance of {@code NullMemory}.
     */
    public static NullMemory getInstance() {
        return DEFAULT;
    }

    private static final String EMPTY_STRING = "";

    @Override
    @CheckReturnValue
    public SemanticTextMemory copy() {
        return new NullMemory();
    }

    @Override
    public Mono<String> saveInformationAsync(
            @Nonnull String collection,
            @Nonnull String text,
            @Nonnull String externalId,
            @Nullable String description,
            @Nullable String additionalMetadata) {
        return Mono.just(EMPTY_STRING);
    }

    @Override
    public Mono<String> saveReferenceAsync(
            @Nonnull String collection,
            @Nonnull String text,
            @Nonnull String externalId,
            @Nonnull String externalSourceName,
            @Nullable String description,
            @Nullable String additionalMetadata) {
        return Mono.just(EMPTY_STRING);
    }

    @Override
    public Mono<MemoryQueryResult> getAsync(String collection, String key, boolean withEmbedding) {
        return Mono.empty();
    }

    @Override
    public Mono<Void> removeAsync(@Nonnull String collection, @Nonnull String key) {
        return Mono.empty();
    }

    @Override
    public Mono<List<MemoryQueryResult>> searchAsync(
            @Nonnull String collection,
            @Nonnull String query,
            int limit,
            float minRelevanceScore,
            boolean withEmbeddings) {
        return Mono.just(Collections.emptyList());
    }

    @Override
    public Mono<List<String>> getCollectionsAsync() {
        return Mono.just(Collections.emptyList());
    }

    /*

    /// <inheritdoc/>
    public Task<string> SaveInformationAsync(
        string collection,
        string text,
        string id,
        string? description = null,
        string? additionalMetadata = null,
        CancellationToken cancel = default)
    {
        return Task.FromResult(string.Empty);
    }

    /// <inheritdoc/>
    public Task<string> SaveReferenceAsync(
        string collection,
        string text,
        string externalId,
        string externalSourceName,
        string? description = null,
        string? additionalMetadata = null,
        CancellationToken cancel = default)
    {
        return Task.FromResult(string.Empty);
    }

    /// <inheritdoc/>
    public Task<MemoryQueryResult?> GetAsync(
        string collection,
        string key,
        bool withEmbedding = false,
        CancellationToken cancel = default)
    {
        return Task.FromResult(null as MemoryQueryResult);
    }

    /// <inheritdoc/>
    public Task RemoveAsync(
        string collection,
        string key,
        CancellationToken cancel = default)
    {
        return Task.CompletedTask;
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<MemoryQueryResult> SearchAsync(
        string collection,
        string query,
        int limit = 1,
        double minRelevanceScore = 0.7,
        bool withEmbeddings = false,
        CancellationToken cancel = default)
    {
        return AsyncEnumerable.Empty<MemoryQueryResult>();
    }

    /// <inheritdoc/>
    public Task<IList<string>> GetCollectionsAsync(
        CancellationToken cancel = default)
    {
        return Task.FromResult(new List<string>() as IList<string>);
    }

    private NullMemory()
    {
    }

     */
}
