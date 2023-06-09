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
using Microsoft.SemanticKernel.Connectors.Memory.Qdrant.Diagnostics;
using Microsoft.SemanticKernel.Connectors.Memory.Qdrant.Http;
using Microsoft.SemanticKernel.Connectors.Memory.Qdrant.Http.ApiSchema;

namespace Microsoft.SemanticKernel.Connectors.Memory.Qdrant;

/// <summary>
/// An implementation of a client for the Qdrant VectorDB. This class is used to
/// connect, create, delete, and get embeddings data from a Qdrant VectorDB instance.
/// </summary>
public class QdrantVectorDbClient : IQdrantVectorDbClient
{
    /// <summary>
    /// The endpoint for the Qdrant service.
    /// </summary>
    public string BaseAddress => this._httpClient.BaseAddress.ToString();

    /// <summary>
    /// The port for the Qdrant service.
    /// </summary>
    public int Port => this._httpClient.BaseAddress.Port;

    /// <summary>
    /// The constructor for the QdrantVectorDbClient.
    /// </summary>
    /// <param name="endpoint"></param>
    /// <param name="vectorSize"></param>
    /// <param name="port"></param>
    /// <param name="httpClient"></param>
    /// <param name="log"></param>
    public QdrantVectorDbClient(
        string endpoint,
        int vectorSize,
        int? port = null,
        HttpClient? httpClient = null,
        ILogger? log = null)
    {
        Verify.ArgNotNullOrEmpty(endpoint, "Qdrant endpoint cannot be null or empty");

        this._vectorSize = vectorSize;
        this._log = log ?? NullLogger<QdrantVectorDbClient>.Instance;
        this._httpClient = httpClient ?? new HttpClient(HttpHandlers.CheckCertificateRevocation);
        this._httpClient.BaseAddress = SanitizeEndpoint(endpoint, port);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<QdrantVectorRecord> GetVectorsByIdAsync(string collectionName, IEnumerable<string> pointIds, bool withVectors = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this._log.LogDebug("Searching vectors by point ID");

        using HttpRequestMessage request = GetVectorsRequest.Create(collectionName)
            .WithPointIDs(pointIds)
            .WithPayloads(true)
            .WithVectors(withVectors)
            .Build();

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);
        try
        {
            response.EnsureSuccessStatusCode();
        }
        catch (HttpRequestException e)
        {
            this._log.LogDebug("Vectors not found {0}", e.Message);
            yield break;
        }

        var data = JsonSerializer.Deserialize<GetVectorsResponse>(responseContent);

        if (data == null)
        {
            this._log.LogWarning("Unable to deserialize Get response");
            yield break;
        }

        if (!data.Result.Any())
        {
            this._log.LogWarning("Vectors not found");
            yield break;
        }

        var records = data.Result;

#pragma warning disable CS8604 // The request specifically asked for a payload to be in the response
        foreach (var record in records)
        {
            yield return new QdrantVectorRecord(
                pointId: record.Id,
                embedding: record.Vector ?? Array.Empty<float>(),
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

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);
        try
        {
            response.EnsureSuccessStatusCode();
        }
        catch (HttpRequestException e)
        {
            this._log.LogDebug("Request for vector with payload ID failed {0}", e.Message);
            return null;
        }

        var data = JsonSerializer.Deserialize<SearchVectorsResponse>(responseContent);

        if (data == null)
        {
            this._log.LogWarning("Unable to deserialize Search response");
            return null;
        }

        if (!data.Results.Any())
        {
            this._log.LogDebug("Vector not found");
            return null;
        }

        var point = data.Results.First();

        var record = new QdrantVectorRecord(
            pointId: point.Id,
            embedding: point.Vector ?? Array.Empty<float>(),
            payload: point.Payload,
            tags: null);
        this._log.LogDebug("Vector found}");

        return record;
    }

    /// <inheritdoc/>
    public async Task DeleteVectorsByIdAsync(string collectionName, IEnumerable<string> pointIds, CancellationToken cancellationToken = default)
    {
        this._log.LogDebug("Deleting vector by point ID");

        Verify.NotNullOrEmpty(collectionName, "Collection name is empty");
        Verify.NotNull(pointIds, "Qdrant point IDs are NULL");

        using var request = DeleteVectorsRequest.DeleteFrom(collectionName)
            .DeleteRange(pointIds)
            .Build();
        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);

        try
        {
            response.EnsureSuccessStatusCode();
            var result = JsonSerializer.Deserialize<QdrantResponse>(responseContent);
            if (result?.Status == "ok")
            {
                this._log.LogDebug("Vector being deleted");
            }
            else
            {
                this._log.LogWarning("Vector delete failed");
            }
        }
        catch (HttpRequestException e)
        {
            this._log.LogError(e, "Vector delete request failed: {0}", e.Message);
        }
    }

    /// <inheritdoc/>
    public async Task DeleteVectorByPayloadIdAsync(string collectionName, string metadataId, CancellationToken cancellationToken = default)
    {
        QdrantVectorRecord? existingRecord = await this.GetVectorByPayloadIdAsync(collectionName, metadataId, false, cancellationToken).ConfigureAwait(false);

        if (existingRecord == null)
        {
            this._log.LogDebug("Vector not found, nothing to delete");
            return;
        }

        this._log.LogDebug("Vector found, deleting");

        using var request = DeleteVectorsRequest
            .DeleteFrom(collectionName)
            .DeleteVector(existingRecord.PointId)
            .Build();

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);

