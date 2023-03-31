// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// An interface for storing and retrieving indexed <see cref="MemoryRecord"/> objects in a datastore.
/// </summary>
public interface IMemoryStore
{
    /// <summary>
    /// Creates a new collection in the datastore.
    /// </summary>
    /// <param name="collectionName"></param>
    /// <param name="cancel"></param>
    Task CreateCollectionAsync(string collectionName, CancellationToken cancel = default);

    /// <summary>
    /// Gets all collection names in the datastore.
    /// </summary>
    /// <param name="cancel"></param>
    /// <returns>A group of collection names</returns>
    IAsyncEnumerable<string> GetCollectionsAsync(CancellationToken cancel = default);

    /// <summary>
    /// Deletes a collection from the datastore.
    /// </summary>
    /// <param name="collectionName"></param>
    /// <param name="cancel"></param>
    Task DeleteCollectionAsync(string collectionName, CancellationToken cancel = default);

    /// <summary>
    /// Upserts a memory record into the datastore.
    ///     If the record already exists, it will be updated.
    ///     If the record does not exist, it will be created.
    /// </summary>
    /// <param name="collectionName"></param>
    /// <param name="record"></param>
    /// <param name="cancel"></param>
    /// <returns>The unique identifier for the memory record.</returns>
    Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancel = default);

    /// <summary>
    /// Upserts a group of memory records into the datastore.
    ///     If the record already exists, it will be updated.
    ///     If the record does not exist, it will be created.
    /// </summary>
    /// <param name="collectionName"></param>
    /// <param name="record"></param>
    /// <param name="cancel"></param>
    /// <returns>The unique identifiers for the memory records.</returns>
    IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> record, CancellationToken cancel = default);

    /// <summary>
    /// Gets a memory record from the datastore.
    /// </summary>
    /// <param name="collectionName"></param>
    /// <param name="key"></param>
    /// <param name="cancel"></param>
    /// <returns>The memory record if found, otherwise Null</returns>
    Task<MemoryRecord?> GetAsync(string collectionName, string key, CancellationToken cancel = default);

    /// <summary>
    /// Gets a batch of memory records from the datastore.
    /// </summary>
    /// <param name="collectionName"></param>
    /// <param name="keys"></param>
    /// <param name="cancel"></param>
    /// <returns>The memory records associated with the unique keys provided</returns>
    IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancel = default);

    /// <summary>
    /// Removes a memory record from the datastore.
    /// </summary>
    /// <param name="collectionName"></param>
    /// <param name="key"></param>
    /// <param name="cancel"></param>
    Task RemoveAsync(string collectionName, string key, CancellationToken cancel = default);

    /// <summary>
    /// Removes a batch of memory records from the datastore.
    /// </summary>
    /// <param name="collectionName"></param>
    /// <param name="keys"></param>
    /// <param name="cancel"></param>
    Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancel = default);

    /// <summary>
    /// Gets the nearest matches to the <see cref="Embedding"/> of type <see cref="float"/>.
    /// </summary>
    /// <param name="collectionName"></param>
    /// <param name="embedding"></param>
    /// <param name="limit"></param>
    /// <param name="minRelevanceScore"></param>
    /// <param name="cancel"></param>
    /// <returns>A group of tuples where item1 is a <see cref="MemoryRecord"/> and item2 is its similarity score as a <see cref="double"/>.</returns>
    IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(
        string collectionName,
        Embedding<float> embedding,
        int limit,
        double minRelevanceScore = 0.0,
        CancellationToken cancel = default);

    /// <summary>
    /// Gets the nearest match to the <see cref="Embedding"/> of type <see cref="float"/>.
    /// </summary>
    /// <param name="collectionName"></param>
    /// <param name="embedding"></param>
    /// <param name="minRelevanceScore"></param>
    /// <param name="cancel"></param>
    /// <returns>A tuple consisting of the <see cref="MemoryRecord"/> and the similarity score as a <see cref="double"/>. Null if no nearest match found.</returns>
    Task<(MemoryRecord, double)?> GetNearestMatchAsync(
        string collectionName,
        Embedding<float> embedding,
        double minRelevanceScore = 0.0,
        CancellationToken cancel = default);
}
