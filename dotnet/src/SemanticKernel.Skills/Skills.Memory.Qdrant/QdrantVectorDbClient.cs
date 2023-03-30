// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory.Storage;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.Diagnostics;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.Http;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.Http.ApiSchema;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant;

/// <summary>
/// An implementation of a client for the Qdrant VectorDB. This class is used to
/// connect, create, delete, and get embeddings data from a Qdrant VectorDB instance.
/// </summary>
public class QdrantVectorDbClient<TEmbedding>
    where TEmbedding : unmanaged
{
    /// <summary>
    /// The endpoint for the Qdrant service.
    /// </summary>
    public string BaseAddress
    {
        get { return this._httpClient.BaseAddress.ToString(); }
    }

    /// <summary>
    /// The port for the Qdrant service.
    /// </summary>
    public int Port
    {
        get { return this._httpClient.BaseAddress.Port; }
    }

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
        this._log = log ?? NullLogger<QdrantVectorDbClient<TEmbedding>>.Instance;
        this._httpClient = httpClient ?? new HttpClient(HttpHandlers.CheckCertificateRevocation);
        this._httpClient.BaseAddress = SanitizeEndpoint(endpoint, port);
    }

    /// <summary>
    /// Get a specific vector by its unique Qdrant ID.
    /// </summary>
    /// <param name="collectionName"></param>
    /// <param name="pointId"></param>
    /// <returns></returns>
    public async Task<DataEntry<QdrantVectorRecord<TEmbedding>>?> GetVectorByIdAsync(string collectionName, string pointId)
    {
        this._log.LogDebug("Searching vector by point ID");

        using HttpRequestMessage request = GetVectorsRequest.Create(collectionName)
            .WithPointId(pointId)
            .WithPayloads(true)
            .WithVectors(true)
            .Build();

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request);
        try
        {
            response.EnsureSuccessStatusCode();
        }
        catch (HttpRequestException e)
        {
            this._log.LogDebug("Vector not found {0}", e.Message);
            return null;
        }

        var data = JsonSerializer.Deserialize<GetVectorsResponse<TEmbedding>>(responseContent);

        if (data == null)
        {
            this._log.LogWarning("Unable to deserialize Get response");
            return null;
        }

        if (!data.Result.Any())
        {
            this._log.LogWarning("Vector not found");
            return null;
        }

        var recordData = data.Result.First();

#pragma warning disable CS8604 // The request specifically asked for a payload to be in the response
        var record = new QdrantVectorRecord<TEmbedding>(
            new Embedding<TEmbedding>(
                recordData.Vector!.ToArray()), // The request specifically asked for a vector to be in the response
            recordData.Payload,
            null);
