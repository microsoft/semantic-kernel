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
    private readonly ITextEmbeddingGeneration _embeddingGenerator;
    private readonly IMemoryStore _storage;
    private HashSet<string>? _collections;

    public SemanticTextMemory(
        IMemoryStore storage,
        ITextEmbeddingGeneration embeddingGenerator)
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
        CancellationToken cancellationToken = default)
    {
        var embedding = await this._embeddingGenerator.GenerateEmbeddingAsync(text, cancellationToken).ConfigureAwait(false);
        MemoryRecord data = MemoryRecord.LocalRecord(
            id: id, text: text, description: description, additionalMetadata: additionalMetadata, embedding: embedding);

        if (!(await this.DoesCollectionExistAsync(collection, cancellationToken).ConfigureAwait(false)))
        {
            await this._storage.CreateCollectionAsync(collection, cancellationToken).ConfigureAwait(false);
        }

        return await this._storage.UpsertAsync(collection, data, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task<string> SaveReferenceAsync(
        string collection,
        string text,
        string externalId,
        string externalSourceName,
        string? description = null,
        string? additionalMetadata = null,
        CancellationToken cancellationToken = default)
    {
        var embedding = await this._embeddingGenerator.GenerateEmbeddingAsync(text, cancellationToken).ConfigureAwait(false);
        var data = MemoryRecord.ReferenceRecord(externalId: externalId, sourceName: externalSourceName, description: description,
            additionalMetadata: additionalMetadata, embedding: embedding);

        if (!(await this.DoesCollectionExistAsync(collection, cancellationToken).ConfigureAwait(false)))
        {
            await this._storage.CreateCollectionAsync(collection, cancellationToken).ConfigureAwait(false);
        }

        return await this._storage.UpsertAsync(collection, data, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task<MemoryQueryResult?> GetAsync(
        string collection,
        string key,
        bool withEmbedding = false,
        CancellationToken cancellationToken = default)
    {
        MemoryRecord? record = await this._storage.GetAsync(collection, key, withEmbedding, cancellationToken).ConfigureAwait(false);

        if (record == null) { return null; }

        return MemoryQueryResult.FromMemoryRecord(record, 1);
    }

    /// <inheritdoc/>
    public async Task RemoveAsync(
        string collection,
        string key,
        CancellationToken cancellationToken = default)
    {
        // $$$ 
        await this._storage.RemoveAsync(collection, key, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<MemoryQueryResult> SearchAsync(
        string collection,
        string query,
        int limit = 1,
        double minRelevanceScore = 0.0,
        bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        // Do not proceed with embedding or query if index isn't present
        if (!(await this.DoesCollectionExistAsync(collection, cancellationToken).ConfigureAwait(false)))
        {
            yield break;
        }

        ReadOnlyMemory<float> queryEmbedding = await this._embeddingGenerator.GenerateEmbeddingAsync(query, cancellationToken).ConfigureAwait(false);

        IAsyncEnumerable<(MemoryRecord, double)> results = this._storage.GetNearestMatchesAsync(
            collectionName: collection,
            embedding: queryEmbedding,
            limit: limit,
            minRelevanceScore: minRelevanceScore,
            withEmbeddings: withEmbeddings,
            cancellationToken: cancellationToken);

        await foreach ((MemoryRecord, double) result in results.WithCancellation(cancellationToken))
        {
            yield return MemoryQueryResult.FromMemoryRecord(result.Item1, result.Item2);
        }
    }

    /// <inheritdoc/>
    public async Task<IList<string>> GetCollectionsAsync(CancellationToken cancellationToken = default)
    {
        IList<string> collections = await this._storage.GetCollectionsAsync(cancellationToken).ToListAsync(cancellationToken).ConfigureAwait(false);

        this._collections = new HashSet<string>(collections); // Capture collections

        return collections;
    }

    public void Dispose()
    {
        // ReSharper disable once SuspiciousTypeConversion.Global
        if (this._embeddingGenerator is IDisposable emb) { emb.Dispose(); }

        // ReSharper disable once SuspiciousTypeConversion.Global
        if (this._storage is IDisposable storage) { storage.Dispose(); }
    }

    private async Task<bool> DoesCollectionExistAsync(string collection, CancellationToken cancellationToken = default)
    {
        // Search cached list of collections to avoid a round trip to storage.
        if (this._collections == null || !this._collections.Contains(collection))
        {
            // Retrieve current list of collections
            await this.GetCollectionsAsync(cancellationToken).ConfigureAwait(false);
        }

        return this._collections?.Contains(collection) ?? false;
    }
}
