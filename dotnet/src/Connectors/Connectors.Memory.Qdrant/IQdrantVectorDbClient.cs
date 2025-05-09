// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// Interface for a Qdrant vector database client.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and QdrantVectorStore")]
public interface IQdrantVectorDbClient
{
    /// <summary>
    /// Get vectors by their unique Qdrant IDs.
    /// </summary>
    /// <param name="collectionName">The name assigned to the collection of vectors.</param>
    /// <param name="pointIds">The unique IDs used to index Qdrant vector entries.</param>
    /// <param name="withVectors">Whether to include the vector data in the returned results.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An asynchronous list of Qdrant vectors records associated with the given IDs</returns>
    IAsyncEnumerable<QdrantVectorRecord> GetVectorsByIdAsync(string collectionName, IEnumerable<string> pointIds, bool withVectors = false,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Get a specific vector by a unique identifier in the metadata (Qdrant payload).
    /// </summary>
    /// <param name="collectionName">The name assigned to a collection of vectors.</param>
    /// <param name="metadataId">The unique ID stored in a Qdrant vector entry's metadata.</param>
    /// <param name="withVector">Whether to include the vector data in the returned result.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The Qdrant vector record associated with the given ID if found, null if not.</returns>
    Task<QdrantVectorRecord?> GetVectorByPayloadIdAsync(string collectionName, string metadataId, bool withVector = false, CancellationToken cancellationToken = default);

    /// <summary>
    /// Delete vectors by their unique Qdrant IDs.
    /// </summary>
    /// <param name="collectionName">The name assigned to a collection of vectors.</param>
    /// <param name="pointIds">The unique IDs used to index Qdrant vector entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    Task DeleteVectorsByIdAsync(string collectionName, IEnumerable<string> pointIds, CancellationToken cancellationToken = default);

    /// <summary>
    /// Delete a vector by its unique identifier in the metadata (Qdrant payload).
    /// </summary>
    /// <param name="collectionName">The name assigned to a collection of vectors.</param>
    /// <param name="metadataId">The unique ID stored in a Qdrant vector entry's metadata.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    Task DeleteVectorByPayloadIdAsync(string collectionName, string metadataId, CancellationToken cancellationToken = default);

    /// <summary>
    /// Upsert a group of vectors into a collection.
    /// </summary>
    /// <param name="collectionName">The name assigned to a collection of vectors.</param>
    /// <param name="vectorData">The Qdrant vector records to upsert.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    Task UpsertVectorsAsync(string collectionName, IEnumerable<QdrantVectorRecord> vectorData, CancellationToken cancellationToken = default);

    /// <summary>
    /// Find the nearest vectors in a collection using vector similarity search.
    /// </summary>
    /// <param name="collectionName">The name assigned to a collection of vectors.</param>
    /// <param name="target">The vector to compare the collection's vectors with.</param>
    /// <param name="threshold">The minimum relevance threshold for returned results.</param>
    /// <param name="top">The maximum number of similarity results to return.</param>
    /// <param name="withVectors">Whether to include the vector data in the returned results.</param>
    /// <param name="requiredTags">Qdrant tags used to filter the results.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    IAsyncEnumerable<(QdrantVectorRecord, double)> FindNearestInCollectionAsync(
        string collectionName,
        ReadOnlyMemory<float> target,
        double threshold,
        int top = 1,
        bool withVectors = false,
        IEnumerable<string>? requiredTags = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Create a Qdrant vector collection.
    /// </summary>
    /// <param name="collectionName">The name assigned to a collection of vectors.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default);

    /// <summary>
    /// Delete a Qdrant vector collection.
    /// </summary>
    /// <param name="collectionName">The name assigned to a collection of vectors.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default);

    /// <summary>
    /// Check if a vector collection exists.
    /// </summary>
    /// <param name="collectionName">The name assigned to a collection of vectors.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancellationToken = default);

    /// <summary>
    /// List all vector collections.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    IAsyncEnumerable<string> ListCollectionsAsync(CancellationToken cancellationToken = default);
}
