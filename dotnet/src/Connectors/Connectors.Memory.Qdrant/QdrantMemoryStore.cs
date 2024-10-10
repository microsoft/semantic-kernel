// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
using System.Net;
>>>>>>> Stashed changes
=======
using System.Net;
>>>>>>> Stashed changes
=======
using System.Net;
>>>>>>> Stashed changes
=======
using System.Net;
>>>>>>> Stashed changes
=======
using System.Net;
>>>>>>> Stashed changes
=======
using System.Net;
>>>>>>> origin/main
=======
using System.Net;
>>>>>>> Stashed changes
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
using Microsoft.Extensions.Logging.Abstractions;
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
using Microsoft.Extensions.Logging.Abstractions;
<<<<<<< main
=======
=======
<<<<<<< Updated upstream
=======
<<<<<<< main
using Microsoft.Extensions.Logging.Abstractions;
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Diagnostics;
<<<<<<< main
>>>>>>> ms/feature-error-handling
=======
>>>>>>> ms/feature-error-handling-part3
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// An implementation of <see cref="IMemoryStore"/> for Qdrant Vector Database.
/// </summary>
/// <remarks>The Embedding data is saved to a Qdrant Vector Database instance specified in the constructor by url and port.
/// The embedding data persists between subsequent instances and has similarity search capability.
/// </remarks>
public class QdrantMemoryStore : IMemoryStore
{
    /// <summary>
    /// The Qdrant Vector Database memory store logger.
    /// </summary>
    private readonly ILogger _logger;

