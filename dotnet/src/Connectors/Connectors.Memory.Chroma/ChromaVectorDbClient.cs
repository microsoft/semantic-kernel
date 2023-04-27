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
using Microsoft.SemanticKernel.Connectors.Memory.Chroma.Diagnostics;
using Microsoft.SemanticKernel.Connectors.Memory.Chroma.Http;
using Microsoft.SemanticKernel.Connectors.Memory.Chroma.Http.ApiSchema;

namespace Microsoft.SemanticKernel.Connectors.Memory.Chroma;

/// <summary>
/// An implementation of a client for the Chroma VectorDB. This class is used to
/// connect, create, delete, and get embeddings data from a Chroma VectorDB instance.
/// </summary>
public class ChromaVectorDbClient
{
    /// <summary>
    /// The endpoint for the Chroma service.
    /// </summary>
    public string BaseAddress => this._httpChromaClient.BaseAddress.ToString();

    /// <summary>
    /// The port for the Chroma service.
    /// </summary>
    public int Port => this._httpChromaClient.BaseAddress.Port;

    public string apiUrl => "/api/v1/";

    /// <summary>
    /// The constructor for the ChromaVectorDbClient.
    /// </summary>
    /// <param name="endpoint"></param>
    /// <param name="vectorSize"></param>
    /// <param name="port"></param>
    /// <param name="httpClient"></param>
    /// <param name="log"></param>
    public ChromaVectorDbClient(
        ChromaSettings chromaSettings,
        HttpClient? httpClient = null,
        ILogger? log = null)
    {
        Verify.NotNull(chromaSettings, "Chroma settings cannot be null or empty");

        this._chromaLog = log ?? NullLogger<ChromaVectorDbClient>.Instance;
        this._httpChromaClient = httpClient ?? new HttpClient(HttpHandlers.CheckCertificateRevocation);
        this._httpChromaClient.BaseAddress = SanitizeEndpoint(chromaSettings.ServerHost, chromaSettings.ServerHttpPort);
        
    }

