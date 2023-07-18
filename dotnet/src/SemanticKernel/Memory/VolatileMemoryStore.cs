// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.Embeddings.VectorOperations;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Memory.Collections;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// A simple volatile memory embeddings store.
/// </summary>
public class VolatileMemoryStore : IMemoryStore
{
    /// <inheritdoc/>
    public Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        if (!this._store.TryAdd(collectionName, new ConcurrentDictionary<string, MemoryRecord>()))
        {
            return Task.FromException(new SKException($"Could not create collection {collectionName}"));
        }

        return Task.CompletedTask;
    }

    /// <inheritdoc/>
    public Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        return Task.FromResult(this._store.ContainsKey(collectionName));
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<string> GetCollectionsAsync(CancellationToken cancellationToken = default)
    {
        return this._store.Keys.ToAsyncEnumerable();
    }

    /// <inheritdoc/>
    public Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        if (!this._store.TryRemove(collectionName, out _))
        {
            return Task.FromException(new SKException($"Could not delete collection {collectionName}"));
        }

        return Task.CompletedTask;
    }

    /// <inheritdoc/>
    public Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);
        Verify.NotNull(record.Metadata.Id);

        if (this.TryGetCollection(collectionName, out var collectionDict, create: false))
        {
            record.Key = record.Metadata.Id;
            collectionDict[record.Key] = record;
        }
        else
        {
            return Task.FromException<string>(new SKException($"Attempted to access a memory collection that does not exist: {collectionName}"));
        }

        return Task.FromResult(record.Key);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> UpsertBatchAsync(
        string collectionName,
        IEnumerable<MemoryRecord> records,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        foreach (var r in records)
        {
            yield return await this.UpsertAsync(collectionName, r, cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    public Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancellationToken = default)
    {
        if (this.TryGetCollection(collectionName, out var collectionDict)
            && collectionDict.TryGetValue(key, out var dataEntry))
        {
            return Task.FromResult<MemoryRecord?>(withEmbedding
                ? dataEntry
                : MemoryRecord.FromMetadata(dataEntry.Metadata, embedding: null, key: dataEntry.Key, timestamp: dataEntry.Timestamp));
        }

        return Task.FromResult<MemoryRecord?>(null);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<MemoryRecord> GetBatchAsync(
        string collectionName,
        IEnumerable<string> keys,
        bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        foreach (var key in keys)
        {
            var record = await this.GetAsync(collectionName, key, withEmbeddings, cancellationToken).ConfigureAwait(false);

            if (record != null)
            {
                yield return record;
            }
        }
    }

    /// <inheritdoc/>
    public Task RemoveAsync(string collectionName, string key, CancellationToken cancellationToken = default)
    {
        if (this.TryGetCollection(collectionName, out var collectionDict))
        {
            collectionDict.TryRemove(key, out MemoryRecord _);
        }

        return Task.CompletedTask;
    }

    /// <inheritdoc/>
    public Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        return Task.WhenAll(keys.Select(k => this.RemoveAsync(collectionName, k, cancellationToken)));
    }

    public IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(
        string collectionName,
        Embedding<float> embedding,
        int limit,
        double minRelevanceScore = 0.0,
        bool withEmbeddings = false,
        CancellationToken cancellationToken = default)
    {
        if (limit <= 0)
        {
            return AsyncEnumerable.Empty<(MemoryRecord, double)>();
        }

        ICollection<MemoryRecord>? embeddingCollection = null;
        if (this.TryGetCollection(collectionName, out var collectionDict))
        {
            embeddingCollection = collectionDict.Values;
        }

        if (embeddingCollection == null || embeddingCollection.Count == 0)
        {
            return AsyncEnumerable.Empty<(MemoryRecord, double)>();
        }

        TopNCollection<MemoryRecord> embeddings = new(limit);

        foreach (var record in embeddingCollection)
        {
            if (record != null)
            {
                double similarity = embedding
                    .AsReadOnlySpan()
                    .CosineSimilarity(record.Embedding.AsReadOnlySpan());
                if (similarity >= minRelevanceScore)
                {
                    var entry = withEmbeddings ? record : MemoryRecord.FromMetadata(record.Metadata, Embedding<float>.Empty, record.Key, record.Timestamp);
                    embeddings.Add(new(entry, similarity));
                }
            }
        }

        embeddings.SortByScore();

        return embeddings.Select(x => (x.Value, x.Score.Value)).ToAsyncEnumerable();
    }

    /// <inheritdoc/>
    public async Task<(MemoryRecord, double)?> GetNearestMatchAsync(
        string collectionName,
        Embedding<float> embedding,
        double minRelevanceScore = 0.0,
        bool withEmbedding = false,
        CancellationToken cancellationToken = default)
    {
        return await this.GetNearestMatchesAsync(
            collectionName: collectionName,
            embedding: embedding,
            limit: 1,
            minRelevanceScore: minRelevanceScore,
            withEmbeddings: withEmbedding,
            cancellationToken: cancellationToken).FirstOrDefaultAsync(cancellationToken).ConfigureAwait(false);
    }

    #region protected ================================================================================

    protected bool TryGetCollection(
        string name,
        [NotNullWhen(true)] out ConcurrentDictionary<string,
            MemoryRecord>? collection,
        bool create = false)
    {
        if (this._store.TryGetValue(name, out collection))
        {
            return true;
        }

        if (create)
        {
            collection = new ConcurrentDictionary<string, MemoryRecord>();
            return this._store.TryAdd(name, collection);
        }

        collection = null;
        return false;
    }

    #endregion

    #region private ================================================================================

    private readonly ConcurrentDictionary<string,
        ConcurrentDictionary<string, MemoryRecord>> _store = new();

    #endregion
}