    /// <summary>
    /// Initializes a new instance of the <see cref="QdrantMemoryStore"/> class.
    /// </summary>
    /// <param name="endpoint">The Qdrant Vector Database endpoint.</param>
    /// <param name="vectorSize">The size of the vectors used.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public QdrantMemoryStore(string endpoint, int vectorSize, ILoggerFactory? loggerFactory = null)
    {
        this._qdrantClient = new QdrantVectorDbClient(endpoint, vectorSize, loggerFactory);
        this._logger = loggerFactory?.CreateLogger(typeof(QdrantMemoryStore)) ?? NullLogger.Instance;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="QdrantMemoryStore"/> class.
    /// </summary>
    /// <param name="httpClient">The <see cref="HttpClient"/> instance used for making HTTP requests.</param>
    /// <param name="vectorSize">The size of the vectors used in the Qdrant Vector Database.</param>
    /// <param name="endpoint">The optional endpoint URL for the Qdrant Vector Database. If not specified, the base address of the HTTP client is used.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public QdrantMemoryStore(HttpClient httpClient, int vectorSize, string? endpoint = null, ILoggerFactory? loggerFactory = null)
    {
        this._qdrantClient = new QdrantVectorDbClient(httpClient, vectorSize, endpoint, loggerFactory);
        this._logger = loggerFactory?.CreateLogger(typeof(QdrantMemoryStore)) ?? NullLogger.Instance;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="QdrantMemoryStore"/> class.
    /// </summary>
    /// <param name="client">The Qdrant Db client for interacting with Qdrant Vector Database.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public QdrantMemoryStore(IQdrantVectorDbClient client, ILoggerFactory? loggerFactory = null)
    {
        this._qdrantClient = client;
        this._logger = loggerFactory?.CreateLogger(typeof(QdrantMemoryStore)) ?? NullLogger.Instance;
    }

    /// <inheritdoc/>
    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        if (!await this._qdrantClient.DoesCollectionExistAsync(collectionName, cancellationToken).ConfigureAwait(false))
        {
            await this._qdrantClient.CreateCollectionAsync(collectionName, cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    public async Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        return await this._qdrantClient.DoesCollectionExistAsync(collectionName, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<string> GetCollectionsAsync(CancellationToken cancellationToken = default)
    {
        return this._qdrantClient.ListCollectionsAsync(cancellationToken);
    }

    /// <inheritdoc/>
    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        if (await this._qdrantClient.DoesCollectionExistAsync(collectionName, cancellationToken).ConfigureAwait(false))
        {
            await this._qdrantClient.DeleteCollectionAsync(collectionName, cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    public async Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken = default)
    {
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        var vectorData = await this.ConvertFromMemoryRecordAsync(collectionName, record, cancellationToken).ConfigureAwait(false) ??
            throw new KernelException("Failed to convert memory record to Qdrant vector record");

        try
        {
            await this._qdrantClient.UpsertVectorsAsync(
                collectionName,
                [vectorData],
                cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException ex)
        {
            this._logger.LogError(ex, "Failed to upsert vectors: {Message}", ex.Message);
            throw;
        }
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        var vectorData = await this.ConvertFromMemoryRecordAsync(collectionName, record, cancellationToken).ConfigureAwait(false) ??
            throw new KernelException("Failed to convert memory record to Qdrant vector record");
=======
<<<<<<< Updated upstream
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
<<<<<<< main
        var vectorData = await this.ConvertFromMemoryRecordAsync(collectionName, record, cancellationToken).ConfigureAwait(false) ??
            throw new KernelException("Failed to convert memory record to Qdrant vector record");
=======
        var vectorData = await this.ConvertFromMemoryRecordAsync(collectionName, record, cancellationToken).ConfigureAwait(false);

        if (vectorData == null)
        {
            throw new SKException("Failed to convert memory record to Qdrant vector record");
        }
>>>>>>> ms/feature-error-handling
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main

        await this._qdrantClient.UpsertVectorsAsync(
                collectionName,
                [vectorData],
                cancellationToken).ConfigureAwait(false);
<<<<<<< main
        }
        catch (HttpOperationException ex)
        {
<<<<<<< main
            this._logger.LogError(ex, "Failed to upsert vectors: {Message}", ex.Message);
            throw;
=======
            throw new SKException("Failed to upsert vectors", ex);
>>>>>>> ms/feature-error-handling-part3
        }
=======
>>>>>>> ms/feature-error-handling
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes

        return vectorData.PointId;
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> records,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var tasks = Task.WhenAll(records.Select(async r => await this.ConvertFromMemoryRecordAsync(collectionName, r, cancellationToken).ConfigureAwait(false)));
        var vectorData = await tasks.ConfigureAwait(false);

<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        try
        {
            await this._qdrantClient.UpsertVectorsAsync(
=======
        await this._qdrantClient.UpsertVectorsAsync(
>>>>>>> origin/main
                collectionName,
                vectorData,
                cancellationToken).ConfigureAwait(false);
<<<<<<< main
        }
        catch (HttpOperationException ex)
        {
<<<<<<< main
            this._logger.LogError(ex, "Failed to upsert vectors: {Message}", ex.Message);
            throw;
=======
            throw new SKException("Failed to upsert vectors", ex);
>>>>>>> ms/feature-error-handling-part3
        }
=======
<<<<<<< head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        await this._qdrantClient.UpsertVectorsAsync(
                collectionName,
                vectorData,
                cancellationToken).ConfigureAwait(false);
<<<<<<< main
        }
        catch (HttpOperationException ex)
        {
<<<<<<< main
            this._logger.LogError(ex, "Failed to upsert vectors: {Message}", ex.Message);
            throw;
=======
            throw new SKException("Failed to upsert vectors", ex);
>>>>>>> ms/feature-error-handling-part3
        }
=======

>>>>>>> ms/feature-error-handling
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======

>>>>>>> ms/feature-error-handling
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
        foreach (var v in vectorData)
        {
            yield return v.PointId;
        }
    }

    /// <inheritdoc/>
    public async Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancellationToken = default)
    {
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
=======
<<<<<<< main
>>>>>>> Stashed changes
        try
        {
            var vectorData = await this._qdrantClient.GetVectorByPayloadIdAsync(collectionName, key, withEmbedding, cancellationToken).ConfigureAwait(false);
            if (vectorData is null) { return null; }

            return MemoryRecord.FromJsonMetadata(
                json: vectorData.GetSerializedPayload(),
                embedding: vectorData.Embedding,
                key: vectorData.PointId);
        }
        catch (HttpOperationException ex)
        {
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> origin/main
            this._logger.LogError(ex, "Failed to get vector data: {Message}", ex.Message);
            throw;
=======
            throw new SKException("Failed to get vector data", ex);
>>>>>>> ms/feature-error-handling-part3
        }
=======
<<<<<<< head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
            this._logger.LogError(ex, "Failed to get vector data: {Message}", ex.Message);
            throw;
=======
            throw new SKException("Failed to get vector data", ex);
>>>>>>> ms/feature-error-handling-part3
        }
=======
<<<<<<< Updated upstream
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
        var vectorData = await this._qdrantClient.GetVectorByPayloadIdAsync(collectionName, key, withEmbedding, cancellationToken).ConfigureAwait(false);
        if (vectorData == null) { return null; }

        return MemoryRecord.FromJsonMetadata(
            json: vectorData.GetSerializedPayload(),
            embedding: new Embedding<float>(vectorData.Embedding, transferOwnership: true),
            key: vectorData.PointId);
>>>>>>> ms/feature-error-handling
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys, bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        foreach (var key in keys)
        {
            MemoryRecord? record = await this.GetAsync(collectionName, key, withEmbeddings, cancellationToken).ConfigureAwait(false);
            if (record is not null)
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
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Memory record</returns>
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    /// <exception cref="KernelException"></exception>
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
<<<<<<< main
    /// <exception cref="KernelException"></exception>
=======
    /// <exception cref="SKException"></exception>
>>>>>>> ms/feature-error-handling-part3
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
<<<<<<< main
    /// <exception cref="KernelException"></exception>
=======
    /// <exception cref="SKException"></exception>
>>>>>>> ms/feature-error-handling-part3
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
    public async Task<MemoryRecord?> GetWithPointIdAsync(string collectionName, string pointId, bool withEmbedding = false,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var vectorDataList = this._qdrantClient
                .GetVectorsByIdAsync(collectionName, [pointId], withEmbedding, cancellationToken);
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
    /// <exception cref="SKException"></exception>
    public async Task<MemoryRecord?> GetWithPointIdAsync(string collectionName, string pointId, bool withEmbedding = false,
        CancellationToken cancellationToken = default)
    {
        var vectorDataList = this._qdrantClient
                .GetVectorsByIdAsync(collectionName, new[] { pointId }, withEmbedding, cancellationToken);
>>>>>>> ms/feature-error-handling
>>>>>>> origin/main

        var vectorData = await vectorDataList.FirstOrDefaultAsync(cancellationToken).ConfigureAwait(false);

<<<<<<< head
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
    /// <exception cref="SKException"></exception>
    public async Task<MemoryRecord?> GetWithPointIdAsync(string collectionName, string pointId, bool withEmbedding = false,
        CancellationToken cancellationToken = default)
    {
        var vectorDataList = this._qdrantClient
                .GetVectorsByIdAsync(collectionName, new[] { pointId }, withEmbedding, cancellationToken);
>>>>>>> ms/feature-error-handling
>>>>>>> origin/main

        var vectorData = await vectorDataList.FirstOrDefaultAsync(cancellationToken).ConfigureAwait(false);

<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
            if (vectorData is null) { return null; }

            return MemoryRecord.FromJsonMetadata(
                json: vectorData.GetSerializedPayload(),
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
=======
<<<<<<< main
>>>>>>> Stashed changes
                embedding: vectorData.Embedding);
        }
        catch (HttpOperationException ex)
        {
            this._logger.LogError(ex, "Failed to get vector data: {Message}", ex.Message);
            throw;
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        }
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
                embedding: new Embedding<float>(vectorData.Embedding, transferOwnership: true));
        }
        catch (HttpRequestException ex)
        {
            throw new SKException("Failed to get vector data", ex);
>>>>>>> ms/feature-error-handling-part3
        }
=======
=======
=======
>>>>>>> Stashed changes
=======
                embedding: new Embedding<float>(vectorData.Embedding, transferOwnership: true));
        }
        catch (HttpRequestException ex)
        {
            throw new SKException("Failed to get vector data", ex);
>>>>>>> ms/feature-error-handling-part3
        }
=======
<<<<<<< Updated upstream
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
        if (vectorData == null) { return null; }

        return MemoryRecord.FromJsonMetadata(
            json: vectorData.GetSerializedPayload(),
            embedding: new Embedding<float>(vectorData.Embedding, transferOwnership: true));
>>>>>>> ms/feature-error-handling
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
    }

    /// <summary>
    /// Get memory records from the Qdrant Vector database using a group of pointIds.
    /// </summary>
    /// <param name="collectionName">The name associated with a collection of embeddings.</param>
    /// <param name="pointIds">The unique indexed IDs associated with Qdrant vector records to get.</param>
    /// <param name="withEmbeddings">If true, the embeddings will be returned in the memory records.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Memory records</returns>
    public async IAsyncEnumerable<MemoryRecord> GetWithPointIdBatchAsync(
        string collectionName,
        IEnumerable<string> pointIds,
        bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var vectorDataList = this._qdrantClient
            .GetVectorsByIdAsync(collectionName, pointIds, withEmbeddings, cancellationToken);

        await foreach (var vectorData in vectorDataList.ConfigureAwait(false))
        {
            yield return MemoryRecord.FromJsonMetadata(
                json: vectorData.GetSerializedPayload(),
                embedding: vectorData.Embedding,
                key: vectorData.PointId);
        }
    }

    /// <inheritdoc />
    public async Task RemoveAsync(string collectionName, string key, CancellationToken cancellationToken = default)
    {
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
=======
<<<<<<< main
>>>>>>> Stashed changes
        try
        {
            await this._qdrantClient.DeleteVectorByPayloadIdAsync(collectionName, key, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException ex)
        {
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> origin/main
=======
<<<<<<< main
>>>>>>> Stashed changes
            this._logger.LogError(ex, "Failed to remove vector data: {Message}", ex.Message);
            throw;
=======
            throw new SKException("Failed to remove vector data", ex);
>>>>>>> ms/feature-error-handling-part3
        }
=======
<<<<<<< Updated upstream
<<<<<<< head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
            this._logger.LogError(ex, "Failed to remove vector data: {Message}", ex.Message);
            throw;
=======
            throw new SKException("Failed to remove vector data", ex);
>>>>>>> ms/feature-error-handling-part3
        }
=======
        await this._qdrantClient.DeleteVectorByPayloadIdAsync(collectionName, key, cancellationToken).ConfigureAwait(false);
>>>>>>> ms/feature-error-handling
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        await this._qdrantClient.DeleteVectorByPayloadIdAsync(collectionName, key, cancellationToken).ConfigureAwait(false);
>>>>>>> ms/feature-error-handling
>>>>>>> origin/main
=======
        await this._qdrantClient.DeleteVectorByPayloadIdAsync(collectionName, key, cancellationToken).ConfigureAwait(false);
>>>>>>> ms/feature-error-handling
>>>>>>> Stashed changes
    }

    /// <inheritdoc />
    public async Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(keys.Select(async k => await this.RemoveAsync(collectionName, k, cancellationToken).ConfigureAwait(false))).ConfigureAwait(false);
    }

    /// <summary>
    /// Remove a MemoryRecord from the Qdrant Vector database by pointId.
    /// </summary>
    /// <param name="collectionName">The name associated with a collection of embeddings.</param>
    /// <param name="pointId">The unique indexed ID associated with the Qdrant vector record to remove.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    /// <exception cref="KernelException"></exception>
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
<<<<<<< main
<<<<<<< main
    /// <exception cref="KernelException"></exception>
=======
    /// <exception cref="SKException"></exception>
>>>>>>> ms/feature-error-handling-part3
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
    public async Task RemoveWithPointIdAsync(string collectionName, string pointId, CancellationToken cancellationToken = default)
    {
        try
        {
            await this._qdrantClient.DeleteVectorsByIdAsync(collectionName, [pointId], cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException ex)
        {
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> origin/main
=======
<<<<<<< main
>>>>>>> Stashed changes
            this._logger.LogError(ex, "Failed to remove vector data: {Message}", ex.Message);
            throw;
=======
            throw new SKException("Failed to remove vector data", ex);
>>>>>>> ms/feature-error-handling-part3
        }
=======
<<<<<<< Updated upstream
<<<<<<< head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
            this._logger.LogError(ex, "Failed to remove vector data: {Message}", ex.Message);
            throw;
=======
            throw new SKException("Failed to remove vector data", ex);
>>>>>>> ms/feature-error-handling-part3
        }
=======
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
    /// <exception cref="SKException"></exception>
    public async Task RemoveWithPointIdAsync(string collectionName, string pointId, CancellationToken cancellationToken = default)
    {
        await this._qdrantClient.DeleteVectorsByIdAsync(collectionName, new[] { pointId }, cancellationToken).ConfigureAwait(false);
>>>>>>> ms/feature-error-handling
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
    }

    /// <summary>
    /// Remove a MemoryRecord from the Qdrant Vector database by a group of pointIds.
    /// </summary>
    /// <param name="collectionName">The name associated with a collection of embeddings.</param>
    /// <param name="pointIds">The unique indexed IDs associated with the Qdrant vector records to remove.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    /// <exception cref="KernelException"></exception>
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
<<<<<<< main
<<<<<<< main
    /// <exception cref="KernelException"></exception>
=======
    /// <exception cref="SKException"></exception>
>>>>>>> ms/feature-error-handling-part3
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
    public async Task RemoveWithPointIdBatchAsync(string collectionName, IEnumerable<string> pointIds, CancellationToken cancellationToken = default)
    {
        try
        {
            await this._qdrantClient.DeleteVectorsByIdAsync(collectionName, pointIds, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException ex)
        {
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            this._logger.LogError(ex, "Failed to remove vector data: {Message}", ex.Message);
            throw;
        }
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
<<<<<<< main
            this._logger.LogError(ex, "Failed to remove vector data: {Message}", ex.Message);
            throw;
=======
            throw new SKException("Failed to remove vector data", ex);
>>>>>>> ms/feature-error-handling-part3
        }
=======
    /// <exception cref="SKException"></exception>
    public async Task RemoveWithPointIdBatchAsync(string collectionName, IEnumerable<string> pointIds, CancellationToken cancellationToken = default)
    {
        await this._qdrantClient.DeleteVectorsByIdAsync(collectionName, pointIds, cancellationToken).ConfigureAwait(false);
>>>>>>> ms/feature-error-handling
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(
        string collectionName,
        ReadOnlyMemory<float> embedding,
        int limit,
        double minRelevanceScore = 0,
        bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        IAsyncEnumerator<(QdrantVectorRecord, double)> enumerator = this._qdrantClient
            .FindNearestInCollectionAsync(
                collectionName: collectionName,
                target: embedding,
                threshold: minRelevanceScore,
                top: limit,
                withVectors: withEmbeddings,
                cancellationToken: cancellationToken)
            .GetAsyncEnumerator(cancellationToken);

        // Workaround for https://github.com/dotnet/csharplang/issues/2949: Yielding in catch blocks not supported in async iterators
        (QdrantVectorRecord, double)? result = null;
        bool hasResult = true;
        do
        {
            try
            {
                hasResult = await enumerator.MoveNextAsync().ConfigureAwait(false);
                if (hasResult)
                {
                    result = enumerator.Current;
                }
                else
                {
                    result = null;
                }
            }
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            catch (HttpOperationException ex) when (ex.StatusCode == System.Net.HttpStatusCode.NotFound)
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
<<<<<<< main
            catch (HttpOperationException ex) when (ex.StatusCode == System.Net.HttpStatusCode.NotFound)
=======
            catch (HttpOperationException ex) when (ex.StatusCode == HttpStatusCode.NotFound)
>>>>>>> ms/feature-error-handling
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
            {
                this._logger.LogWarning("NotFound when calling {QdrantMemoryStore}::FindNearestInCollectionAsync - the collection '{Name}' may not exist yet",
                    nameof(QdrantMemoryStore), collectionName);
                hasResult = false;
            }

            if (result is not null)
            {
                yield return (
                    MemoryRecord.FromJsonMetadata(
                        json: result.Value.Item1.GetSerializedPayload(),
                        embedding: result.Value.Item1.Embedding),
                    result.Value.Item2);
            }
        } while (hasResult);
    }

    /// <inheritdoc/>
    public async Task<(MemoryRecord, double)?> GetNearestMatchAsync(
        string collectionName,
        ReadOnlyMemory<float> embedding,
        double minRelevanceScore = 0,
        bool withEmbedding = false,
        CancellationToken cancellationToken = default)
    {
        var results = this.GetNearestMatchesAsync(
            collectionName: collectionName,
            embedding: embedding,
            minRelevanceScore: minRelevanceScore,
            limit: 1,
            withEmbeddings: withEmbedding,
            cancellationToken: cancellationToken);

        var record = await results.FirstOrDefaultAsync(cancellationToken).ConfigureAwait(false);

        return (record.Item1, record.Item2);
    }

    #region private ================================================================================

    private readonly IQdrantVectorDbClient _qdrantClient;

    private async Task<QdrantVectorRecord> ConvertFromMemoryRecordAsync(
        string collectionName,
        MemoryRecord record,
        CancellationToken cancellationToken = default)
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
            var existingRecord = await this._qdrantClient.GetVectorByPayloadIdAsync(
                    collectionName,
                    record.Metadata.Id,
                    cancellationToken: cancellationToken)
                .ConfigureAwait(false);

            if (existingRecord is not null)
            {
                pointId = existingRecord.PointId;
            }
            else
            {
                do // Generate a new ID until a unique one is found (more than one pass should be exceedingly rare)
                {
                    // If no matching record can be found, generate an ID for the new record
                    pointId = Guid.NewGuid().ToString();
                    existingRecord = await this._qdrantClient.GetVectorsByIdAsync(collectionName, [pointId], cancellationToken: cancellationToken)
                        .FirstOrDefaultAsync(cancellationToken).ConfigureAwait(false);
                } while (existingRecord is not null);
            }
        }

        return QdrantVectorRecord.FromJsonMetadata(
            pointId: pointId,
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> origin/main
            embedding: record.Embedding,
            json: record.GetSerializedMetadata()) ??
            throw new KernelException("Failed to convert memory record to Qdrant vector record");
=======
<<<<<<< head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
            embedding: record.Embedding,
            json: record.GetSerializedMetadata()) ??
            throw new KernelException("Failed to convert memory record to Qdrant vector record");
<<<<<<< main
=======
=======
<<<<<<< Updated upstream
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
            embedding: record.Embedding.Vector,
            json: record.GetSerializedMetadata());

        if (vectorData == null)
        {
            throw new SKException("Failed to convert memory record to Qdrant vector record");
        }

        return vectorData;
>>>>>>> ms/feature-error-handling
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
    }

    #endregion
}
