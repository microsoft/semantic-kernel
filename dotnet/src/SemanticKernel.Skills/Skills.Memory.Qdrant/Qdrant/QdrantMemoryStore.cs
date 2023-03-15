// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory.Storage;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.SDKClient;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.SDKClient.Internal.Diagnostics;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant;

/// <summary>
/// An implementation of <see cref="ILongTermMemoryStore{TEmbedding}"/> which is an embedding of type float
/// backed by a Qdrant Vector database. The type of Embedding (float) to be stored in this data store which has the interface of
/// <see cref="IDataStore{VectorRecordData}"/>
/// </summary>
/// <remarks>The Embedding data is saved to a Qdrant Vector database instance specified in the constructor by url and port.
/// The embedding data persists between subsequent instances and has similarity search capability.
/// </remarks>
public class QdrantMemoryStore : ILongTermMemoryStore<float>
{
    public QdrantMemoryStore(string host, int port)
    {
        this._qdrantClient = new QdrantVectorDb(host, port);
    }

    public IAsyncEnumerable<string> GetCollectionsAsync(CancellationToken cancel = default)
    {
        return AsyncEnumerable.Empty<string>();
    }

    public async Task<DataEntry<VectorRecordData<float>>?> GetAsync(string collection, string key, CancellationToken cancel = default)
    {
        DataEntry<VectorRecordData<float>> vectorResult = default;

        if (!this._qdrantData.TryGetValue(collection, out var value) && value.TryGetValue(key, out vectorResult))
        {
            try
            {
                var vectorData = await this._qdrantClient.GetVectorDataAsync(collection, key);
                if (vectorData != null)
                {
                    if (!this._qdrantData.ContainsKey(collection))
                    {
                        this._qdrantData.TryAdd(collection, new ConcurrentDictionary<string, DataEntry<VectorRecordData<float>>>());
                        this._qdrantData[collection].TryAdd(key, vectorData);
                    }
                    else
                    {
                        this._qdrantData[collection].TryAdd(key, vectorData);
                    }

                    vectorResult = vectorData;
                }
            }
            catch (Exception ex)
            {
                throw new VectorDbException($"Failed to get vector data from Qdrant {ex.Message}");
            }
        }

        return vectorResult;
    }

    public async Task<DataEntry<VectorRecordData<float>>> PutAsync(string collection, DataEntry<VectorRecordData<float>> data,
        CancellationToken cancel = default)
    {
        DataEntry<VectorRecordData<float>> vectorData; //= new DataEntry<VectorRecordData<float>>(data.Key, data.Value);
        bool result = await this._qdrantClient.PutVectorDataAsync<DataEntry<VectorRecordData<float>>>(collection, data.Key, data, data.Value!.Payload);
        if (!result)
        {
            throw new VectorDbException("Failed to put vector data into Qdrant");
        }

        vectorData = await this._qdrantClient.GetVectorDataAsync(collection, data.Key);

        if (vectorData == null)
        {
            throw new VectorDbException("Failed to put and retrieve vector data from Qdrant");
        }

        return vectorData;
    }

    public async Task RemoveAsync(string collection, string key, CancellationToken cancel = default)
    {
        bool result;
        try
        {
            result = await this._qdrantClient.DeleteVectorDataAsync(collection, key);
            if (result)
            {
                if (this._qdrantData.TryGetValue(collection, out var value) && value.ContainsKey(key))
                {
                    value.TryRemove(key, out _);
                }
            }
        }
        catch (Exception ex)
        {
            throw new VectorDbException($"Failed to remove vector data from Qdrant {ex.Message}");
        }
    }

