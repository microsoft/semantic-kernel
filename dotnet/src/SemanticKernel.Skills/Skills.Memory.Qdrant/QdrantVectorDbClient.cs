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
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.DataModels;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.Diagnostics;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.HttpSchema;
using Micrsoft.SemanticKernel.Skills.Memory.Qdrant.HttpSchema;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant;

/// <summary>
/// An implementation of a client for the Qdrant VectorDB. This class is used to
/// connect, create, delete, and get embeddings data from a Qdrant VectorDB instance.
/// </summary>
public class QdrantVectorDbClient<TEmbedding>
where TEmbedding : unmanaged
{
    public string BaseAddress
    {
        get { return this._httpClient.BaseAddress.ToString(); }
        set { this._httpClient.BaseAddress = SanitizeEndpoint(value); }
    }

    public int Port
    {
        get { return this._httpClient.BaseAddress.Port; }
        set { this._httpClient.BaseAddress = SanitizeEndpoint(this.BaseAddress, value); }
    }

    public QdrantVectorDbClient(
        string endpoint,
        int? port = null,
        HttpClient? httpClient = null,
        ILogger<QdrantVectorDbClient<TEmbedding>>? log = null)
    {
        this._log = log ?? NullLogger<QdrantVectorDbClient<TEmbedding>>.Instance;

        this._httpClient = httpClient ?? new HttpClient(HttpHandlers.CheckCertificateRevocation);
        this.BaseAddress = endpoint;

        if (port.HasValue)
        {
            this.Port = port.Value;
        }
    }

    public async Task<DataEntry<QdrantVectorRecord<TEmbedding>>?> GetVectorByIdAsync(string collectionName, string key)
    {
        var pointId = Base64Encode(key);

        this._log.LogDebug("Searching vector by point ID {0}", pointId);

        using HttpRequestMessage request = SearchVectorsRequest<TEmbedding>
            .Create(collectionName, this._defaultVectorSize)
            .HavingExternalId(pointId)
            .IncludePayLoad()
            .TakeFirst()
            .Build();

        var (response, responseContent) = await this.ExecuteHttpRequestAsync(request);
        response.EnsureSuccessStatusCode();

        var data = new SearchVectorsResponse<TEmbedding>(responseContent);
        Verify.Equals("ok", data.Status, "Something went wrong while looking for the vector");

        if (data.Vectors.Count == 0)
        {
            this._log.LogWarning("Vector not found: {0}", pointId);
            return null;
        }

        var record = new QdrantVectorRecord<TEmbedding>(
            new Embedding<TEmbedding>(data.Vectors.First().Vector.ToArray()),
            data.Vectors.First().ExternalPayload,
            data.Vectors.First().ExternalTags);
        this._log.LogDebug("Vector found}");

        return new DataEntry<QdrantVectorRecord<TEmbedding>>(Base64Decode(pointId), record);
    }

    public async Task DeleteVectorAsync(string collectionName, string key)
    {
        var pointId = Base64Encode(key);
        this._log.LogDebug("Deleting vector by point ID {0}", pointId);

        Verify.NotNullOrEmpty(collectionName, "Collection name is empty");
        Verify.NotNullOrEmpty(pointId, "Qdrant point ID is empty");

        using var request = DeleteVectorsRequest
            .DeleteFrom(collectionName)
            .DeleteVector(pointId)
            .Build();
        await this.ExecuteHttpRequestAsync(request);
    }

    public async Task UpsertVectorAsync(string collectionName, DataEntry<QdrantVectorRecord<TEmbedding>> vectorData)
    {
        this._log.LogDebug("Upserting vector");
        Verify.NotNull(vectorData, "The vector is NULL");

        DataEntry<QdrantVectorRecord<TEmbedding>>? existingRecord = await this.GetVectorByIdAsync(collectionName, vectorData.Key);

        // Generate a new ID for the new vector
        if (existingRecord == null)
        {
            return;
        }

        using var request = CreateVectorsRequest<TEmbedding>
            .CreateIn(collectionName)
            .UpsertVector(Base64Encode(vectorData.Key), vectorData.Value).Build();
        var (response, responseContent) = await this.ExecuteHttpRequestAsync(request);

        if (response.StatusCode == HttpStatusCode.UnprocessableEntity
            && responseContent.Contains("data did not match any variant of untagged enum ExtendedPointId", StringComparison.OrdinalIgnoreCase))
        {
            throw new VectorDbException("The vector ID must be a GUID string");
        }

        try
        {
            response.EnsureSuccessStatusCode();
        }
        catch (Exception e)
        {
            this._log.LogError(e, "Vector upsert failed: {0}, {1}", e.Message, responseContent);
            throw;
        }
    }

    public async IAsyncEnumerable<(QdrantVectorRecord<TEmbedding>, double)> FindNearesetInCollectionAsync(
        string collectionName,
        Embedding<TEmbedding> target,
        int top = 1,
        string[]? requiredTags = null)
    {
        this._log.LogDebug("Searching top {0} closest vectors in {1}", top);

        Verify.NotNull(target, "The given vector is NULL");

        using HttpRequestMessage request = SearchVectorsRequest<TEmbedding>
            .Create(collectionName)
            .SimilarTo(target.Vector.ToArray())
            .HavingTags(requiredTags)
            .IncludePayLoad()
            .IncludeVectorData()
            .Take(top)
            .Build();

        var (response, responseContent) = await this.ExecuteHttpRequestAsync(request);
        response.EnsureSuccessStatusCode();

        var data = new SearchVectorsResponse<TEmbedding>(responseContent);
        Verify.Equals("ok", data.Status, "Something went wrong while looking for the vector");

        if (data.Vectors.Count == 0)
        {
            this._log.LogWarning("Nothing found");
            yield break;
        }

        var result = new List<(QdrantVectorRecord<TEmbedding>, double)>();

        foreach (var v in data.Vectors)
        {
            var record = new QdrantVectorRecord<TEmbedding>(
                new Embedding<TEmbedding>(v.Vector),
                v.ExternalPayload,
                v.ExternalTags);

            result.Add((record, v.Score ?? 0));
        }

        // Qdrant search results are currently sorted by id, alphabetically
        result = SortSearchResultByScore(result);
        foreach (var kv in result)
        {
            yield return kv;
        }
    }

    public async Task CreateCollectionAsync(string collectionName)
    {
        this._log.LogDebug("Creating collection {0}", collectionName);

        using var request = CreateCollectionRequest
            .Create(collectionName)
            .WithVectorSize(this._defaultVectorSize)
            .WithDistanceType(QdrantDistanceType.Cosine)
            .Build();
        var (response, responseContent) = await this.ExecuteHttpRequestAsync(request);
        
        // Creation is idempotent, ignore error (and for now ignore vector size)
        if (response.StatusCode == HttpStatusCode.BadRequest)
        {
            if (responseContent.Contains("already exists", StringComparison.InvariantCultureIgnoreCase)) { return; }
        }

        try
        {
            response.EnsureSuccessStatusCode();
        }
        catch (Exception e)
        {
            this._log.LogError(e, "Collection upsert failed: {0}, {1}", e.Message, responseContent);
            throw;
        }
    }

    public async Task<bool> DoesCollectionExistAsync(string collectionName)
    {
        this._log.LogDebug("Fetching collection {0}", collectionName);

        using var request = FetchCollectionRequest.Fetch(collectionName).Build();
        var (response, responseContent) = await this.ExecuteHttpRequestAsync(request);

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

    public async IAsyncEnumerable<string> ListCollectionsAsync()
    {
        this._log.LogDebug("Listing collections");

        using var request = ListCollectionsRequest.Create().Build();
        var (response, responseContent) = await this.ExecuteHttpRequestAsync(request);

        var collections = JsonSerializer.Deserialize<ListCollectionsResponse>(responseContent);

        foreach (var collection in collections?.Collections ?? Enumerable.Empty<ListCollectionsResponse.CollectionDescription>())
        {
            yield return collection.Name;
        }
    }

    #region private ================================================================================

    private readonly ILogger<QdrantVectorDbClient<TEmbedding>> _log;
    private readonly HttpClient _httpClient;
    private readonly int _defaultVectorSize = 1536; //output dimension size for OpenAI's text-emebdding-ada-002

    private static List<(QdrantVectorRecord<TEmbedding>, double)> SortSearchResultByScore(
        List<(QdrantVectorRecord<TEmbedding>, double)> tuplesList)
    {
        // Sort list in place
        tuplesList.Sort((a, b) => b.Item2.CompareTo(a.Item2));
        return tuplesList;
    }

    private static string Base64Encode(string plainText)
    {
        var byteString = System.Text.Encoding.UTF8.GetBytes(plainText);
        return Convert.ToBase64String(byteString);
    }

    private static string Base64Decode(string base64Text)
    {
        var bytes = Convert.FromBase64String(base64Text);
        return System.Text.Encoding.UTF8.GetString(bytes);
    }

    private static Uri SanitizeEndpoint(string endpoint)
    {
        Verify.IsValidUrl(nameof(endpoint), endpoint, false, true, false);
        return new Uri(endpoint);
    }

    private static Uri SanitizeEndpoint(string endpoint, int port)
    {
        UriBuilder builder =
            new UriBuilder(SanitizeEndpoint(endpoint)) { Port = port };
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
            this._log.LogWarning("Qdrant responsed with error");
        }

        return (response, responseContent);
    }

    #endregion
}