        try
        {
            response.EnsureSuccessStatusCode();
            var result = JsonSerializer.Deserialize<QdrantResponse>(responseContent);
            if (result?.Status == "ok")
            {
                this._log.LogDebug("Vector being deleted");
            }
            else
            {
                this._log.LogWarning("Vector delete failed");
            }
        }
        catch (HttpRequestException e)
        {
            this._log.LogError(e, "Vector delete request failed: {0}", e.Message);
        }
    }

    /// <inheritdoc/>
    public async Task UpsertVectorsAsync(string collectionName, IEnumerable<QdrantVectorRecord> vectorData, CancellationToken cancellationToken = default)
    {
        this._log.LogDebug("Upserting vectors");
        Verify.NotNull(vectorData, "The vector data entries are NULL");
        Verify.NotNullOrEmpty(collectionName, "Collection name is empty");

        using var request = UpsertVectorRequest.Create(collectionName)
            .UpsertRange(vectorData)
            .Build();
        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);

        try
        {
            response.EnsureSuccessStatusCode();
            var result = JsonSerializer.Deserialize<UpsertVectorResponse>(responseContent);
            if (result?.Status == "ok")
            {
                this._log.LogDebug("Vectors upserted");
            }
            else
            {
                this._log.LogWarning("Vector upserts failed");
            }
        }
        catch (HttpRequestException e)
        {
            this._log.LogError(e, "Vector upserts request failed: {0}", e.Message);
        }
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<(QdrantVectorRecord, double)> FindNearestInCollectionAsync(
        string collectionName,
        IEnumerable<float> target,
        double threshold,
        int top = 1,
        bool withVectors = false,
        IEnumerable<string>? requiredTags = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this._log.LogDebug("Searching top {0} nearest vectors", top);

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

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);

        if (response.StatusCode == HttpStatusCode.NotFound)
        {
            this._log.LogWarning("No vectors were found.");
            yield break;
        }

        response.EnsureSuccessStatusCode();

        var data = JsonSerializer.Deserialize<SearchVectorsResponse>(responseContent);

        if (data == null)
        {
            this._log.LogWarning("Unable to deserialize Search response");
            yield break;
        }

        if (!data.Results.Any())
        {
            this._log.LogWarning("Nothing found");
            yield break;
        }

        var result = new List<(QdrantVectorRecord, double)>();

        foreach (var v in data.Results)
        {
            var record = new QdrantVectorRecord(
                pointId: v.Id,
                embedding: v.Vector ?? Array.Empty<float>(),
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
        this._log.LogDebug("Creating collection {0}", collectionName);

        using var request = CreateCollectionRequest
            .Create(collectionName, this._vectorSize, QdrantDistanceType.Cosine)
            .Build();

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);

        // Creation is idempotent, ignore error (and for now ignore vector size)
        if (response.StatusCode == HttpStatusCode.BadRequest)
        {
            if (responseContent.IndexOf("already exists", StringComparison.OrdinalIgnoreCase) >= 0) { return; }
        }

        try
        {
            response.EnsureSuccessStatusCode();
        }
        catch (HttpRequestException e)
        {
            this._log.LogError(e, "Collection upsert failed: {0}, {1}", e.Message, responseContent);
            throw;
        }
    }

    /// <inheritdoc/>
    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        this._log.LogDebug("Deleting collection {0}", collectionName);

        using var request = DeleteCollectionRequest.Create(collectionName).Build();
        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);

        // Deletion is idempotent, ignore error
        if (response.StatusCode == HttpStatusCode.NotFound)
        {
            return;
        }

        try
        {
            response.EnsureSuccessStatusCode();
        }
        catch (HttpRequestException e)
        {
            this._log.LogError(e, "Collection deletion failed: {0}, {1}", e.Message, responseContent);
            throw;
        }
    }

    /// <inheritdoc/>
    public async Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        this._log.LogDebug("Fetching collection {0}", collectionName);

        using var request = GetCollectionsRequest.Create(collectionName).Build();
        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);

        if (response.IsSuccessStatusCode)
        {
            return true;
        }
        else if (response.StatusCode == HttpStatusCode.NotFound)
        {
            return false;
        }
        else
        {
            this._log.LogError("Collection fetch failed: {0}, {1}", response.StatusCode, responseContent);
            return false;
        }
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> ListCollectionsAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this._log.LogDebug("Listing collections");

        using var request = ListCollectionsRequest.Create().Build();
        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);

        var collections = JsonSerializer.Deserialize<ListCollectionsResponse>(responseContent);

        foreach (var collection in collections?.Result?.Collections ?? Enumerable.Empty<ListCollectionsResponse.CollectionResult.CollectionDescription>())
        {
            yield return collection.Name;
        }
    }

    #region private ================================================================================

    private readonly ILogger _log;
    private readonly HttpClient _httpClient;
    private readonly int _vectorSize;

    private static Uri SanitizeEndpoint(string endpoint, int? port)
    {
        Verify.IsValidUrl(nameof(endpoint), endpoint, false, true, false);

        UriBuilder builder = new(endpoint);
        if (port.HasValue) { builder.Port = port.Value; }

        return builder.Uri;
    }

    private async Task<(HttpResponseMessage response, string responseContent)> ExecuteHttpRequestAsync(
        HttpRequestMessage request,
        CancellationToken cancellationToken = default)
    {
        HttpResponseMessage response = await this._httpClient.SendAsync(request, cancellationToken).ConfigureAwait(false);

        string responseContent = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
        if (response.IsSuccessStatusCode)
        {
            this._log.LogTrace("Qdrant responded successfully");
        }
        else
        {
            this._log.LogTrace("Qdrant responded with error");
        }

        return (response, responseContent);
    }

    #endregion
}
