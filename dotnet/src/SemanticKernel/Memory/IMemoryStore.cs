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
    /// <param name="collectionName">The name associated with a collection of vectors.</param>
    /// <param name="cancel">Cancellation token.</param>
    Task CreateCollectionAsync(string collectionName, CancellationToken cancel = default);

    /// <summary>
    /// Gets all collection names in the datastore.
    /// </summary>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns>A group of collection names.</returns>
    IAsyncEnumerable<string> GetCollectionsAsync(CancellationToken cancel = default);

    /// <summary>
    /// Determines if a collection exists in the datastore.
    /// </summary>
    /// <param name="collectionName">The name associated with a collection of vectors.</param>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns>True if given collection exists, false if not.</returns>
    Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancel = default);

    /// <summary>
    /// Deletes a collection from the datastore.
    /// </summary>
    /// <param name="collectionName">The name associated with a collection of vectors.</param>
    /// <param name="cancel">Cancellation token.</param>
    Task DeleteCollectionAsync(string collectionName, CancellationToken cancel = default);

    /// <summary>
    /// Upserts a memory record into the datastore. Does not guarantee that the collection exists.
    ///     If the record already exists, it will be updated.
    ///     If the record does not exist, it will be created.
    /// </summary>
    /// <param name="collectionName">The name associated with a collection of vectors.</param>
    /// <param name="record">The memory record to upsert.</param>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns>The unique identifier for the memory record.</returns>
    Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancel = default);

    /// <summary>
    /// Upserts a group of memory records into the datastore. Does not guarantee that the collection exists.
    ///     If the record already exists, it will be updated.
    ///     If the record does not exist, it will be created.
    /// </summary>
    /// <param name="collectionName">The name associated with a collection of vectors.</param>
    /// <param name="records">The memory records to upsert.</param>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns>The unique identifiers for the memory records.</returns>
    IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> records, CancellationToken cancel = default);

    /// <summary>
    /// Gets a memory record from the datastore. Does not guarantee that the collection exists.
    /// </summary>
    /// <param name="collectionName">The name associated with a collection of vectors.</param>
    /// <param name="key">The unique id associated with the memory record to get.</param>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns>The memory record if found, otherwise null.</returns>
    Task<MemoryRecord?> GetAsync(string collectionName, string key, CancellationToken cancel = default);

    /// <summary>
    /// Gets a batch of memory records from the datastore. Does not guarantee that the collection exists.
    /// </summary>
    /// <param name="collectionName">The name associated with a collection of vectors.</param>
    /// <param name="keys">The unique ids associated with the memory record to get.</param>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns>The memory records associated with the unique keys provided.</returns>
    IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancel = default);

    /// <summary>
    /// Removes a memory record from the datastore. Does not guarantee that the collection exists.
    /// </summary>
    /// <param name="collectionName">The name associated with a collection of vectors.</param>
    /// <param name="key">The unique id associated with the memory record to remove.</param>
    /// <param name="cancel">Cancellation token.</param>
    Task RemoveAsync(string collectionName, string key, CancellationToken cancel = default);

    /// <summary>
    /// Removes a batch of memory records from the datastore. Does not guarantee that the collection exists.
    /// </summary>
    /// <param name="collectionName">The name associated with a collection of vectors.</param>
    /// <param name="keys">The unique ids associated with the memory record to remove.</param>
    /// <param name="cancel">Cancellation token.</param>
    Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancel = default);

    /// <summary>
    /// Gets the nearest matches to the <see cref="Embedding"/> of type <see cref="float"/>. Does not guarantee that the collection exists.
    /// </summary>
    /// <param name="collectionName">The name associated with a collection of vectors.</param>
    /// <param name="embedding">The <see cref="Embedding"/> to compare the collection's vectors with.</param>
    /// <param name="limit">The maximum number of similarity results to return.</param>
    /// <param name="minRelevanceScore">The minimum relevance threshold for returned results.</param>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns>A group of tuples where item1 is a <see cref="MemoryRecord"/> and item2 is its similarity score as a <see cref="double"/>.</returns>
    IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(
        string collectionName,
        Embedding<float> embedding,
        int limit,
        double minRelevanceScore = 0.0,
        CancellationToken cancel = default);

    /// <summary>
    /// Gets the nearest match to the <see cref="Embedding"/> of type <see cref="float"/>. Does not guarantee that the collection exists.
    /// </summary>
    /// <param name="collectionName">The name associated with a collection of vectors.</param>
    /// <param name="embedding">The vector to compare the collection's vectors with.</param>
    /// <param name="minRelevanceScore">The minimum relevance threshold for returned results.</param>
    /// <param name="cancel">Cancellation token</param>
    /// <returns>A tuple consisting of the <see cref="MemoryRecord"/> and the similarity score as a <see cref="double"/>. Null if no nearest match found.</returns>
    Task<(MemoryRecord, double)?> GetNearestMatchAsync(
        string collectionName,
        Embedding<float> embedding,
        double minRelevanceScore = 0.0,
        CancellationToken cancel = default);
}
