// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// Implementation of <see cref="ISemanticTextMemory"/>./>.
/// </summary>
public sealed class SemanticTextMemory : ISemanticTextMemory, IDisposable
{
    private readonly IEmbeddingGeneration<string, float> _embeddingGenerator;
    private readonly IMemoryStore _storage;

    public SemanticTextMemory(
        IMemoryStore storage,
        IEmbeddingGeneration<string, float> embeddingGenerator)
    {
        this._embeddingGenerator = embeddingGenerator;
        this._storage = storage;
    }

    /// <inheritdoc/>
    public async Task<string> SaveInformationAsync(
        string collection,
        string text,
        string id,
        string? description = null,
        string? additionalMetadata = null,
        CancellationToken cancel = default)
    {
        var embedding = await this._embeddingGenerator.GenerateEmbeddingAsync(text, cancellationToken: cancel);
        MemoryRecord data = MemoryRecord.LocalRecord(
            id: id, text: text, description: description, additionalMetadata: additionalMetadata, embedding: embedding);

        if (!(await this._storage.DoesCollectionExistAsync(collection, cancel)))
        {
            await this._storage.CreateCollectionAsync(collection, cancel);
        }

        return await this._storage.UpsertAsync(collection, record: data, cancel: cancel);
    }

    /// <inheritdoc/>
    public async Task<string> SaveReferenceAsync(
        string collection,
        string text,
        string externalId,
        string externalSourceName,
        string? description = null,
        string? additionalMetadata = null,
        CancellationToken cancel = default)
    {
        var embedding = await this._embeddingGenerator.GenerateEmbeddingAsync(text, cancellationToken: cancel);
        var data = MemoryRecord.ReferenceRecord(externalId: externalId, sourceName: externalSourceName, description: description,
            additionalMetadata: additionalMetadata, embedding: embedding);

        if (!(await this._storage.DoesCollectionExistAsync(collection, cancel)))
        {
            await this._storage.CreateCollectionAsync(collection, cancel);
        }

        return await this._storage.UpsertAsync(collection, record: data, cancel: cancel);
    }

    /// <inheritdoc/>
    public async Task<MemoryQueryResult?> GetAsync(
        string collection,
        string key,
        bool withEmbedding = false,
        CancellationToken cancel = default)
    {
        MemoryRecord? record = await this._storage.GetAsync(collection, key, withEmbedding, cancel);

        if (record == null) { return null; }

        return MemoryQueryResult.FromMemoryRecord(record, 1);
    }

    /// <inheritdoc/>
    public async Task RemoveAsync(
        string collection,
        string key,
        CancellationToken cancel = default)
    {
        await this._storage.RemoveAsync(collection, key, cancel);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<MemoryQueryResult> SearchAsync(
        string collection,
        string query,
        int limit = 1,
        double minRelevanceScore = 0.7,
        bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        Embedding<float> queryEmbedding = await this._embeddingGenerator.GenerateEmbeddingAsync(query, cancellationToken: cancel);

        IAsyncEnumerable<(MemoryRecord, double)> results = this._storage.GetNearestMatchesAsync(
            collectionName: collection,
            embedding: queryEmbedding,
            limit: limit,
            minRelevanceScore: minRelevanceScore,
            withEmbeddings: withEmbeddings,
            cancel: cancel);

        await foreach ((MemoryRecord, double) result in results.WithCancellation(cancel))
        {
            yield return MemoryQueryResult.FromMemoryRecord(result.Item1, result.Item2);
        }
    }

    /// <inheritdoc/>
    public async Task<IList<string>> GetCollectionsAsync(CancellationToken cancel = default)
    {
        return await this._storage.GetCollectionsAsync(cancel).ToListAsync(cancel);
    }

    public void Dispose()
    {
        // ReSharper disable once SuspiciousTypeConversion.Global
        if (this._embeddingGenerator is IDisposable emb) { emb.Dispose(); }

        // ReSharper disable once SuspiciousTypeConversion.Global
        if (this._storage is IDisposable storage) { storage.Dispose(); }
    }
}
