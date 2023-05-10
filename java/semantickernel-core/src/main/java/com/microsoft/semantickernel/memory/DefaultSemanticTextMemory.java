// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.memory;

import com.microsoft.semantickernel.ai.embeddings.EmbeddingGeneration;
import com.microsoft.semantickernel.exceptions.NotSupportedException;

import reactor.core.publisher.Mono;

import java.util.List;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

/// <summary>
/// Implementation of <see cref="ISemanticTextMemory"/>./>.
/// </summary>
public class DefaultSemanticTextMemory implements SemanticTextMemory {

    @Nonnull private final EmbeddingGeneration<String, Float> _embeddingGenerator;
    @Nonnull private /*final*/ MemoryStore _storage;

    public DefaultSemanticTextMemory(
            @Nonnull MemoryStore storage,
            @Nonnull EmbeddingGeneration<String, Float> embeddingGenerator) {
        this._embeddingGenerator = embeddingGenerator;
        // TODO: this assignment raises EI_EXPOSE_REP2 in spotbugs (filtered out for now)
        this._storage = storage;
    }

    @Override
    public SemanticTextMemory copy() {
        // TODO: this is a shallow copy. Should it be a deep copy?
        return new DefaultSemanticTextMemory(this._storage, this._embeddingGenerator);
    }

    @Override
    public Mono<String> saveInformationAsync(
            @Nonnull String collection,
            @Nonnull String text,
            @Nonnull String id,
            @Nullable String description,
            @Nullable String additionalMetadata) {
        return Mono.error(new NotSupportedException("Pending implementation"));
        //        var embedding = await this._embeddingGenerator.GenerateEmbeddingAsync(text,
        // cancellationToken: cancel);
        //        MemoryRecord data = MemoryRecord.LocalRecord(
        //                id: id, text: text, description: description, additionalMetadata:
        // additionalMetadata, embedding: embedding);
        //
        //        if (!(await this._storage.DoesCollectionExistAsync(collection, cancel)))
        //        {
        //            await this._storage.CreateCollectionAsync(collection, cancel);
        //        }
        //
        //        return await this._storage.UpsertAsync(collection, record: data, cancel: cancel);
    }

    @Override
    public Mono<MemoryQueryResult> getAsync(String collection, String key, boolean withEmbedding) {
        return Mono.error(new NotSupportedException("Pending implementation"));
        //        MemoryRecord? record = await this._storage.GetAsync(collection, key,
        // withEmbedding, cancel);
        //
        //        if (record == null) { return null; }
        //
        //        return MemoryQueryResult.FromMemoryRecord(record, 1);
    }

    @Override
    public Mono<Void> removeAsync(@Nonnull String collection, @Nonnull String key) {
        return Mono.error(new NotSupportedException("Pending implementation"));
        //        await this._storage.RemoveAsync(collection, key, cancel);
    }

    @Override
    public Mono<List<MemoryQueryResult>> searchAsync(
            @Nonnull String collection,
            @Nonnull String query,
            int limit,
            double minRelevanceScore,
            boolean withEmbeddings) {
        return Mono.error(new NotSupportedException("Pending implementation"));
        //        Embedding<float> queryEmbedding = await
        // this._embeddingGenerator.GenerateEmbeddingAsync(query, cancellationToken: cancel);
        //
        //        IAsyncEnumerable<(MemoryRecord, double)> results =
        // this._storage.GetNearestMatchesAsync(
        //                collectionName: collection,
        //                embedding: queryEmbedding,
        //                limit: limit,
        //                minRelevanceScore: minRelevanceScore,
        //                withEmbeddings: withEmbeddings,
        //                cancel: cancel);
        //
        //        await foreach ((MemoryRecord, double) result in results.WithCancellation(cancel))
        //        {
        //            yield return MemoryQueryResult.FromMemoryRecord(result.Item1, result.Item2);
        //        }

    }

    @Override
    public Mono<List<String>> getCollectionsAsync() {
        return Mono.error(new NotSupportedException("Pending implementation"));
    }

    @Override
    public Mono<String> saveReferenceAsync(
            @Nonnull String collection,
            @Nonnull String text,
            @Nonnull String externalId,
            @Nonnull String externalSourceName,
            @Nullable String description,
            @Nullable String additionalMetadata) {

        return Mono.error(new NotSupportedException("Pending implementation"));
        //        var embedding = await this._embeddingGenerator.GenerateEmbeddingAsync(text,
        // cancellationToken: cancel);
        //        var data = MemoryRecord.ReferenceRecord(externalId: externalId, sourceName:
        // externalSourceName, description: description,
        //            additionalMetadata: additionalMetadata, embedding: embedding);
        //
        //        if (!(await this._storage.DoesCollectionExistAsync(collection, cancel)))
        //        {
        //            await this._storage.CreateCollectionAsync(collection, cancel);
        //        }
        //
        //        return await this._storage.UpsertAsync(collection, record: data, cancel: cancel);
    }

    @Override
    public SemanticTextMemory merge(MemoryQueryResult b) {
        throw new NotSupportedException("Pending implementation");
    }
}
