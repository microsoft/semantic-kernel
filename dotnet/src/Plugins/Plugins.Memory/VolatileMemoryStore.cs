// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
>>>>>>> head
using System.Numerics.Tensors;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream

namespace Microsoft.SemanticKernel.Memory;
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main

namespace Microsoft.SemanticKernel.Memory;
=======
<<<<<<< div
=======
>>>>>>> main
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head

namespace Microsoft.SemanticKernel.Memory;
=======
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings.VectorOperations;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Memory.Collections;

namespace Microsoft.SemanticKernel.Plugins.Memory;
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head

/// <summary>
/// A simple volatile memory embeddings store.
/// </summary>
public class VolatileMemoryStore : IMemoryStore
{
    /// <inheritdoc/>
    public Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        this._store.TryAdd(collectionName, new ConcurrentDictionary<string, MemoryRecord>());
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
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            return Task.FromException(new KernelException($"Could not delete collection {collectionName}"));
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
            return Task.FromException(new KernelException($"Could not delete collection {collectionName}"));
=======
            return Task.FromException(new SKException($"Could not delete collection {collectionName}"));
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
            return Task.FromException(new KernelException($"Could not delete collection {collectionName}"));
=======
            return Task.FromException(new SKException($"Could not delete collection {collectionName}"));
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< div
>>>>>>> main
=======
<<<<<<< Updated upstream
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
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
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            return Task.FromException<string>(new KernelException($"Attempted to access a memory collection that does not exist: {collectionName}"));
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
<<<<<<< HEAD
            return Task.FromException<string>(new KernelException($"Attempted to access a memory collection that does not exist: {collectionName}"));
=======
            return Task.FromException<string>(new SKException($"Attempted to access a memory collection that does not exist: {collectionName}"));
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
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

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            if (record is not null)
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
            if (record is not null)
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
            if (record is not null)
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
            if (record is not null)
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
            if (record is not null)
=======
            if (record != null)
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
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
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            collectionDict.TryRemove(key, out _);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
<<<<<<< HEAD
            collectionDict.TryRemove(key, out _);
=======
            collectionDict.TryRemove(key, out MemoryRecord _);
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
        }

        return Task.CompletedTask;
    }

    /// <inheritdoc/>
    public Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        return Task.WhenAll(keys.Select(k => this.RemoveAsync(collectionName, k, cancellationToken)));
    }

<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> origin/main
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
<<<<<<< div
=======
<<<<<<< HEAD
>>>>>>> main
=======
>>>>>>> head
    /// <summary>
    /// Retrieves the nearest matches to the given embedding in the specified collection.
    /// </summary>
    /// <param name="collectionName">The name of the collection to search.</param>
    /// <param name="embedding">The embedding to find the nearest matches for.</param>
    /// <param name="limit">The maximum number of matches to return.</param>
    /// <param name="minRelevanceScore">The minimum relevance score for a match to be included in the results.</param>
    /// <param name="withEmbeddings">Whether to include the embeddings in the returned memory records.</param>
    /// <param name="cancellationToken">A cancellation token to cancel the operation.</param>
    /// <returns>An asynchronous enumerable of memory records and their relevance scores.</returns>
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> origin/main
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
<<<<<<< div
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> main
=======
>>>>>>> head
    public IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(
        string collectionName,
        ReadOnlyMemory<float> embedding,
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

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        if (embeddingCollection is null || embeddingCollection.Count == 0)
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        if (embeddingCollection is null || embeddingCollection.Count == 0)
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
        if (embeddingCollection is null || embeddingCollection.Count == 0)
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
        if (embeddingCollection is null || embeddingCollection.Count == 0)
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        if (embeddingCollection is null || embeddingCollection.Count == 0)
=======
        if (embeddingCollection == null || embeddingCollection.Count == 0)
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
        {
            return AsyncEnumerable.Empty<(MemoryRecord, double)>();
        }

        TopNCollection<MemoryRecord> embeddings = new(limit);

        foreach (var record in embeddingCollection)
        {
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            if (record is not null)
            {
                double similarity = TensorPrimitives.CosineSimilarity(embedding.Span, record.Embedding.Span);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< HEAD
>>>>>>> origin/main
<<<<<<< div
=======
<<<<<<< HEAD
>>>>>>> main
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
            if (record is not null)
            {
                double similarity = TensorPrimitives.CosineSimilarity(embedding.Span, record.Embedding.Span);
=======
            if (record != null)
            {
                double similarity = embedding
                    .Span
                    .CosineSimilarity(record.Embedding.Span);
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
                if (similarity >= minRelevanceScore)
                {
                    var entry = withEmbeddings ? record : MemoryRecord.FromMetadata(record.Metadata, ReadOnlyMemory<float>.Empty, record.Key, record.Timestamp);
                    embeddings.Add(new(entry, similarity));
                }
            }
        }

        embeddings.SortByScore();

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        return embeddings.Select(x => (x.Value, x.Score)).ToAsyncEnumerable();
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
<<<<<<< HEAD
        return embeddings.Select(x => (x.Value, x.Score)).ToAsyncEnumerable();
=======
        return embeddings.Select(x => (x.Value, x.Score.Value)).ToAsyncEnumerable();
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
    }

    /// <inheritdoc/>
    public async Task<(MemoryRecord, double)?> GetNearestMatchAsync(
        string collectionName,
        ReadOnlyMemory<float> embedding,
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
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
>>>>>>> head
    /// <summary>
    /// Tries to get the collection with the specified name.
    /// </summary>
    /// <param name="name">The name of the collection to get.</param>
    /// <param name="collection">The retrieved collection, if found.</param>
    /// <param name="create">Whether to create the collection if it does not exist.</param>
    /// <returns>True if the collection was found or created, false otherwise.</returns>
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======

>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======

>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======

>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======

>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======

>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======

>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======

>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
=======

>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======

>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
>>>>>>> head
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
