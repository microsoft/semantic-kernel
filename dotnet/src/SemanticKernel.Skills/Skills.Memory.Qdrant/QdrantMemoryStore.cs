// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Memory.Storage;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.DataModels;
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
    public QdrantMemoryStore(string host, int port)
    {
        this._qdrantClient = new QdrantVectorDbClient<TEmbedding>(host, port);
    }

    public async Task<DataEntry<IEmbeddingWithMetadata<TEmbedding>>?> GetAsync(string collection, string key, CancellationToken cancel = default)
    {
        DataEntry<QdrantVectorRecord<TEmbedding>> vectorResult = default;

        if (!this._qdrantData.TryGetValue(collection, out var value) && value.TryGetValue(key, out vectorResult))
        {
            try
            {
                // Qdrant entries are uniquely identified by Base-64 or UUID strings
                var vectorData = await this._qdrantClient.GetVectorByIdAsync(collection, key);
                if (vectorData != null)
                {
                    if (!this._qdrantData.ContainsKey(collection))
                    {
                        this._qdrantData.TryAdd(collection, new ConcurrentDictionary<string, DataEntry<QdrantVectorRecord<TEmbedding>>>());
                    }

                    this._qdrantData[collection].TryAdd(key, vectorData.Value);

                    vectorResult = vectorData.Value;
                }
            }
            catch (Exception ex)
            {
                throw new VectorDbException($"Failed to get vector data from Qdrant {ex.Message}");
            }
        }

        return new DataEntry<IEmbeddingWithMetadata<TEmbedding>>(
            key: key,
            value: (IEmbeddingWithMetadata<TEmbedding>)vectorResult.Value!);
    }

    public async Task<DataEntry<IEmbeddingWithMetadata<TEmbedding>>> PutAsync(string collection, DataEntry<IEmbeddingWithMetadata<TEmbedding>> data, CancellationToken cancel = default)
    {
        var collectionExists = await this._qdrantClient.IsExistingCollection(collection);
        if (!collectionExists)
        {
            await this._qdrantClient.CreateNewCollectionAsync(collection);
        }

        var vectorData = new DataEntry<QdrantVectorRecord<TEmbedding>>(
            key: data.Key,
            value: QdrantVectorRecord<TEmbedding>.FromJson(data.Value!.Embedding, data.Value.JsonSerializeMetadata()));
        await this._qdrantClient.UpsertVectorAsync(collection, vectorData);

        return data;
    }

    public async Task RemoveAsync(string collection, string key, CancellationToken cancel = default)
    {
        try
        {
            await this._qdrantClient.DeleteVectorAsync(collection, key);
        }
        catch (Exception ex)
        {
            throw new VectorDbException($"Failed to remove vector data from Qdrant {ex.Message}");
        }
    }

    public async IAsyncEnumerable<(IEmbeddingWithMetadata<TEmbedding>, double)> GetNearestMatchesAsync(string collection, Embedding<TEmbedding> embedding, int limit = 1, double minRelevanceScore = 0)
    {
        var results = this._qdrantClient.FindNearesetInCollectionAsync(collection, embedding, limit);
        await foreach ((IEmbeddingWithMetadata<TEmbedding>, double) result in results)
        {
            yield return result;
        }
    }

    public IAsyncEnumerable<string> GetCollectionsAsync(CancellationToken cancel = default)
    {
        return this._qdrantClient.GetCollectionListAsync();
    }

    #region private ================================================================================

    /// <summary>
    /// Concurrent dictionary consisting of Qdrant Collection names mapped to
    /// a concurrent dictionary of cached Qdrant vector entries mapped by plaintext key
    /// </summary>
    private readonly ConcurrentDictionary<string, ConcurrentDictionary<string, DataEntry<QdrantVectorRecord<TEmbedding>>>> _qdrantData = new();
    private QdrantVectorDbClient<TEmbedding> _qdrantClient;

    #endregion
}

/// <summary>
/// Default constructor for a Qdrant memory embeddings store for embeddings - defaults to floating point vectors.
/// The default embedding type is <see cref="float"/>.
/// </summary>
public class QdrantMemoryStore : QdrantMemoryStore<float>
{
    public QdrantMemoryStore(string host, int port) : base(host, port)
    {
    }
}
