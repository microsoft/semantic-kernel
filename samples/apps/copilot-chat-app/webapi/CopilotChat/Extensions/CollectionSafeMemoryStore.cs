// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory;

namespace SemanticKernel.Service.CopilotChat.Extensions;

/// <summary>
/// This class is meant to mitigate the inconsistent behavior between memory stores where Qdrant accepts searching a non existant collection where as Chroma raises an exception, and the incomplete semantics of SemanticTextMemory where most operations check and create the collection if it doesn't exist, but search operation just pass the query to the memory store. 
/// </summary>
public class CollectionSafeMemoryStore : IMemoryStore
{
    private readonly IMemoryStore _unsafeMemoryStore;

    public CollectionSafeMemoryStore(IMemoryStore unsafeMemoryStore)
    {
        this._unsafeMemoryStore = unsafeMemoryStore;
    }

    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = new CancellationToken())
    {
        await this._unsafeMemoryStore.CreateCollectionAsync(collectionName, cancellationToken);
    }

    public IAsyncEnumerable<string> GetCollectionsAsync(CancellationToken cancellationToken = new CancellationToken())
    {
        return this._unsafeMemoryStore.GetCollectionsAsync(cancellationToken);
    }

    public async Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancellationToken = new CancellationToken())
    {
        return await this._unsafeMemoryStore.DoesCollectionExistAsync(collectionName, cancellationToken);
    }

    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = new CancellationToken())
    {
        await this._unsafeMemoryStore.DeleteCollectionAsync(collectionName, cancellationToken);
    }

    public async Task<string> UpsertAsync(string collectionName, MemoryRecord record,
        CancellationToken cancellationToken = new CancellationToken())
    {
        return await this._unsafeMemoryStore.UpsertAsync(collectionName, record, cancellationToken);
    }

    public IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> records,
        CancellationToken cancellationToken = new CancellationToken())
    {
        return this._unsafeMemoryStore.UpsertBatchAsync(collectionName, records, cancellationToken);
    }

    public async Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false,
        CancellationToken cancellationToken = new CancellationToken())
    {
        return await this._unsafeMemoryStore.GetAsync(collectionName, key, withEmbedding, cancellationToken);
    }

    public IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys, bool withEmbeddings = false,
        CancellationToken cancellationToken = new CancellationToken())
    {
        return this._unsafeMemoryStore.GetBatchAsync(collectionName, keys, withEmbeddings, cancellationToken);
    }

    public async Task RemoveAsync(string collectionName, string key, CancellationToken cancellationToken = new CancellationToken())
    {
        await this._unsafeMemoryStore.RemoveAsync(collectionName, key, cancellationToken);
    }

    public async Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys,
        CancellationToken cancellationToken = new CancellationToken())
    {
        await this._unsafeMemoryStore.RemoveBatchAsync(collectionName, keys, cancellationToken);
    }

    public async IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(string collectionName, Embedding<float> embedding, int limit,
        double minRelevanceScore = 0, bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = new CancellationToken())
    {
        await this.CheckAndCreateCollectionAsync(collectionName, cancellationToken);
        await foreach (var match in this._unsafeMemoryStore.GetNearestMatchesAsync(collectionName, embedding, limit, minRelevanceScore, withEmbeddings, cancellationToken))
        {
            yield return match;
        }
    }

    public async Task<(MemoryRecord, double)?> GetNearestMatchAsync(string collectionName, Embedding<float> embedding, double minRelevanceScore = 0,
        bool withEmbedding = false, CancellationToken cancellationToken = new CancellationToken())
    {
        await this.CheckAndCreateCollectionAsync(collectionName, cancellationToken);
        return await this._unsafeMemoryStore.GetNearestMatchAsync(collectionName, embedding, minRelevanceScore, withEmbedding, cancellationToken);
    }

    private ConcurrentDictionary<string, bool> _collectionChecked = new();
    private readonly SemaphoreSlim _collectionCheckLock = new SemaphoreSlim(1, 1);

    private async Task CheckAndCreateCollectionAsync(string collectionName, CancellationToken cancellationToken)
    {
        if (!this._collectionChecked.ContainsKey(collectionName))
        {
            // Wait until no other threads are in this section.
            await this._collectionCheckLock.WaitAsync(cancellationToken).ConfigureAwait(false);
            try
            {
                // We need to check again in case another thread added and created the collection while we were waiting for the lock.
                if (!this._collectionChecked.ContainsKey(collectionName))
                {
                    if (!await this.DoesCollectionExistAsync(collectionName, cancellationToken).ConfigureAwait(false))
                    {
                        await this.CreateCollectionAsync(collectionName, cancellationToken).ConfigureAwait(false);
                    }
                    this._collectionChecked[collectionName] = true;
                }
            }
            finally
            {
                // Release the lock so that other threads can enter.
                this._collectionCheckLock.Release();
            }
        }
    }
}
