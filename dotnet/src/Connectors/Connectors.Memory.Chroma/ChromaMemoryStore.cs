using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Connectors.Memory.Chroma.Http.ApiSchema;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Memory.Chroma;

/// <summary>
/// A Chroma implementation of <see cref="IMemoryStore"/> that uses the Chroma REST API.
/// </summary>
public class ChromaMemoryStore : IMemoryStore
{
    private readonly HttpClient _httpClient;
    private readonly JsonSerializerOptions _jsonOptions;

    /// <summary>
    /// Initializes a new instance of the <see cref="ChromaMemoryStore"/> class.
    /// </summary>
    /// <param name="httpClient">The <see cref="HttpClient"/> to use for the API calls.</param>
    /// <param name="apiUrl">The base URL of the Chroma API.</param>
    public ChromaMemoryStore(HttpClient httpClient, string apiUrl)
    {
        if (httpClient == null)
        {
            throw new ArgumentNullException(nameof(httpClient));
        }

        if (string.IsNullOrEmpty(apiUrl))
        {
            throw new ArgumentException("API URL cannot be null or empty.", nameof(apiUrl));
        }

        this._httpClient = httpClient;
        this._httpClient.BaseAddress = new Uri(apiUrl);

        this._jsonOptions = new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
            DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
        };
    }

    /// <inheritdoc/>
    public async Task<string> CreateCollectionAsync(string collectionName, CancellationToken cancel = default)
    {
        string responseBody = String.Empty;

        if (string.IsNullOrEmpty(collectionName))
        {
            throw new ArgumentException("Collection name cannot be null or empty.", nameof(collectionName));
        }

        var request = new CreateCollectionRequest
        {
            Name = collectionName,
        };

        var content = new StringContent(JsonSerializer.Serialize(request, this._jsonOptions), Encoding.UTF8, "application/json");

        var response = await this._httpClient.PostAsync("/collections", content, cancel).ConfigureAwait(false);

        response.EnsureSuccessStatusCode();

        responseBody = await response.Content.ReadAsStringAsync();

        return responseBody;
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> GetCollectionsAsync(CancellationToken cancel = default)
    {
        var response = await this._httpClient.GetAsync("/collections", cancel).ConfigureAwait(false);

        response.EnsureSuccessStatusCode();

        var json = await response.Content.ReadAsStringAsync().ConfigureAwait(false);

        var collections = JsonSerializer.Deserialize<IEnumerable<GetResponse>>(json, this._jsonOptions);

        foreach (var collection in collections!)
        {
            yield return collection.Name;
        }
    }

    /// <inheritdoc/>
    public async Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancel = default)
    {
        if (string.IsNullOrEmpty(collectionName))
        {
            throw new ArgumentException("Collection name cannot be null or empty.", nameof(collectionName));
        }

        var response = await this._httpClient.GetAsync($"/collections/{collectionName}", cancel).ConfigureAwait(false);

        return response.IsSuccessStatusCode;
    }

    /// <inheritdoc/>
   

    /// <inheritdoc/>
    public async Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancel = default)
    {
        if (string.IsNullOrEmpty(collectionName))
        {
            throw new ArgumentException("Collection name cannot be null or empty.", nameof(collectionName));
        }

        if (record == null)
        {
            throw new ArgumentNullException(nameof(record));
        }

        var request = new AddRequest
        {
            Embeddings = new[] { record.Embedding.Vector.FirstOrDefault()},
            Metadatas = new[] { record.Metadata },
            Documents = new[] { String.Empty },
            Ids = new[] { record.Key },
        };

        var content = new StringContent(JsonSerializer.Serialize(request, this._jsonOptions), Encoding.UTF8, "application/json");

        var response = await this._httpClient.PostAsync($"/collections/{collectionName}/add", content, cancel).ConfigureAwait(false);

        response.EnsureSuccessStatusCode();

        return record.Key;
    }


    IAsyncEnumerable<string> IMemoryStore.UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> records, CancellationToken cancel)
    {
        throw new NotImplementedException();
    }

    public async Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding, CancellationToken cancel)
    {
        var response = await this._httpClient.GetAsync($"create_collection{collectionName}").ConfigureAwait(false);

        response.EnsureSuccessStatusCode();

        return MemoryRecord.FromJsonMetadata(
                    json: await response.Content.ReadAsStringAsync(),
                    embedding: null,
                    key: collectionName);
       
    }

    IAsyncEnumerable<MemoryRecord> IMemoryStore.GetBatchAsync(string collectionName, IEnumerable<string> keys, bool withEmbeddings, CancellationToken cancel)
    {
        throw new NotImplementedException();
    }

    Task RemoveAsync(string collectionName, string key, CancellationToken cancel)
    {
        Delete
    }

    Task IMemoryStore.RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancel)
    {
        throw new NotImplementedException();
    }

    IAsyncEnumerable<(MemoryRecord, double)> IMemoryStore.GetNearestMatchesAsync(string collectionName, Embedding<float> embedding, int limit, double minRelevanceScore, bool withEmbeddings, CancellationToken cancel)
    {
        throw new NotImplementedException();
    }

    Task<(MemoryRecord, double)?> IMemoryStore.GetNearestMatchAsync(string collectionName, Embedding<float> embedding, double minRelevanceScore, bool withEmbedding, CancellationToken cancel)
    {
        throw new NotImplementedException();
    }
}