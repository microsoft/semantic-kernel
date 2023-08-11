// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// An interface for storing and retrieving indexed <see cref="MemoryRecord"/> objects in a data store.
/// </summary>
public interface IMemoryStore
{
    /// <summary>
    /// Creates a new collection in the data store.
    /// </summary>
    /// <param name="collectionName">The name associated with a collection of embeddings.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets all collection names in the data store.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A group of collection names.</returns>
    IAsyncEnumerable<string> GetCollectionsAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Determines if a collection exists in the data store.
    /// </summary>
    /// <param name="collectionName">The name associated with a collection of embeddings.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>True if given collection exists, false if not.</returns>
    Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancellationToken = default);

    /// <summary>
    /// Deletes a collection from the data store.
    /// </summary>
    /// <param name="collectionName">The name associated with a collection of embeddings.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default);

    /// <summary>
    /// Upserts a memory record into the data store. Does not guarantee that the collection exists.
    ///     If the record already exists, it will be updated.
    ///     If the record does not exist, it will be created.
    /// </summary>
    /// <param name="collectionName">The name associated with a collection of embeddings.</param>
    /// <param name="record">The memory record to upsert.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The unique identifier for the memory record.</returns>
    Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken = default);

    /// <summary>
    /// Upserts a group of memory records into the data store. Does not guarantee that the collection exists.
    ///     If the record already exists, it will be updated.
    ///     If the record does not exist, it will be created.
    /// </summary>
    /// <param name="collectionName">The name associated with a collection of vectors.</param>
    /// <param name="records">The memory records to upsert.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The unique identifiers for the memory records.</returns>
    IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> records, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets a memory record from the data store. Does not guarantee that the collection exists.
    /// </summary>
    /// <param name="collectionName">The name associated with a collection of embeddings.</param>
    /// <param name="key">The unique id associated with the memory record to get.</param>
    /// <param name="withEmbedding">If true, the embedding will be returned in the memory record.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The memory record if found, otherwise null.</returns>
    Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets a batch of memory records from the data store. Does not guarantee that the collection exists.
    /// </summary>
    /// <param name="collectionName">The name associated with a collection of embedding.</param>
    /// <param name="keys">The unique ids associated with the memory record to get.</param>
    /// <param name="withEmbeddings">If true, the embeddings will be returned in the memory records.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The memory records associated with the unique keys provided.</returns>
    IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys, bool withEmbeddings = false, CancellationToken cancellationToken = default);

    /// <summary>
    /// Removes a memory record from the data store. Does not guarantee that the collection exists.
    /// </summary>
    /// <param name="collectionName">The name associated with a collection of embeddings.</param>
    /// <param name="key">The unique id associated with the memory record to remove.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    Task RemoveAsync(string collectionName, string key, CancellationToken cancellationToken = default);

    /// <summary>
    /// Removes a batch of memory records from the data store. Does not guarantee that the collection exists.
    /// </summary>
    /// <param name="collectionName">The name associated with a collection of embeddings.</param>
    /// <param name="keys">The unique ids associated with the memory record to remove.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets the nearest matches to the <see cref="Embedding{Single}"/> of type <see cref="float"/>. Does not guarantee that the collection exists.
    /// </summary>
    /// <param name="collectionName">The name associated with a collection of embeddings.</param>
    /// <param name="embedding">The <see cref="Embedding{Single}"/> to compare the collection's embeddings with.</param>
    /// <param name="limit">The maximum number of similarity results to return.</param>
    /// <param name="minRelevanceScore">The minimum relevance threshold for returned results.</param>
    /// <param name="withEmbeddings">If true, the embeddings will be returned in the memory records.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A group of tuples where item1 is a <see cref="MemoryRecord"/> and item2 is its similarity score as a <see cref="double"/>.</returns>
    IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(
        string collectionName,
        ReadOnlyMemory<float> embedding,
        int limit,
        double minRelevanceScore = 0.0,
        bool withEmbeddings = false,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets the nearest match to the <see cref="Embedding{Single}"/> of type <see cref="float"/>. Does not guarantee that the collection exists.
    /// </summary>
    /// <param name="collectionName">The name associated with a collection of embeddings.</param>
    /// <param name="embedding">The <see cref="Embedding{Single}"/> to compare the collection's embeddings with.</param>
    /// <param name="minRelevanceScore">The minimum relevance threshold for returned results.</param>
    /// <param name="withEmbedding">If true, the embedding will be returned in the memory record.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A tuple consisting of the <see cref="MemoryRecord"/> and the similarity score as a <see cref="double"/>. Null if no nearest match found.</returns>
    Task<(MemoryRecord, double)?> GetNearestMatchAsync(
        string collectionName,
        ReadOnlyMemory<float> embedding,
        double minRelevanceScore = 0.0,
        bool withEmbedding = false,
        CancellationToken cancellationToken = default);
}
