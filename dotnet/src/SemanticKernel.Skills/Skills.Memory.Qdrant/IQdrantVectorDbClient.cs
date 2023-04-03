// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using System.Threading;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.Diagnostics;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant;

public interface IQdrantVectorDbClient
{
    /// <summary>
    /// Get a specific vector by its unique Qdrant ID.
    /// </summary>
    /// <param name="collectionName"></param>
    /// <param name="pointIds"></param>
    /// <param name="cancel"></param>
    /// <returns></returns>
    public IAsyncEnumerable<QdrantVectorRecord> GetVectorsByIdAsync(string collectionName, IEnumerable<string> pointIds,
        CancellationToken cancel = default);

    /// <summary>
    /// Get a specific vector by a unique identifier in the metadata (Qdrant payload).
    /// </summary>
    /// <param name="collectionName"></param>
    /// <param name="metadataId"></param>
    /// <param name="cancel"></param>
    /// <returns></returns>
    public Task<QdrantVectorRecord?> GetVectorByPayloadIdAsync(string collectionName, string metadataId, CancellationToken cancel = default);

    /// <summary>
    /// Delete a vector by its unique Qdrant ID.
    /// </summary>
    /// <param name="collectionName"></param>
    /// <param name="pointIds"></param>
    /// <param name="cancel"></param>
    /// <returns></returns>
    public Task DeleteVectorsByIdAsync(string collectionName, IEnumerable<string> pointIds, CancellationToken cancel = default);

    /// <summary>
    /// Delete a vector by its unique identifier in the metadata (Qdrant payload).
    /// </summary>
    /// <param name="collectionName"></param>
    /// <param name="metadataId"></param>
    /// <param name="cancel"></param>
    /// <returns></returns>
    public Task DeleteVectorByPayloadIdAsync(string collectionName, string metadataId, CancellationToken cancel = default);

    /// <summary>
    /// Upsert a group of vectors into a collection.
    /// </summary>
    /// <param name="collectionName"></param>
    /// <param name="vectorData"></param>
    /// <param name="cancel"></param>
    /// <returns></returns>
    public Task UpsertVectorsAsync(string collectionName, IEnumerable<QdrantVectorRecord> vectorData, CancellationToken cancel = default);

    /// <summary>
    /// Find the nearest vectors in a collection using vector similarity search.
    /// </summary>
    /// <param name="collectionName"></param>
    /// <param name="target"></param>
    /// <param name="threshold"></param>
    /// <param name="top"></param>
    /// <param name="requiredTags"></param>
    /// <param name="cancel"></param>
    /// <returns></returns>
    public IAsyncEnumerable<(QdrantVectorRecord, double)> FindNearestInCollectionAsync(
        string collectionName,
        IEnumerable<float> target,
        double threshold,
        int top = 1,
        IEnumerable<string>? requiredTags = null,
        CancellationToken cancel = default);

    /// <summary>
    /// Create a Qdrant vector collection.
    /// </summary>
    /// <param name="collectionName"></param>
    /// <param name="cancel"></param>
    /// <returns></returns>
    public Task CreateCollectionAsync(string collectionName, CancellationToken cancel = default);

    /// <summary>
    /// Delete a Qdrant vector collection.
    /// </summary>
    /// <param name="collectionName"></param>
    /// <param name="cancel"></param>
    /// <returns></returns>
    public Task DeleteCollectionAsync(string collectionName, CancellationToken cancel = default);

    /// <summary>
    /// Check if a vector collection exists.
    /// </summary>
    /// <param name="collectionName"></param>
    /// <param name="cancel"></param>
    /// <returns></returns>
    /// <exception cref="VectorDbException"></exception>
    public Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancel = default);

    /// <summary>
    /// List all vector collections.
    /// </summary>
    /// <param name="cancel"></param>
    /// <returns></returns>
    public IAsyncEnumerable<string> ListCollectionsAsync(CancellationToken cancel = default);

}
