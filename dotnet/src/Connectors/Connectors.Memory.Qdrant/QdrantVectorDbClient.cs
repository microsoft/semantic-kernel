// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
using Microsoft.SemanticKernel.Http;
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
<<<<<<< main
>>>>>>> origin/main
using Microsoft.SemanticKernel.Http;
=======
<<<<<<< Updated upstream
=======
<<<<<<< main
using Microsoft.SemanticKernel.Http;
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
using Microsoft.SemanticKernel.Connectors.Memory.Qdrant.Http.ApiSchema;
using Microsoft.SemanticKernel.Diagnostics;
using Verify = Microsoft.SemanticKernel.Connectors.Memory.Qdrant.Diagnostics.Verify;
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

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// An implementation of a client for the Qdrant Vector Database. This class is used to
/// connect, create, delete, and get embeddings data from a Qdrant Vector Database instance.
/// </summary>
#pragma warning disable CA1001 // Types that own disposable fields should be disposable. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
public sealed class QdrantVectorDbClient : IQdrantVectorDbClient
#pragma warning restore CA1001 // Types that own disposable fields should be disposable. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
{
    /// <summary>
    /// Initializes a new instance of the <see cref="QdrantVectorDbClient"/> class.
    /// </summary>
    /// <param name="endpoint">The Qdrant Vector Database endpoint.</param>
    /// <param name="vectorSize">The size of the vectors used in the Qdrant Vector Database.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public QdrantVectorDbClient(
        string endpoint,
        int vectorSize,
        ILoggerFactory? loggerFactory = null)
    {
        this._vectorSize = vectorSize;
        this._httpClient = HttpClientProvider.GetHttpClient();
        this._httpClient.BaseAddress = SanitizeEndpoint(endpoint);
        this._logger = loggerFactory?.CreateLogger(typeof(QdrantVectorDbClient)) ?? NullLogger.Instance;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="QdrantVectorDbClient"/> class.
    /// </summary>
    /// <param name="httpClient">The <see cref="HttpClient"/> instance used for making HTTP requests.</param>
    /// <param name="vectorSize">The size of the vectors used in the Qdrant Vector Database.</param>
    /// <param name="endpoint">The optional endpoint URL for the Qdrant Vector Database. If not specified, the base address of the HTTP client is used.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public QdrantVectorDbClient(
        HttpClient httpClient,
        int vectorSize,
        string? endpoint = null,
        ILoggerFactory? loggerFactory = null)
    {
        if (string.IsNullOrEmpty(httpClient.BaseAddress?.AbsoluteUri) && string.IsNullOrEmpty(endpoint))
        {
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            throw new ArgumentException($"The {nameof(httpClient)}.{nameof(HttpClient.BaseAddress)} and {nameof(endpoint)} are both null or empty. Please ensure at least one is provided.");
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
            throw new ArgumentException($"The {nameof(httpClient)}.{nameof(HttpClient.BaseAddress)} and {nameof(endpoint)} are both null or empty. Please ensure at least one is provided.");
=======
            throw new ArgumentException("The HttpClient BaseAddress and endpoint are both null or empty. Please ensure at least one is provided.");
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
=======
>>>>>>> Stashed changes
<<<<<<< main
            throw new ArgumentException($"The {nameof(httpClient)}.{nameof(HttpClient.BaseAddress)} and {nameof(endpoint)} are both null or empty. Please ensure at least one is provided.");
=======
            throw new ArgumentException("The HttpClient BaseAddress and endpoint are both null or empty. Please ensure at least one is provided.");
>>>>>>> ms/feature-error-handling
<<<<<<< Updated upstream
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
        }

        this._httpClient = httpClient;
        this._vectorSize = vectorSize;
        this._endpointOverride = string.IsNullOrEmpty(endpoint) ? null : SanitizeEndpoint(endpoint!);
        this._logger = loggerFactory?.CreateLogger(typeof(QdrantVectorDbClient)) ?? NullLogger.Instance;
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<QdrantVectorRecord> GetVectorsByIdAsync(string collectionName, IEnumerable<string> pointIds, bool withVectors = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Searching vectors by point ID");

        using HttpRequestMessage request = GetVectorsRequest.Create(collectionName)
            .WithPointIDs(pointIds)
            .WithPayloads(true)
            .WithVectors(withVectors)
            .Build();

        string? responseContent = null;

        try
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
            (_, responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Vectors not found {Message}", e.Message);
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
            response.EnsureSuccess(responseContent, this._logger);
        }
        catch (HttpOperationException e)
        {
            this._logger.LogDebug("Vectors not found {0}", e.Message);
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
            throw;
        }

        var data = JsonSerializer.Deserialize<GetVectorsResponse>(responseContent);

        if (data is null)
        {
            this._logger.LogWarning("Unable to deserialize Get response");
            yield break;
        }

        if (!data.Result.Any())
        {
            this._logger.LogWarning("Vectors not found");
            yield break;
        }

        var records = data.Result;

#pragma warning disable CS8604 // The request specifically asked for a payload to be in the response
        foreach (var record in records)
        {
            yield return new QdrantVectorRecord(
                pointId: record.Id,
                embedding: record.Vector ?? default,
                record.Payload,
                tags: null);
        }
#pragma warning restore CS8604
    }

    /// <inheritdoc/>
    public async Task<QdrantVectorRecord?> GetVectorByPayloadIdAsync(string collectionName, string metadataId, bool withVector = false, CancellationToken cancellationToken = default)
    {
        using HttpRequestMessage request = SearchVectorsRequest.Create(collectionName)
            .SimilarTo(new float[this._vectorSize])
            .HavingExternalId(metadataId)
            .IncludePayLoad()
            .TakeFirst()
            .IncludeVectorData(withVector)
            .Build();

        string? responseContent = null;

        try
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
            (_, responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException e) when (e.StatusCode == HttpStatusCode.NotFound)
        {
            return null;
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
            response.EnsureSuccess(responseContent, this._logger);
        }
        catch (HttpOperationException e)
        {
            this._logger.LogDebug("Request for vector with payload ID failed {0}", e.Message);
            throw;
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
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Request for vector with payload ID failed {Message}", e.Message);
            throw;
        }

        var data = JsonSerializer.Deserialize<SearchVectorsResponse>(responseContent);

        if (data is null)
        {
            this._logger.LogWarning("Unable to deserialize Search response");
            return null;
        }

        if (!data.Results.Any())
        {
            this._logger.LogDebug("Vector not found");
            return null;
        }

        var point = data.Results.First();

        var record = new QdrantVectorRecord(
            pointId: point.Id,
            embedding: point.Vector,
            payload: point.Payload,
            tags: null);
        this._logger.LogDebug("Vector found}");

        return record;
    }

    /// <inheritdoc/>
    public async Task DeleteVectorsByIdAsync(string collectionName, IEnumerable<string> pointIds, CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Deleting vector by point ID");

        Verify.NotNullOrWhiteSpace(collectionName);
        Verify.NotNull(pointIds);

        using var request = DeleteVectorsRequest.DeleteFrom(collectionName)
            .DeleteRange(pointIds)
            .Build();

        string? responseContent = null;

        try
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
            (_, responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Vector delete request failed: {Message}", e.Message);
            throw;
        }

        var result = JsonSerializer.Deserialize<DeleteVectorsResponse>(responseContent);
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        if (result?.Status == "ok")
        {
=======
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
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
        if (result?.Status == "ok")
        {
=======
            response.EnsureSuccess(responseContent, this._logger);
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Vector delete request failed: {0}", e.Message);
            throw;
        }

        var result = JsonSerializer.Deserialize<QdrantResponse>(responseContent);
>>>>>>> origin/main
        if (result?.Status == "ok")
        {
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
            this._logger.LogDebug("Vector being deleted");
        }
        else
        {
            this._logger.LogWarning("Vector delete failed");
        }
    }

    /// <inheritdoc/>
    public async Task DeleteVectorByPayloadIdAsync(string collectionName, string metadataId, CancellationToken cancellationToken = default)
    {
        QdrantVectorRecord? existingRecord = await this.GetVectorByPayloadIdAsync(collectionName, metadataId, false, cancellationToken).ConfigureAwait(false);

        if (existingRecord is null)
        {
            this._logger.LogDebug("Vector not found, nothing to delete");
            return;
        }

        this._logger.LogDebug("Vector found, deleting");

        using var request = DeleteVectorsRequest
            .DeleteFrom(collectionName)
            .DeleteVector(existingRecord.PointId)
            .Build();

        string? responseContent = null;

        try
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
            (_, responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Vector delete request failed: {Message}", e.Message);
            throw;
        }

        var result = JsonSerializer.Deserialize<DeleteVectorsResponse>(responseContent);
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
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
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
        if (result?.Status == "ok")
        {
            this._logger.LogDebug("Vector being deleted");
        }
        else
        {
=======
            response.EnsureSuccess(responseContent, this._logger);
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Vector delete request failed: {0}", e.Message);
            throw;
        }

        var result = JsonSerializer.Deserialize<QdrantResponse>(responseContent);
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
>>>>>>> Stashed changes
        if (result?.Status == "ok")
        {
            this._logger.LogDebug("Vector being deleted");
        }
        else
        {
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> ms/feature-error-handling
>>>>>>> Stashed changes
=======
>>>>>>> ms/feature-error-handling
>>>>>>> Stashed changes
=======
>>>>>>> ms/feature-error-handling
>>>>>>> Stashed changes
=======
>>>>>>> ms/feature-error-handling
>>>>>>> Stashed changes
=======
>>>>>>> ms/feature-error-handling
>>>>>>> Stashed changes
=======
>>>>>>> ms/feature-error-handling
>>>>>>> origin/main
=======
>>>>>>> ms/feature-error-handling
>>>>>>> Stashed changes
            this._logger.LogWarning("Vector delete failed");
        }
    }

    /// <inheritdoc/>
    public async Task UpsertVectorsAsync(string collectionName, IEnumerable<QdrantVectorRecord> vectorData, CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Upserting vectors");
        Verify.NotNull(vectorData);
        Verify.NotNullOrWhiteSpace(collectionName);

        using var request = UpsertVectorRequest.Create(collectionName)
            .UpsertRange(vectorData)
            .Build();

        string? responseContent = null;

        try
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
            (_, responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Vector upserts request failed: {Message}", e.Message);
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
            response.EnsureSuccess(responseContent, this._logger);
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Vector upserts request failed: {0}", e.Message);
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
            throw;
        }

        var result = JsonSerializer.Deserialize<UpsertVectorResponse>(responseContent);
        if (result?.Status == "ok")
        {
            this._logger.LogDebug("Vectors upserted");
        }
        else
        {
            this._logger.LogWarning("Vector upserts failed");
        }
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<(QdrantVectorRecord, double)> FindNearestInCollectionAsync(
        string collectionName,
        ReadOnlyMemory<float> target,
        double threshold,
        int top = 1,
        bool withVectors = false,
        IEnumerable<string>? requiredTags = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Searching top {0} nearest vectors", top);

        Verify.NotNull(target, "The given vector is NULL");

        using HttpRequestMessage request = SearchVectorsRequest
            .Create(collectionName)
            .SimilarTo(target)
            .HavingTags(requiredTags)
            .WithScoreThreshold(threshold)
            .IncludePayLoad()
            .IncludeVectorData(withVectors)
            .Take(top)
            .Build();

        string? responseContent = null;

        try
        {
            (_, responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Vectors search failed: {Message}", e.Message);
            throw;
        }
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======

        try
        {
            response.EnsureSuccess(responseContent, this._logger);
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Nearest vectors search failed: {0}", e.Message);
            throw;
        }
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

        var data = JsonSerializer.Deserialize<SearchVectorsResponse>(responseContent);

        if (data is null)
        {
            this._logger.LogWarning("Unable to deserialize Search response");
            yield break;
        }

        if (!data.Results.Any())
        {
            this._logger.LogWarning("Nothing found");
            yield break;
        }

        var result = new List<(QdrantVectorRecord, double)>();

        foreach (var v in data.Results)
        {
            var record = new QdrantVectorRecord(
                pointId: v.Id,
                embedding: v.Vector,
                payload: v.Payload);

            result.Add((record, v.Score ?? 0.0));
        }

        // Qdrant search results are currently sorted by id, alphabetically, sort list in place
        result.Sort((a, b) => b.Item2.CompareTo(a.Item2));
        foreach (var kv in result)
        {
            yield return kv;
        }
    }

    /// <inheritdoc/>
    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Creating collection {0}", collectionName);

        using var request = CreateCollectionRequest
            .Create(collectionName, this._vectorSize, QdrantDistanceType.Cosine)
            .Build();

        try
        {
            await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException e) when (e.StatusCode == HttpStatusCode.BadRequest)
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
            // Creation is idempotent, ignore error (and for now ignore vector size)
            if (e.ResponseContent?.IndexOf("already exists", StringComparison.OrdinalIgnoreCase) >= 0)
            {
                return;
            }

            this._logger.LogError(e, "Collection creation failed: {Message}, {Response}", e.Message, e.ResponseContent);
            throw;
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
            response.EnsureSuccess(responseContent, this._logger);
>>>>>>> ms/feature-error-handling
>>>>>>> Stashed changes
=======
=======
            response.EnsureSuccess(responseContent, this._logger);
>>>>>>> ms/feature-error-handling
>>>>>>> Stashed changes
=======
=======
            response.EnsureSuccess(responseContent, this._logger);
>>>>>>> ms/feature-error-handling
>>>>>>> Stashed changes
=======
=======
            response.EnsureSuccess(responseContent, this._logger);
>>>>>>> ms/feature-error-handling
>>>>>>> Stashed changes
=======
=======
            response.EnsureSuccess(responseContent, this._logger);
>>>>>>> ms/feature-error-handling
>>>>>>> Stashed changes
=======
=======
            response.EnsureSuccess(responseContent, this._logger);
>>>>>>> ms/feature-error-handling
>>>>>>> origin/main
=======
=======
            response.EnsureSuccess(responseContent, this._logger);
>>>>>>> ms/feature-error-handling
>>>>>>> Stashed changes
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Collection creation failed: {Message}, {Response}", e.Message, e.ResponseContent);
            throw;
        }
    }

    /// <inheritdoc/>
    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Deleting collection {0}", collectionName);

        using var request = DeleteCollectionRequest.Create(collectionName).Build();

        try
        {
            await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException e) when (e.StatusCode == HttpStatusCode.NotFound)
        {
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            return; // Deletion is idempotent, ignore error
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
            return; // Deletion is idempotent, ignore error
=======
            response.EnsureSuccess(responseContent, this._logger);
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
<<<<<<< main
            return; // Deletion is idempotent, ignore error
=======
            response.EnsureSuccess(responseContent, this._logger);
>>>>>>> ms/feature-error-handling
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Collection deletion failed: {Message}, {Response}", e.Message, e.ResponseContent);
            throw;
        }
    }

    /// <inheritdoc/>
    public async Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Fetching collection {0}", collectionName);

        using var request = GetCollectionsRequest.Create(collectionName).Build();

        try
        {
            await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);

            return true;
        }
        catch (HttpOperationException e) when (e.StatusCode == HttpStatusCode.NotFound)
        {
            this._logger.LogDebug(e, "Collection {Name} not found: {Message}, {Response}", collectionName, e.Message, e.ResponseContent);
            return false;
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Collection fetch failed: {Message}, {Response}", e.Message, e.ResponseContent);
            throw;
        }
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> ListCollectionsAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Listing collections");

        using var request = ListCollectionsRequest.Create().Build();

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
        string? responseContent = null;

        try
        {
            (_, responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Collection listing failed: {Message}, {Response}", e.Message, e.ResponseContent);
            throw;
        }
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);
>>>>>>> ms/feature-error-handling

        try
        {
            response.EnsureSuccess(responseContent, this._logger);
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Unable to list collections: {0}, {1}", e.Message, responseContent);
            throw;
        }
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

        var collections = JsonSerializer.Deserialize<ListCollectionsResponse>(responseContent);

        foreach (var collection in collections?.Result?.Collections ?? Enumerable.Empty<ListCollectionsResponse.CollectionResult.CollectionDescription>())
        {
            yield return collection.Name;
        }
    }

    #region private ================================================================================

    private readonly ILogger _logger;
    private readonly HttpClient _httpClient;
    private readonly int _vectorSize;
    private readonly Uri? _endpointOverride;

    private static Uri SanitizeEndpoint(string endpoint, int? port = null)
    {
        Verify.ValidateUrl(endpoint);

        UriBuilder builder = new(endpoint);
        if (port.HasValue) { builder.Port = port.Value; }

        return builder.Uri;
    }

    private async Task<(HttpResponseMessage response, string responseContent)> ExecuteHttpRequestAsync(
        HttpRequestMessage request,
        CancellationToken cancellationToken = default)
    {
        //Apply endpoint override if it's specified.
        if (this._endpointOverride is not null)
        {
            request.RequestUri = new Uri(this._endpointOverride, request.RequestUri!);
        }

        HttpResponseMessage response = await this._httpClient.SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);

        string responseContent = await response.Content.ReadAsStringWithExceptionMappingAsync().ConfigureAwait(false);

        return (response, responseContent);
    }

    #endregion
}