    /// <inheritdoc/>
     public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancel = default)
    {
        if (string.IsNullOrEmpty(collectionName))
        {
            throw new ArgumentException("Collection name cannot be null or empty.", nameof(collectionName));
        }

        var response = await this._httpChromaClient.DeleteAsync($"/collections/{collectionName}", cancel).ConfigureAwait(false);

        response.EnsureSuccessStatusCode();
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<ChromaVectorRecord> GetVectorsByIdAsync(string collectionName, IEnumerable<string> pointIds, bool withVectors = false,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        this._log.LogDebug("Searching vectors by point ID");

        
        try
        {
            
        }
        catch (HttpRequestException e)
        {
            this._log.LogDebug("Vectors not found {0}", e.Message);
            yield break;
        }

        var data = JsonSerializer.Deserialize<GetResponse>(responseContent);

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
            yield return new ChromaVectorRecord(
                pointId: record.Id,
                embedding: record.Vector ?? Array.Empty<float>(),
                record.Payload,
                tags: null);
        }
#pragma warning restore CS8604
    }

    /// <inheritdoc/>
    public async Task<ChromaVectorRecord?> GetVectorByPayloadIdAsync(string collectionName, string metadataId, bool withVector = false, CancellationToken cancel = default)
    {
        
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

        var record = new ChromaVectorRecord(
            pointId: point.Id,
            embedding: point.Vector ?? Array.Empty<float>(),
            payload: point.Payload,
            tags: null);
        this._log.LogDebug("Vector found}");

        return record;
    }

    /// <inheritdoc/>
    public async Task DeleteVectorsByIdAsync(string collectionName, IEnumerable<string> pointIds, CancellationToken cancel = default)
    {
        this._log.LogDebug("Deleting vector by point ID");

        Verify.NotNullOrEmpty(collectionName, "Collection name is empty");
        Verify.NotNull(pointIds, "Chroma point IDs are NULL");



        foreach (var pointId in pointIds)
        {
            requestBuilder.DeleteVector(pointId);
        }

        using var request = requestBuilder.Build();

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancel).ConfigureAwait(false);

        try
        {
            response.EnsureSuccessStatusCode();
            var result = JsonSerializer.Deserialize<ChromaResponse>(responseContent);
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
    public async Task DeleteVectorByPayloadIdAsync(string collectionName, string metadataId, CancellationToken cancel = default)
    {
        ChromaVectorRecord? existingRecord = await this.GetVectorByPayloadIdAsync(collectionName, metadataId, false, cancel).ConfigureAwait(false);

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

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancel).ConfigureAwait(false);

        try
        {
            response.EnsureSuccessStatusCode();
            var result = JsonSerializer.Deserialize<ChromaResponse>(responseContent);
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
    public async Task UpsertVectorsAsync(string collectionName, IEnumerable<ChromaVectorRecord> vectorData, CancellationToken cancel = default)
    {
        this._log.LogDebug("Upserting vectors");
        Verify.NotNull(vectorData, "The vector data entries are NULL");
        Verify.NotNullOrEmpty(collectionName, "Collection name is empty");

        var requestBuilder = UpsertVectorRequest.Create(collectionName);

        foreach (var record in vectorData)
        {
            ChromaVectorRecord? existingRecord = await this.GetVectorsByIdAsync(collectionName, new[] { record.PointId }, false, cancel).FirstOrDefaultAsync(cancel).ConfigureAwait(false);

            if (existingRecord != null)
            {
                continue;
            }

            requestBuilder.UpsertVector(record);
        }

        using var request = requestBuilder.Build();
        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancel).ConfigureAwait(false);

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
    public async IAsyncEnumerable<(ChromaVectorRecord, double)> FindNearestInCollectionAsync(
        string collectionName,
        IEnumerable<float> target,
        double threshold,
        int top = 1,
        bool withVectors = false,
        IEnumerable<string>? requiredTags = null,
        [EnumeratorCancellation] CancellationToken cancel = default)
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

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancel).ConfigureAwait(false);
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

        var result = new List<(ChromaVectorRecord, double)>();

        foreach (var v in data.Results)
        {
            var record = new ChromaVectorRecord(
                pointId: v.Id,
                embedding: v.Vector ?? Array.Empty<float>(),
                payload: v.Payload);

            result.Add((record, v.Score ?? 0.0));
        }

        // Chroma search results are currently sorted by id, alphabetically, sort list in place
        result.Sort((a, b) => b.Item2.CompareTo(a.Item2));
        foreach (var kv in result)
        {
            yield return kv;
        }
    }

    /// <inheritdoc/>
    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancel = default)
    {
        ChromaMemoryStore chromaMemStore;
        this._log.LogDebug("Creating collection {0}", collectionName);

        string response = chromaMemStore.CreateCollectionAsync(collectionName, cancel);

        
    }

    /// <inheritdoc/>
    public async Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancel = default)
    {
        ChromaMemoryStore chromaMemStore;
        this._log.LogDebug("Fetching collection {0}", collectionName);

       using var request = GetCollectionsRequest.Create(collectionName).Build();
        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancel).ConfigureAwait(false);

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
    public async IAsyncEnumerable<string> ListCollectionsAsync([EnumeratorCancellation] CancellationToken cancel = default)
    {
        this._log.LogDebug("Listing collections");

        using var request = ListCollectionsRequest.Create().Build();
        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancel).ConfigureAwait(false);

        var collections = JsonSerializer.Deserialize<ListCollectionsResponse>(responseContent);

        foreach (var collection in collections?.Result?.Collections ?? Enumerable.Empty<ListCollectionsResponse.CollectionResult.CollectionDescription>())
        {
            yield return collection.Name;
        }
    }

    #region private ================================================================================

    private readonly ILogger _chromaLog;
    private readonly HttpClient _httpChromaClient;
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
        CancellationToken cancel = default)
    {
        HttpResponseMessage response = await this._httpClient.SendAsync(request, cancel).ConfigureAwait(false);

        string responseContent = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
        if (response.IsSuccessStatusCode)
        {
            this._log.LogTrace("Chroma responded successfully");
        }
        else
        {
            this._log.LogTrace("Chroma responded with error");
        }

        return (response, responseContent);
    }

    #endregion
}