#pragma warning restore CS8604

        this._log.LogDebug("Vector found");

        return new DataEntry<QdrantVectorRecord<TEmbedding>>(pointId.ToString(), record);
    }

    /// <summary>
    /// Get a specific vector by a unique identifier in the metadata (Qdrant payload).
    /// </summary>
    /// <param name="collectionName"></param>
    /// <param name="metadataId"></param>
    /// <returns></returns>
    public async Task<DataEntry<QdrantVectorRecord<TEmbedding>>?> GetVectorByPayloadIdAsync(string collectionName, string metadataId)
    {
        using HttpRequestMessage request = SearchVectorsRequest<TEmbedding>.Create(collectionName)
            .SimilarTo(new TEmbedding[this._vectorSize])
            .HavingExternalId(metadataId)
            .IncludePayLoad()
            .TakeFirst()
            .IncludeVectorData()
            .Build();

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request);
        try
        {
            response.EnsureSuccessStatusCode();
        }
        catch (HttpRequestException e)
        {
            this._log.LogDebug("Request for vector with payload ID failed {0}", e.Message);
            return null;
        }

        var data = JsonSerializer.Deserialize<SearchVectorsResponse<TEmbedding>>(responseContent);

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

        var record = new QdrantVectorRecord<TEmbedding>(
            new Embedding<TEmbedding>(
                point.Vector.ToArray()),
            point.Payload,
            null);
        this._log.LogDebug("Vector found}");

        return new DataEntry<QdrantVectorRecord<TEmbedding>>(point.Id, record);
    }

    /// <summary>
    /// Delete a vector by its unique Qdrant ID.
    /// </summary>
    /// <param name="collectionName"></param>
    /// <param name="pointId"></param>
    /// <returns></returns>
    public async Task DeleteVectorByIdAsync(string collectionName, string pointId)
    {
        this._log.LogDebug("Deleting vector by point ID");

        Verify.NotNullOrEmpty(collectionName, "Collection name is empty");
        Verify.NotNull(pointId, "Qdrant point ID is NULL");

        using var request = DeleteVectorsRequest
            .DeleteFrom(collectionName)
            .DeleteVector(pointId)
            .Build();

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request);

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

    /// <summary>
    /// Delete a vector by its unique identifier in the metadata (Qdrant payload).
    /// </summary>
    /// <param name="collectionName"></param>
    /// <param name="metadataId"></param>
    /// <returns></returns>
    public async Task DeleteVectorByPayloadIdAsync(string collectionName, string metadataId)
    {
        DataEntry<QdrantVectorRecord<TEmbedding>>? existingRecord = await this.GetVectorByPayloadIdAsync(collectionName, metadataId);

        if (existingRecord == null)
        {
            this._log.LogDebug("Vector not found");
            return;
        }

        this._log.LogDebug("Vector found, deleting");

        using var request = DeleteVectorsRequest
            .DeleteFrom(collectionName)
            .DeleteVector(existingRecord.Value.Key)
            .Build();

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request);

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

    /// <summary>
    /// Upsert a vector.
    /// </summary>
    /// <param name="collectionName"></param>
    /// <param name="vectorData"></param>
    /// <returns></returns>
    public async Task UpsertVectorAsync(string collectionName, DataEntry<QdrantVectorRecord<TEmbedding>> vectorData)
    {
        this._log.LogDebug("Upserting vector");
        Verify.NotNull(vectorData, "The vector data entry is NULL");
        Verify.NotNull(vectorData.Value, "The vector data entry contains NULL value");

        DataEntry<QdrantVectorRecord<TEmbedding>>? existingRecord = await this.GetVectorByPayloadIdAsync(collectionName, vectorData.Key);

        if (existingRecord != null)
        {
            return;
        }

        // Generate a new ID for the new vector
        using var request = UpsertVectorRequest<TEmbedding>
            .Create(collectionName)
            .UpsertVector(Guid.NewGuid().ToString(), vectorData.Value).Build();
        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request);

        try
        {
            response.EnsureSuccessStatusCode();
            var result = JsonSerializer.Deserialize<UpsertVectorResponse>(responseContent);
            if (result?.Status == "ok")
            {
                this._log.LogDebug("Vector upserted");
            }
            else
            {
                this._log.LogWarning("Vector upsert failed");
            }
        }
        catch (HttpRequestException e)
        {
            this._log.LogError(e, "Vector upsert request failed: {0}", e.Message);
        }
    }

    /// <summary>
    /// Find the nearest vectors in a collection using vector similarity search.
    /// </summary>
    /// <param name="collectionName"></param>
    /// <param name="target"></param>
    /// <param name="threshold"></param>
    /// <param name="top"></param>
    /// <param name="requiredTags"></param>
    /// <returns></returns>
    public async IAsyncEnumerable<(QdrantVectorRecord<TEmbedding>, double)> FindNearestInCollectionAsync(
        string collectionName,
        Embedding<TEmbedding> target,
        double threshold,
        int top = 1,
        IEnumerable<string>? requiredTags = null)
    {
        this._log.LogDebug("Searching top {0} closest vectors in {1}", top);

        Verify.NotNull(target, "The given vector is NULL");

        using HttpRequestMessage request = SearchVectorsRequest<TEmbedding>
            .Create(collectionName)
            .SimilarTo(target.Vector.ToArray())
            .HavingTags(requiredTags)
            .WithScoreThreshold(threshold)
            .IncludePayLoad()
            .IncludeVectorData()
            .Take(top)
            .Build();

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request);
        response.EnsureSuccessStatusCode();

        var data = JsonSerializer.Deserialize<SearchVectorsResponse<TEmbedding>>(responseContent);

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

        var result = new List<(QdrantVectorRecord<TEmbedding>, double)>();

        foreach (var v in data.Results)
        {
            var record = new QdrantVectorRecord<TEmbedding>(
                new Embedding<TEmbedding>(v.Vector),
                v.Payload);

            result.Add((record, v.Score ?? 0));
        }

        // Qdrant search results are currently sorted by id, alphabetically
        result = SortSearchResultByScore(result);
        foreach (var kv in result)
        {
            yield return kv;
        }
    }

    /// <summary>
    /// Create a Qdrant vector collection.
    /// </summary>
    /// <param name="collectionName"></param>
    /// <returns></returns>
    public async Task CreateCollectionAsync(string collectionName)
    {
        this._log.LogDebug("Creating collection {0}", collectionName);

        using var request = CreateCollectionRequest
            .Create(collectionName, this._vectorSize, QdrantDistanceType.Cosine)
            .Build();

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request);

        // Creation is idempotent, ignore error (and for now ignore vector size)
        if (response.StatusCode == HttpStatusCode.BadRequest)
        {
            if (responseContent.Contains("already exists", StringComparison.InvariantCultureIgnoreCase)) { return; }
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

    /// <summary>
    /// Delete a Qdrant vector collection.
    /// </summary>
    /// <param name="collectionName"></param>
    /// <returns></returns>
    public async Task DeleteCollectionAsync(string collectionName)
    {
        this._log.LogDebug("Deleting collection {0}", collectionName);

        using var request = DeleteCollectionRequest.Create(collectionName).Build();
        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request);

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

    /// <summary>
    /// Check if a vector collection exists.
    /// </summary>
    /// <param name="collectionName"></param>
    /// <returns></returns>
    /// <exception cref="VectorDbException"></exception>
    public async Task<bool> DoesCollectionExistAsync(string collectionName)
    {
        this._log.LogDebug("Fetching collection {0}", collectionName);

        using var request = GetCollectionsRequest.Create(collectionName).Build();
        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request);

        if (response.StatusCode == HttpStatusCode.NotFound)
        {
            return false;
        }

        if (response.IsSuccessStatusCode)
        {
            return true;
        }

        this._log.LogError("Collection fetch failed: {0}, {1}", response.StatusCode, responseContent);
        throw new VectorDbException($"Unexpected response: {response.StatusCode}");
    }

    /// <summary>
    /// List all vector collections.
    /// </summary>
    /// <returns></returns>
    public async IAsyncEnumerable<string> ListCollectionsAsync()
    {
        this._log.LogDebug("Listing collections");

        using var request = ListCollectionsRequest.Create().Build();
        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request);

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

    private static List<(QdrantVectorRecord<TEmbedding>, double)> SortSearchResultByScore(
        List<(QdrantVectorRecord<TEmbedding>, double)> tuplesList)
    {
        // Sort list in place
        tuplesList.Sort((a, b) => b.Item2.CompareTo(a.Item2));
        return tuplesList;
    }

    private static Uri SanitizeEndpoint(string endpoint, int? port)
    {
        Verify.IsValidUrl(nameof(endpoint), endpoint, false, true, false);

        UriBuilder builder = new(endpoint);
        if (port.HasValue) { builder.Port = port.Value; }

        return builder.Uri;
    }

    private async Task<(HttpResponseMessage response, string responseContent)> ExecuteHttpRequestAsync(HttpRequestMessage request)
    {
        HttpResponseMessage response = await this._httpClient.SendAsync(request);

        string responseContent = await response.Content.ReadAsStringAsync();
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
