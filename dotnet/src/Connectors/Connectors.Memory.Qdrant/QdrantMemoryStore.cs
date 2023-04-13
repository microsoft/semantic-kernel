// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Connectors.Memory.Qdrant.Diagnostics;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Memory.Qdrant;

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

    /// <summary>
    /// Constructor for a memory store backed by a <see cref="IQdrantVectorDbClient"/>
    /// </summary>
    public QdrantMemoryStore(IQdrantVectorDbClient client)
    {
        this._qdrantClient = client;
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
    public async Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancel = default)
    {
        return await this._qdrantClient.DoesCollectionExistAsync(collectionName, cancel: cancel);
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<string> GetCollectionsAsync(CancellationToken cancel = default)
    {
        return this._qdrantClient.ListCollectionsAsync(cancel: cancel);
    }

    /// <inheritdoc/>
    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancel = default)
    {
        if (!await this._qdrantClient.DoesCollectionExistAsync(collectionName, cancel: cancel))
        {
            await this._qdrantClient.DeleteCollectionAsync(collectionName, cancel: cancel);
        }
    }

    /// <inheritdoc/>
    public async Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancel = default)
    {
        var vectorData = await this.ConvertFromMemoryRecordAsync(collectionName, record, cancel);

        if (vectorData == null)
        {
            throw new QdrantMemoryException(QdrantMemoryException.ErrorCodes.FailedToConvertMemoryRecordToQdrantVectorRecord,
                $"Failed to convert MemoryRecord to QdrantVectorRecord");
        }

        try
        {
            await this._qdrantClient.UpsertVectorsAsync(
                collectionName,
                new[] { vectorData },
                cancel: cancel);
        }
        catch (HttpRequestException ex)
        {
            throw new QdrantMemoryException(
                QdrantMemoryException.ErrorCodes.FailedToUpsertVectors,
                $"Failed to upsert due to HttpRequestException: {ex.Message}",
                ex);
        }

        return vectorData.PointId;
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> records,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        var tasks = Task.WhenAll(records.Select(async r => await this.ConvertFromMemoryRecordAsync(collectionName, r, cancel)));
        var vectorData = await tasks;

        try
        {
            await this._qdrantClient.UpsertVectorsAsync(
                collectionName,
                vectorData,
                cancel: cancel);
        }
        catch (HttpRequestException ex)
        {
            throw new QdrantMemoryException(
                QdrantMemoryException.ErrorCodes.FailedToUpsertVectors,
                $"Failed to upsert due to HttpRequestException: {ex.Message}",
                ex);
        }

        foreach (var v in vectorData)
        {
            yield return v.PointId;
        }
    }

    /// <inheritdoc/>
    public async Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancel = default)
    {
        try
        {
            var vectorData = await this._qdrantClient.GetVectorByPayloadIdAsync(collectionName, key, withEmbedding, cancel: cancel);
            if (vectorData != null)
            {
                return MemoryRecord.FromJsonMetadata(
                    json: vectorData.GetSerializedPayload(),
                    embedding: new Embedding<float>(vectorData.Embedding),
                    key: vectorData.PointId);
            }
            else
            {
                return null;
            }
        }
        catch (HttpRequestException ex)
        {
            throw new QdrantMemoryException(
                QdrantMemoryException.ErrorCodes.FailedToGetVectorData,
                $"Failed to get vector data from Qdrant: {ex.Message}",
                ex);
        }
        catch (MemoryException ex)
        {
            throw new QdrantMemoryException(
                QdrantMemoryException.ErrorCodes.FailedToConvertQdrantVectorRecordToMemoryRecord,
                $"Failed deserialize Qdrant response to Memory Record: {ex.Message}",
                ex);
        }
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys, bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        foreach (var key in keys)
        {
            MemoryRecord? record = await this.GetAsync(collectionName, key, withEmbeddings, cancel);
            if (record != null)
            {
                yield return record;
            }
        }
    }

    /// <summary>
    /// Get a MemoryRecord from the Qdrant Vector database by pointId.
    /// </summary>
    /// <param name="collectionName">The name associated with a collection of embeddings.</param>
    /// <param name="pointId">The unique indexed ID associated with the Qdrant vector record to get.</param>
    /// <param name="withEmbedding">If true, the embedding will be returned in the memory record.</param>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns></returns>
    /// <exception cref="QdrantMemoryException"></exception>
    public async Task<MemoryRecord?> GetWithPointIdAsync(string collectionName, string pointId, bool withEmbedding = false, CancellationToken cancel = default)
    {
        try
        {
            var vectorDataList = this._qdrantClient
                .GetVectorsByIdAsync(collectionName, new[] { pointId }, withEmbedding, cancel: cancel);

            var vectorData = await vectorDataList.FirstOrDefaultAsync(cancel);

            if (vectorData != null)
            {
                return MemoryRecord.FromJsonMetadata(
                    json: vectorData.GetSerializedPayload(),
                    embedding: new Embedding<float>(vectorData.Embedding));
            }
            else
            {
                return null;
            }
        }
        catch (HttpRequestException ex)
        {
            throw new QdrantMemoryException(
                QdrantMemoryException.ErrorCodes.FailedToGetVectorData,
                $"Failed to get vector data from Qdrant: {ex.Message}",
                ex);
        }
        catch (MemoryException ex)
        {
            throw new QdrantMemoryException(
                QdrantMemoryException.ErrorCodes.FailedToConvertQdrantVectorRecordToMemoryRecord,
                $"Failed deserialize Qdrant response to Memory Record: {ex.Message}",
                ex);
        }
    }

    /// <summary>
    /// Get a MemoryRecord from the Qdrant Vector database by a group of pointIds.
    /// </summary>
    /// <param name="collectionName">The name associated with a collection of embeddings.</param>
    /// <param name="pointIds">The unique indexed IDs associated with Qdrant vector records to get.</param>
    /// <param name="withEmbeddings">If true, the embeddings will be returned in the memory records.</param>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns></returns>
    public async IAsyncEnumerable<MemoryRecord> GetWithPointIdBatchAsync(string collectionName, IEnumerable<string> pointIds, bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        var vectorDataList = this._qdrantClient
            .GetVectorsByIdAsync(collectionName, pointIds, withEmbeddings, cancel: cancel);

        await foreach (var vectorData in vectorDataList)
        {
            yield return MemoryRecord.FromJsonMetadata(
                json: vectorData.GetSerializedPayload(),
                embedding: new Embedding<float>(vectorData.Embedding),
                key: vectorData.PointId);
        }
    }

    /// <inheritdoc />
    public async Task RemoveAsync(string collectionName, string key, CancellationToken cancel = default)
    {
        try
        {
            await this._qdrantClient.DeleteVectorByPayloadIdAsync(collectionName, key, cancel: cancel);
        }
        catch (HttpRequestException ex)
        {
            throw new QdrantMemoryException(
                QdrantMemoryException.ErrorCodes.FailedToRemoveVectorData,
                $"Failed to remove vector data from Qdrant {ex.Message}",
                ex);
        }
    }

    /// <inheritdoc />
    public async Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancel = default)
    {
        await Task.WhenAll(keys.Select(async k => await this.RemoveAsync(collectionName, k, cancel)));
    }

    /// <summary>
    /// Remove a MemoryRecord from the Qdrant Vector database by pointId.
    /// </summary>
    /// <param name="collectionName">The name associated with a collection of embeddings.</param>
    /// <param name="pointId">The unique indexed ID associated with the Qdrant vector record to remove.</param>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns></returns>
    /// <exception cref="QdrantMemoryException"></exception>
    public async Task RemoveWithPointIdAsync(string collectionName, string pointId, CancellationToken cancel = default)
    {
        try
        {
            await this._qdrantClient.DeleteVectorsByIdAsync(collectionName, new[] { pointId }, cancel: cancel);
        }
        catch (HttpRequestException ex)
        {
            throw new QdrantMemoryException(
                QdrantMemoryException.ErrorCodes.FailedToRemoveVectorData,
                $"Failed to remove vector data from Qdrant {ex.Message}",
                ex);
        }
    }

    /// <summary>
    /// Remove a MemoryRecord from the Qdrant Vector database by a group of pointIds.
    /// </summary>
    /// <param name="collectionName">The name associated with a collection of embeddings.</param>
    /// <param name="pointIds">The unique indexed IDs associated with the Qdrant vector records to remove.</param>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns></returns>
    /// <exception cref="QdrantMemoryException"></exception>
    public async Task RemoveWithPointIdBatchAsync(string collectionName, IEnumerable<string> pointIds, CancellationToken cancel = default)
    {
        try
        {
            await this._qdrantClient.DeleteVectorsByIdAsync(collectionName, pointIds, cancel: cancel);
        }
        catch (HttpRequestException ex)
        {
            throw new QdrantMemoryException(
                QdrantMemoryException.ErrorCodes.FailedToRemoveVectorData,
                $"Error in batch removing data from Qdrant {ex.Message}",
                ex);
        }
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(
        string collectionName,
        Embedding<float> embedding,
        int limit,
        double minRelevanceScore = 0,
        bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        var results = this._qdrantClient.FindNearestInCollectionAsync(
            collectionName: collectionName,
            target: embedding.Vector,
            threshold: minRelevanceScore,
            top: limit,
            withVectors: withEmbeddings,
            cancel: cancel);

        await foreach ((QdrantVectorRecord, double) result in results)
        {
            yield return (
                MemoryRecord.FromJsonMetadata(
                    json: result.Item1.GetSerializedPayload(),
                    embedding: new Embedding<float>(result.Item1.Embedding)),
                result.Item2);
        }
    }

    /// <inheritdoc/>
    public async Task<(MemoryRecord, double)?> GetNearestMatchAsync(
        string collectionName,
        Embedding<float> embedding,
        double minRelevanceScore = 0,
        bool withEmbedding = false,
        CancellationToken cancel = default)
    {
        var results = this.GetNearestMatchesAsync(
            collectionName: collectionName,
            embedding: embedding,
            minRelevanceScore: minRelevanceScore,
            limit: 1,
            withEmbeddings: withEmbedding,
            cancel: cancel);

        var record = await results.FirstOrDefaultAsync(cancellationToken: cancel);

        return (record.Item1, record.Item2);
    }

    #region private ================================================================================

    private readonly IQdrantVectorDbClient _qdrantClient;

    private async Task<QdrantVectorRecord> ConvertFromMemoryRecordAsync(string collectionName, MemoryRecord record, CancellationToken cancel = default)
    {
        string pointId;

        // Check if a database key has been provided for update
        if (!string.IsNullOrEmpty(record.Key))
        {
            pointId = record.Key;
        }
        // Check if the data store contains a record with the provided metadata ID
        else
        {
            var existingRecord = await this._qdrantClient.GetVectorByPayloadIdAsync(collectionName, record.Metadata.Id, cancel: cancel);

            if (existingRecord != null)
            {
                pointId = existingRecord.PointId;
            }
            else
            {
                do // Generate a new ID until a unique one is found (more than one pass should be exceedingly rare)
                {
                    // If no matching record can be found, generate an ID for the new record
                    pointId = Guid.NewGuid().ToString();
                    existingRecord = await this._qdrantClient.GetVectorsByIdAsync(collectionName, new[] { pointId }, cancel: cancel)
                        .FirstOrDefaultAsync(cancel);
                } while (existingRecord != null);
            }
        }

        var vectorData = QdrantVectorRecord.FromJsonMetadata(
            pointId: pointId,
            embedding: record.Embedding.Vector,
            json: record.GetSerializedMetadata());

        if (vectorData == null)
        {
            throw new QdrantMemoryException(QdrantMemoryException.ErrorCodes.FailedToConvertMemoryRecordToQdrantVectorRecord,
                $"Failed to convert MemoryRecord to QdrantVectorRecord");
        }

        return vectorData;
    }

    #endregion
}
