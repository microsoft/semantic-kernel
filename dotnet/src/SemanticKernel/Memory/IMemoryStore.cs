// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
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
    void CreateCollection(string collectionName);

    /// <summary>
    /// Deletes a collection from the datastore.
    /// </summary>
    /// <param name="collectionName"></param>
    void DeleteCollection(string collectionName);

    /// <summary>
    /// Upserts a memory record into the datastore.
    ///     If the record already exists, it will be updated.
    ///     If the record does not exist, it will be created.
    /// </summary>
    /// <param name="collectionName"></param>
    /// <param name="record"></param>
    /// <returns></returns>
    string Upsert(string collectionName, MemoryRecord record);

    /// <summary>
    /// Gets a memory record from the datastore.
    /// </summary>
    /// <param name="collectionName"></param>
    /// <param name="key"></param>
    /// <returns></returns>
    MemoryRecord? Get(string collectionName, string key);

    /// <summary>
    /// Gets a batch of memory records from the datastore.
    /// </summary>
    /// <param name="collectionName"></param>
    /// <param name="keys"></param>
    /// <returns></returns>
    IAsyncEnumerable<MemoryRecord> GetBatch(string collectionName, IEnumerable<string> keys);

    /// <summary>
    /// Removes a memory record from the datastore.
    /// </summary>
    /// <param name="collectionName"></param>
    /// <param name="key"></param>
    void Remove(string collectionName, string key);

    /// <summary>
    /// Removes a batch of memory records from the datastore.
    /// </summary>
    /// <param name="collectionName"></param>
    /// <param name="keys"></param>
    void RemoveBatch(string collectionName, IEnumerable<string> keys);

    /// <summary>
    /// Gets the nearest matches to the <see cref="Embedding"/> of type <see cref="float"/>.
    /// </summary>
    /// <param name="collection"></param>
    /// <param name="embedding"></param>
    /// <param name="limit"></param>
    /// <param name="minRelevanceScore"></param>
    /// <returns></returns>
    IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(
        string collection,
        Embedding<float> embedding,
        int limit = 1,
        double minRelevanceScore = 0.0);

    /// <summary>
    /// Gets the nearest match to the <see cref="Embedding"/> of type <see cref="float"/>.
    /// </summary>
    /// <param name="collection"></param>
    /// <param name="embedding"></param>
    /// <param name="minRelevanceScore"></param>
    /// <returns></returns>
    (MemoryRecord, double) GetNearestMatchAsync(
        string collection,
        Embedding<float> embedding,
        double minRelevanceScore = 0.0);
}
