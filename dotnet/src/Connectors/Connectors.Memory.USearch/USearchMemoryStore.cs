// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Cloud.Unum.USearch;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Memory.USearch;

/// <summary>
/// An implementation of <see cref="IMemoryStore"/> for USearch.
/// </summary>
/// <remarks>The data for each collection is saved in separate USearch in-memory storage.
/// This implementations uses collection-level locks to avoid race conditions.
/// </remarks>
public class USearchMemoryStore : IMemoryStore, IDisposable
{
    /// <summary>
    /// Create in-memory collection of USearch storages
    /// </summary>
    /// <param name="metricKind">Metric for measuring vector distances, examples: MetricKind.Ip, MetricKind.Cos</param>
    /// <param name="dimensions">Embedding vector size</param>
    /// <param name="connectivity">Connectivity parameter. Defaults to 0</param>
    /// <param name="expansionAdd">Expansion add parameter. Defaults to 0</param>
    /// <param name="expansionSearch">Expansion search parameter. Defaults to 0</param>
    public USearchMemoryStore(
        MetricKind metricKind,
        ulong dimensions,
        ulong connectivity = 0uL,
        ulong expansionAdd = 0uL,
        ulong expansionSearch = 0uL)
    {
        this._usearchIndexOptions = new IndexOptions(
            metricKind: metricKind,
            dimensions: dimensions,
            quantization: ScalarKind.Float32,
            connectivity: connectivity,
            expansionAdd: expansionAdd,
            expansionSearch: expansionSearch,
            multi: false
        );
    }

    // TODO: implement constructor for persistence usage
    // public USearchMemoryStore(string Path) {}

    /// <inheritdoc/>
    public Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        lock (this._collectionLockerStore.GetLockFor(collectionName))
        {
            this._store.TryAdd(collectionName, new USearchCollectionStore(this._usearchIndexOptions));
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
        lock (this._collectionLockerStore.GetLockFor(collectionName))
        {
            if (!this._store.TryRemove(collectionName, out var usearchCollection))
            {
                return Task.FromException(new SKException($"Could not delete collection {collectionName}"));
            }
            usearchCollection.Dispose();
            this._collectionLockerStore.RemoveLockFor(collectionName);
        }

        return Task.CompletedTask;
    }

    /// <inheritdoc/>
    public Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken = default)
    {
        lock (this._collectionLockerStore.GetLockFor(collectionName))
        {
            if (!this.TryGetCollection(collectionName, out var usearchCollection, create: false))
            {
                return Task.FromException<string>(new SKException($"Attempted to access a memory collection that does not exist: {collectionName}"));
            }

            return Task.FromResult(usearchCollection.Upsert(record));
        }
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<string> UpsertBatchAsync(
        string collectionName,
        IEnumerable<MemoryRecord> records,
        CancellationToken cancellationToken = default)
    {
        lock (this._collectionLockerStore.GetLockFor(collectionName))
        {
            if (this.TryGetCollection(collectionName, out var usearchCollection, create: false))
            {
                return usearchCollection.UpsertBatch(records).ToAsyncEnumerable();
            }

            throw new SKException($"Attempted to access a memory collection that does not exist: {collectionName}");
        }
    }

    /// <inheritdoc/>
    public Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancellationToken = default)
    {
        lock (this._collectionLockerStore.GetLockFor(collectionName))
        {
            if (this.TryGetCollection(collectionName, out var usearchCollection)
            && usearchCollection.TryGetRecord(key, out var memoryRecord, withEmbedding))
            {
                return Task.FromResult<MemoryRecord?>(memoryRecord);
            }
        }

        return Task.FromResult<MemoryRecord?>(null);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys, bool withEmbeddings = false, [EnumeratorCancellation] CancellationToken cancellationToken = default)
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
        lock (this._collectionLockerStore.GetLockFor(collectionName))
        {
            if (this.TryGetCollection(collectionName, out var usearchCollection))
            {
                usearchCollection.Remove(key);
            }
        }
        return Task.CompletedTask;
    }

    /// <inheritdoc/>
    public Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        lock (this._collectionLockerStore.GetLockFor(collectionName))
        {
            if (this.TryGetCollection(collectionName, out var usearchCollection))
            {
                foreach (var key in keys)
                {
                    usearchCollection.Remove(key);
                }
            }
        }
        return Task.CompletedTask;
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(
        string collectionName,
        ReadOnlyMemory<float> embedding,
        int limit,
        double minRelevanceScore = 0,
        bool withEmbeddings = false,
        CancellationToken cancellationToken = default)
    {
        minRelevanceScore = minRelevanceScore > 0 ? (minRelevanceScore < 1 ? minRelevanceScore : 1) : 0;

        if (limit <= 0)
        {
            return AsyncEnumerable.Empty<(MemoryRecord, double)>();
        }

        lock (this._collectionLockerStore.GetLockFor(collectionName))
        {
            if (!this.TryGetCollection(collectionName, out var usearchCollection))
            {
                return AsyncEnumerable.Empty<(MemoryRecord, double)>();
            }
            return usearchCollection.GetNearestMatches(
                embedding,
                limit,
                minRelevanceScore,
                withEmbeddings
            ).ToAsyncEnumerable<(MemoryRecord, double)>();
        }
    }

    public async Task<(MemoryRecord, double)?> GetNearestMatchAsync(string collectionName, ReadOnlyMemory<float> embedding, double minRelevanceScore = 0, bool withEmbedding = false, CancellationToken cancellationToken = default)
    {
        return await this.GetNearestMatchesAsync(
                    collectionName: collectionName,
                    embedding: embedding,
                    limit: 1,
                    minRelevanceScore: minRelevanceScore,
                    withEmbeddings: withEmbedding,
                    cancellationToken: cancellationToken).FirstOrDefaultAsync(cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    #region protected ================================================================================

    protected virtual void Dispose(bool disposing)
    {
        if (!this._disposedValue)
        {
            foreach (KeyValuePair<string, IUSearchCollectionStore> entry in this._store)
            {
                lock (this._collectionLockerStore.GetLockFor(entry.Key))
                {
                    entry.Value.Dispose();
                }
            }
            this._disposedValue = true;
        }
    }

    protected bool TryGetCollection(
        string name,
        [NotNullWhen(true)] out IUSearchCollectionStore? collection,
        bool create = false)
    {
        if (this._store.TryGetValue(name, out collection))
        {
            return true;
        }

        if (create)
        {
            collection = new USearchCollectionStore(this._usearchIndexOptions);
            if (this._store.TryAdd(name, collection))
            {
                return true;
            }
            collection.Dispose();
            return false;
        }

        collection = null;
        return false;
    }

    #endregion

    #region private ================================================================================

    private readonly USearchConcurrentCollectionLockStore _collectionLockerStore = new();

    private readonly ConcurrentDictionary<string, IUSearchCollectionStore> _store = new();

    private readonly IndexOptions _usearchIndexOptions;

    private bool _disposedValue;

    #endregion
}
