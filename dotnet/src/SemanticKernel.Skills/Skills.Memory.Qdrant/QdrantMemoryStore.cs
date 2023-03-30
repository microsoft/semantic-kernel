// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Memory.Storage;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.Diagnostics;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant;

/// <summary>
/// An implementation of <see cref="IMemoryStore{TEmbedding}"/> for Qdrant Vector database.
/// </summary>
/// <remarks>The Embedding data is saved to a Qdrant Vector database instance specified in the constructor by url and port.
/// The embedding data persists between subsequent instances and has similarity search capability.
/// </remarks>
public class QdrantMemoryStore<TEmbedding> : IMemoryStore<TEmbedding>
    where TEmbedding : unmanaged
{
    /// <summary>
    /// Constructor for a memory store backed by a Qdrant Vector database instance.
    /// </summary>
    /// <param name="host"></param>
    /// <param name="port"></param>
    /// <param name="vectorSize"></param>
    /// <param name="logger"></param>
    public QdrantMemoryStore(string host, int port, int vectorSize, ILogger? logger = null)
    {
        this._qdrantClient = new QdrantVectorDbClient<TEmbedding>(endpoint: host, port: port, vectorSize: vectorSize, log: logger);
    }

    /// <inheritdoc />
    public async Task<DataEntry<IEmbeddingWithMetadata<TEmbedding>>?> GetAsync(string collection, string key, CancellationToken cancel = default)
    {
        try
        {
            var vectorData = await this._qdrantClient.GetVectorByPayloadIdAsync(collection, key);
            if (vectorData != null && vectorData.Value.HasValue)
            {
                return new DataEntry<IEmbeddingWithMetadata<TEmbedding>>(
                    key: key,
                    value: vectorData.Value.Value);
            }
            else
            {
                return null;
            }
        }
        catch (Exception ex)
        {
            throw new VectorDbException($"Failed to get vector data from Qdrant {ex.Message}");
        }
    }

    /// <inheritdoc />
    public async Task<DataEntry<IEmbeddingWithMetadata<TEmbedding>>> PutAsync(
        string collection,
        DataEntry<IEmbeddingWithMetadata<TEmbedding>> data,
        CancellationToken cancel = default)
    {
        if (!await this._qdrantClient.DoesCollectionExistAsync(collection))
        {
            await this._qdrantClient.CreateCollectionAsync(collection);
        }

        var vectorData = new DataEntry<QdrantVectorRecord<TEmbedding>>(
            key: data.Key,
            value: QdrantVectorRecord<TEmbedding>.FromJson(data.Value!.Embedding, data.Value.GetSerializedMetadata()));
        await this._qdrantClient.UpsertVectorAsync(collection, vectorData);

        return data;
    }

    /// <inheritdoc />
    public async Task RemoveAsync(string collection, string key, CancellationToken cancel = default)
    {
        try
        {
            await this._qdrantClient.DeleteVectorByIdAsync(collection, key);
        }
        catch (Exception ex)
        {
            throw new VectorDbException($"Failed to remove vector data from Qdrant {ex.Message}");
        }
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<(IEmbeddingWithMetadata<TEmbedding>, double)> GetNearestMatchesAsync(
        string collection,
        Embedding<TEmbedding> embedding,
        int limit = 1,
        double minRelevanceScore = 0)
    {
        var results = this._qdrantClient.FindNearestInCollectionAsync(collection, embedding, minRelevanceScore, limit);
        await foreach ((IEmbeddingWithMetadata<TEmbedding>, double) result in results)
        {
            yield return result;
        }
    }

    /// <inheritdoc />
    public IAsyncEnumerable<string> GetCollectionsAsync(CancellationToken cancel = default)
    {
        return this._qdrantClient.ListCollectionsAsync();
    }

    /// <summary>
    /// Deletes a collection from the Qdrant Vector database.
    /// </summary>
    /// <param name="collection"></param>
    /// <returns></returns>
    public async Task DeleteCollectionAsync(string collection)
    {
        await this._qdrantClient.DeleteCollectionAsync(collection);
    }

    #region private ================================================================================

    /// <summary>
    /// Concurrent dictionary consisting of Qdrant Collection names mapped to
    /// a concurrent dictionary of cached Qdrant vector entries mapped by plaintext key
    /// </summary>
    private readonly QdrantVectorDbClient<TEmbedding> _qdrantClient;

    #endregion
}

/// <summary>
/// Default constructor for a Qdrant memory embeddings store for embeddings - defaults to floating point vectors.
/// The default embedding type is <see cref="float"/>.
/// </summary>
public class QdrantMemoryStore : QdrantMemoryStore<float>
{
    public QdrantMemoryStore(string host, int port, int vectorSize, ILogger? logger = null) : base(host, port, vectorSize, logger)
    {
    }
}
