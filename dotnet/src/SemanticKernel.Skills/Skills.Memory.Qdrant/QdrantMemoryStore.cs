// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.Diagnostics;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant;

/// <summary>
/// An implementation of <see cref="IMemoryStore"/> for Qdrant Vector database.
/// </summary>
/// <remarks>The Embedding data is saved to a Qdrant Vector database instance specified in the constructor by url and port.
/// The embedding data persists between subsequent instances and has similarity search capability.
/// </remarks>
public class QdrantMemoryStore : IMemoryStore
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
        this._qdrantClient = new QdrantVectorDbClient(endpoint: host, port: port, vectorSize: vectorSize, log: logger);
    }

    /// <inheritdoc/>
    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancel = default)
    {
        if (!await this._qdrantClient.DoesCollectionExistAsync(collectionName, cancel: cancel))
        {
            await this._qdrantClient.CreateCollectionAsync(collectionName, cancel: cancel);
        }
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<string> GetCollectionsAsync(CancellationToken cancel = default)
    {
        return this._qdrantClient.ListCollectionsAsync(cancel: cancel);
    }

    /// <inheritdoc/>
    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancel = default)
    {
        await this._qdrantClient.DeleteCollectionAsync(collectionName, cancel: cancel);
    }

    public async Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancel = default)
    {
        if (!await this._qdrantClient.DoesCollectionExistAsync(collectionName, cancel: cancel))
        {
            await this._qdrantClient.CreateCollectionAsync(collectionName, cancel: cancel);
        }

        string pointId;
        QdrantVectorRecord? existingRecord = null;

        // Check if a database key has been provided for update
        if (!string.IsNullOrEmpty(record.Key))
        {
            pointId = record.Key;
        }
        // Check if the data store contains a record with the provided metadata ID
        else
        {
            existingRecord = await this._qdrantClient.GetVectorByPayloadIdAsync(collectionName, record.Metadata.Id, cancel: cancel);
            
            if (existingRecord != null)
            {
                pointId = existingRecord.PointId;
            }
            else
            {
                // If no matching record can be found, generate an ID for the new record
                pointId = Guid.NewGuid().ToString();
                existingRecord = await this._qdrantClient.GetVectorByIdAsync(collectionName, pointId, cancel: cancel);
                if (existingRecord != null)
                {
                    throw new VectorDbException(VectorDbException.ErrorCodes.NewGuidAlreadyExistsInCollection, $"Failed to generate unique ID for new record");
                }
            }
        }
        
        var vectorData = QdrantVectorRecord.FromJson(
            pointId: pointId,
            embedding: record.Embedding.Vector,
            json: record.GetSerializedMetadata());
        
        await this._qdrantClient.UpsertVectorAsync(collectionName, vectorData, cancel: cancel);

        return pointId;
    }

    public IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> record, CancellationToken cancel = default)
    {
        throw new NotImplementedException();
    }

    public async Task<MemoryRecord?> GetAsync(string collectionName, string key, CancellationToken cancel = default)
    {
        try
        {
            var vectorData = await this._qdrantClient.GetVectorByPayloadIdAsync(collectionName, key, cancel: cancel);
            if (vectorData != null)
            {
                return MemoryRecord.FromJson(vectorData.GetSerializedPayload(), new Embedding<float>(vectorData.Embedding));
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

    public async Task<MemoryRecord?> GetWithPointIdAsync(string collectionName, string pointId, CancellationToken cancel = default)
    {
        try
        {
            var vectorData = await this._qdrantClient.GetVectorByIdAsync(collectionName, pointId, cancel: cancel);
            if (vectorData != null)
            {
                return MemoryRecord.FromJson(
                    json: vectorData.GetSerializedPayload(),
                    embedding: new Embedding<float>(vectorData.Embedding));
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

    public IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancel = default)
    {
        throw new NotImplementedException();
    }

    public async Task RemoveAsync(string collectionName, string key, CancellationToken cancel = default)
    {
        try
        {
            await this._qdrantClient.DeleteVectorByIdAsync(collectionName, key, cancel: cancel);
        }
        catch (Exception ex)
        {
            throw new VectorDbException($"Failed to remove vector data from Qdrant {ex.Message}");
        }
    }

    public Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancel = default)
    {
        throw new NotImplementedException();
    }

    public async IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(
        string collectionName,
        Embedding<float> embedding,
        int limit,
        double minRelevanceScore = 0,
        CancellationToken cancel = default)
    {
        var results = this._qdrantClient.FindNearestInCollectionAsync(
            collectionName: collectionName,
            target: embedding.Vector,
            threshold: minRelevanceScore,
            top: limit,
            cancel: cancel);
        
        await foreach ((QdrantVectorRecord, double) result in results)
        {
            yield return (
                MemoryRecord.FromJson(
                    json: result.Item1.GetSerializedPayload(),
                    embedding: new Embedding<float>(result.Item1.Embedding)),
                result.Item2);
        }
    }

    public async Task<(MemoryRecord, double)?> GetNearestMatchAsync(
        string collectionName,
        Embedding<float> embedding,
        double minRelevanceScore = 0,
        CancellationToken cancel = default)
    {
        var results = this.GetNearestMatchesAsync(
            collectionName: collectionName,
            embedding: embedding,
            minRelevanceScore: minRelevanceScore,
            limit: 1,
            cancel: cancel);

        var record = await results.FirstOrDefaultAsync(cancellationToken: cancel);

        return (record.Item1, record.Item2);
    }

    #region private ================================================================================

    /// <summary>
    /// Concurrent dictionary consisting of Qdrant Collection names mapped to
    /// a concurrent dictionary of cached Qdrant vector entries mapped by plaintext key
    /// </summary>
    private readonly QdrantVectorDbClient _qdrantClient;
    
    #endregion
}
