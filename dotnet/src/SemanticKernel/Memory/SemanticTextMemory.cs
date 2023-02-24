// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory.Storage;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// Implementation of <see cref="ISemanticTextMemory"/>./>.
/// </summary>
public sealed class SemanticTextMemory : ISemanticTextMemory, IDisposable
{
    private readonly IEmbeddingGenerator<string, float> _embeddingGenerator;
    private readonly IMemoryStore<float> _storage;

    public SemanticTextMemory(
        IMemoryStore<float> storage,
        IEmbeddingGenerator<string, float> embeddingGenerator)
    {
        this._embeddingGenerator = embeddingGenerator;
        this._storage = storage;
    }

    /// <inheritdoc/>
    public async Task SaveInformationAsync(
        string collection,
        string text,
        string id,
        string? description = null,
        CancellationToken cancel = default)
    {
        var embeddings = await this._embeddingGenerator.GenerateEmbeddingAsync(text);
        MemoryRecord data = MemoryRecord.LocalRecord(id, text, description, embeddings);

        await this._storage.PutValueAsync(collection, key: id, value: data, cancel: cancel);
    }

    /// <inheritdoc/>
    public async Task SaveReferenceAsync(
        string collection,
        string text,
        string externalId,
        string externalSourceName,
        string? description = null,
        CancellationToken cancel = default)
    {
        var embedding = await this._embeddingGenerator.GenerateEmbeddingAsync(text);
        var data = MemoryRecord.ReferenceRecord(externalId: externalId, sourceName: externalSourceName, description, embedding);

        await this._storage.PutValueAsync(collection, key: externalId, value: data, cancel: cancel);
    }

    /// <inheritdoc/>
    public async Task<MemoryQueryResult?> GetAsync(
        string collection,
        string key,
        CancellationToken cancel = default)
    {
        DataEntry<IEmbeddingWithMetadata<float>>? record = await this._storage.GetAsync(collection, key, cancel);

        if (record == null || record.Value == null || record.Value.Value == null) { return null; }

        MemoryRecord result = (MemoryRecord)(record.Value.Value);

        return MemoryQueryResult.FromMemoryRecord(result, 1);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<MemoryQueryResult> SearchAsync(
        string collection,
        string query,
        int limit = 1,
        double minRelevanceScore = 0.7,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        Embedding<float> queryEmbedding = await this._embeddingGenerator.GenerateEmbeddingAsync(query);

        IAsyncEnumerable<(IEmbeddingWithMetadata<float>, double)> results = this._storage.GetNearestMatchesAsync(
            collection, queryEmbedding, limit: limit, minRelevanceScore: minRelevanceScore);

        await foreach ((IEmbeddingWithMetadata<float>, double) result in results.WithCancellation(cancel))
        {
            yield return MemoryQueryResult.FromMemoryRecord((MemoryRecord)result.Item1, result.Item2);
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