    public async IAsyncEnumerable<(VectorRecordData<float>, double)> GetNearestMatchesAsync(string collection, Embedding<float> embedding, int limit = 1,
        double minRelevanceScore = 0)
    {
        DataEntry<VectorRecordData<float>> vectorData = new DataEntry<VectorRecordData<float>>()
        {
            Value = new VectorRecordData<float>(embedding, new Dictionary<string, object>(), new List<string>()),
            Timestamp = DateTime.Now,
        };

        var result = await this._qdrantClient.SearchVectorBySimilarityAsync(collection, vectorData, minRelevanceScore);
        await foreach (var rd in result.ToAsyncEnumerable())
        {
            yield return (rd.Key.Value!, rd.Value);
        }
    }

    async IAsyncEnumerable<(IEmbeddingWithMetadata<float>, double)> IEmbeddingIndex<float>.GetNearestMatchesAsync(string collection, Embedding<float> embedding,
        int limit, double minRelevanceScore)
    {
        DataEntry<VectorRecordData<float>> vectorData = new DataEntry<VectorRecordData<float>>()
        {
            Value = new VectorRecordData<float>(embedding, new Dictionary<string, object>(), new List<string>()),
            Timestamp = DateTime.Now,
        };
        var result = await this._qdrantClient.SearchVectorBySimilarityAsync(collection, vectorData, minRelevanceScore);
        await foreach (var match in result.ToAsyncEnumerable())
        {
            yield return (match.Key.Value!, match.Value);
        }
    }

    public async IAsyncEnumerable<DataEntry<VectorRecordData<float>>> GetAllAsync(string collection,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        IAsyncEnumerable<DataEntry<VectorRecordData<float>>> vectorResult;
        IVectorDbCollection vectorCollection = await this._qdrantClient.GetCollectionDataAsync(collection);

        vectorResult = vectorCollection.GetAllVectorsAsync()!;

        await foreach (var v in vectorResult)
        {
            yield return v;
        }
    }

    IAsyncEnumerable<DataEntry<IEmbeddingWithMetadata<float>>> IDataStore<IEmbeddingWithMetadata<float>>.GetAllAsync(string collection,
        CancellationToken cancel)
    {
        IAsyncEnumerable<DataEntry<VectorRecordData<float>>> vectorResult = this.GetAllAsync(collection, CancellationToken.None);
        IAsyncEnumerable<DataEntry<IEmbeddingWithMetadata<float>>> result = vectorResult.Select(x =>
            new DataEntry<IEmbeddingWithMetadata<float>>(x.Key, x.Value));
        return result;
    }

    public async Task<DataEntry<IEmbeddingWithMetadata<float>>> PutAsync(string collection, DataEntry<IEmbeddingWithMetadata<float>> data,
        CancellationToken cancel = default)
    {
        VectorRecordData<float> vectorData = new VectorRecordData<float>(data.Value!.Embedding, new Dictionary<string, object>(), new List<string>());
        DataEntry<VectorRecordData<float>> dataEntry = new DataEntry<VectorRecordData<float>>(data.Key, vectorData);
        var result = await this.PutAsync(collection, dataEntry, CancellationToken.None);

        DataEntry<IEmbeddingWithMetadata<float>> resultData = new DataEntry<IEmbeddingWithMetadata<float>>(result.Key, result.Value);
        return resultData;
    }

    async Task<DataEntry<IEmbeddingWithMetadata<float>>?> IDataStore<IEmbeddingWithMetadata<float>>.GetAsync(string collection, string key,
        CancellationToken cancel)
    {
        DataEntry<VectorRecordData<float>>? result = await this.GetAsync(collection, key, CancellationToken.None);
        string datakey = result.Value.Key;
        IEmbeddingWithMetadata<float> data = result.Value.Value!;

        DataEntry<IEmbeddingWithMetadata<float>>? resultData = new DataEntry<IEmbeddingWithMetadata<float>>(datakey, data);
        return resultData;
    }

    #region private ================================================================================

    private readonly ConcurrentDictionary<string, ConcurrentDictionary<string, DataEntry<VectorRecordData<float>>>> _qdrantData = new();
    private QdrantVectorDb _qdrantClient;

    #endregion
}
