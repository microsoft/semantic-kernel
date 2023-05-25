// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Diagnostics;
using Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Http.ApiSchema;
using Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Model;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Memory.Weaviate;

/// <summary>
/// An implementation of <see cref="IMemoryStore" /> for Weaviate.
/// </summary>
/// <remarks>The Embedding data is saved to Weaviate instance specified in the constructor.
/// The embedding data persists between subsequent instances and has similarity search capability.
/// </remarks>
// ReSharper disable once ClassWithVirtualMembersNeverInherited.Global
public class WeaviateMemoryStore : IMemoryStore, IDisposable
{
    // Regex to ensure Weaviate class names confirm to the naming convention
    // https://weaviate.io/developers/weaviate/configuration/schema-configuration#class
    private static readonly Regex s_classNameRegEx = new(@"[^0-9a-zA-Z]+", RegexOptions.Compiled);

    private static readonly JsonSerializerOptions s_jsonSerializerOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
    };

    private readonly HttpClient _httpClient;
    private readonly bool _isSelfManagedHttpClient;

    private readonly ILogger _log;
    private bool _disposed;

    /// <summary>
    ///     Constructor for a memory store backed by Weaviate
    /// </summary>
    public WeaviateMemoryStore(string scheme, string host, int port, string? apiKey = null, HttpClient? httpClient = null, ILogger? logger = null)
    {
        Verify.ArgNotNullOrEmpty(scheme, "Scheme cannot be null or empty");
        Verify.ArgNotNullOrEmpty(host, "Endpoint cannot be null or empty");

        this._log = logger ?? NullLogger<WeaviateMemoryStore>.Instance;
        if (httpClient == null)
        {
            if (string.IsNullOrEmpty(apiKey))
            {
                this._httpClient = new();
            }
            else
            {
                this._httpClient = new()
                {
                    DefaultRequestHeaders =
                    {
                        {
                            "authorization", apiKey
                        }
                    }
                };
            }

            // If not passed an HttpClient, then it is the responsibility of this class
            // to ensure it is cleared up in the Dispose() method.
            this._isSelfManagedHttpClient = true;
        }
        else
        {
            this._httpClient = httpClient;
        }

        this._httpClient.BaseAddress = new($"{scheme}://{host}:{port}/v1/");
    }

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    /// <inheritdoc />
    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancel = default)
    {
        Verify.NotNullOrEmpty(collectionName, "Collection name is empty");

        string className = ToWeaviateFriendlyClassName(collectionName);
        this._log.LogTrace("Creating collection: {0}, with class name: {1}", collectionName, className);

        using HttpRequestMessage request = CreateClassSchemaRequest
            .Create(className, ToWeaviateFriendlyClassDescription(collectionName))
            .Build();

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancel).ConfigureAwait(false);
        CreateClassSchemaResponse? result = JsonSerializer.Deserialize<CreateClassSchemaResponse>(responseContent, s_jsonSerializerOptions);

        try
        {
            response.EnsureSuccessStatusCode();

            if (result == null || result.Description != ToWeaviateFriendlyClassDescription(collectionName))
            {
                throw new WeaviateMemoryException(WeaviateMemoryException.ErrorCodes.CollectionNameConflict,
                    $"Name conflict for collection: {collectionName} with class name: {className}");
            }

            this._log.LogTrace("Created collection: {0}, with class name: {1}", collectionName, className);
        }
        catch (HttpRequestException e)
        {
            throw new WeaviateMemoryException(WeaviateMemoryException.ErrorCodes.FailedToCreateCollection,
                $"Unable to create collection: {collectionName}, with class name: {className}", e);
        }
    }

    /// <inheritdoc />
    public async Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancel = default)
    {
        Verify.NotNullOrEmpty(collectionName, "Collection name is empty");

        string className = ToWeaviateFriendlyClassName(collectionName);
        this._log.LogTrace("Does collection exist: {0}, with class name: {1}:", collectionName, className);

        using HttpRequestMessage request = GetClassRequest.Create(className).Build();
        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancel).ConfigureAwait(false);

        // Needs to return a non-404 AND collection name should match
        bool exists = response.StatusCode != HttpStatusCode.NotFound;

        if (!exists)
        {
            this._log.LogTrace("Collection: {0}, with class name: {1}, does not exist.", collectionName, className);
        }
        else
        {
            GetClassResponse? existing = JsonSerializer.Deserialize<GetClassResponse>(responseContent, s_jsonSerializerOptions);
            if (existing != null && existing.Description != ToWeaviateFriendlyClassDescription(collectionName))
            {
                // ReSharper disable once CommentTypo
                // Check that we don't have an accidental conflict.
                // For example a collectionName of '__this_collection' and 'this_collection' are
                // both transformed to the class name of SKthiscollection - even though the external
                // system could consider them as unique collection names.
                if (existing.Description != ToWeaviateFriendlyClassDescription(collectionName))
                {
                    throw new WeaviateMemoryException(WeaviateMemoryException.ErrorCodes.CollectionNameConflict, $"Unable to verify existing collection: {collectionName} with class name: {className}");
                }
            }
        }

        return exists;
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> GetCollectionsAsync([EnumeratorCancellation] CancellationToken cancel = default)
    {
        this._log.LogTrace("Listing collections");

        using HttpRequestMessage request = GetSchemaRequest.Create().Build();
        (HttpResponseMessage _, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancel).ConfigureAwait(false);

        GetSchemaResponse? getSchemaResponse = JsonSerializer.Deserialize<GetSchemaResponse>(responseContent, s_jsonSerializerOptions);

        foreach (GetClassResponse? @class in getSchemaResponse!.Classes!
                     .Where(@class => IsPossibleSemanticKernelCollection(@class.Class!)))
        {
            yield return @class.Class!;
        }
    }

    /// <inheritdoc />
    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancel = default)
    {
        Verify.NotNullOrEmpty(collectionName, "Collection name is empty");

        if (await this.DoesCollectionExistAsync(collectionName, cancel).ConfigureAwait(false))
        {
            string className = ToWeaviateFriendlyClassName(collectionName);
            this._log.LogTrace("Deleting collection: {0}, with class name: {1}", collectionName, className);

            using HttpRequestMessage request = DeleteSchemaRequest.Create(className).Build();
            (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancel).ConfigureAwait(false);

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
    }

    /// <inheritdoc />
    public async Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancel = default)
    {
        Verify.NotNullOrEmpty(collectionName, "Collection name is empty");

        return await this.UpsertBatchAsync(collectionName, new[] { record }, cancel).FirstOrDefaultAsync(cancel).ConfigureAwait(false) ?? string.Empty;
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> records,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        Verify.NotNullOrEmpty(collectionName, "Collection name is empty");

        this._log.LogTrace("Upserting vectors");

        string className = ToWeaviateFriendlyClassName(collectionName);
        BatchRequest requestBuilder = BatchRequest.Create(className);
        foreach (MemoryRecord? record in records)
        {
            requestBuilder.Add(record);
        }

        using HttpRequestMessage request = requestBuilder.Build();
        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancel).ConfigureAwait(false);

        response.EnsureSuccessStatusCode();
        BatchResponse[]? result = JsonSerializer.Deserialize<BatchResponse[]>(responseContent, s_jsonSerializerOptions);
        foreach (BatchResponse batchResponse in result!)
        {
            yield return batchResponse.Id!;
        }
    }

    /// <inheritdoc />
    public async Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancel = default)
    {
        Verify.NotNullOrEmpty(collectionName, "Collection name is empty");
        Verify.NotNullOrEmpty(key, "Key is empty");

        using HttpRequestMessage request = new GetObjectRequest
        {
            Id = key,
            Additional = withEmbedding ? new[] { "vector" } : null
        }.Build();

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancel).ConfigureAwait(false);
        try
        {
            response.EnsureSuccessStatusCode();
        }
        catch (HttpRequestException e)
        {
            this._log.LogTrace("Request for vector failed {0}", e.Message);
            return null;
        }

        WeaviateObject? weaviateObject = JsonSerializer.Deserialize<WeaviateObject>(responseContent, s_jsonSerializerOptions);
        if (weaviateObject == null)
        {
            this._log.LogWarning("Unable to deserialize response to WeaviateObject");
            return null;
        }

        DateTimeOffset? timestamp = weaviateObject.Properties == null
            ? null
            : Convert.ToDateTime(weaviateObject.Properties["sk_timestamp"].ToString(), CultureInfo.InvariantCulture);

        MemoryRecord record = new(
            key: weaviateObject.Id!,
            timestamp: timestamp,
            embedding: new(weaviateObject.Vector ?? Array.Empty<float>()),
            metadata: ToMetadata(weaviateObject));

        this._log.LogTrace("Vector found with key: {0}", key);

        return record;
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys, bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        foreach (string? key in keys)
        {
            MemoryRecord? record = await this.GetAsync(collectionName, key, withEmbeddings, cancel).ConfigureAwait(false);
            if (record != null)
            {
                yield return record;
            }
            else
            {
                this._log.LogWarning("Unable to locate object with id: {0}", key);
            }
        }
    }

    /// <inheritdoc />
    public async Task RemoveAsync(string collectionName, string key, CancellationToken cancel = default)
    {
        Verify.NotNullOrEmpty(collectionName, "Collection name is empty");
        Verify.NotNull(key, "Key is NULL");

        string className = ToWeaviateFriendlyClassName(collectionName);
        this._log.LogTrace("Deleting vector with key: {0}, from collection {1}, with class name: {2}:", key, collectionName, className);

        DeleteObjectRequest requestBuilder = new()
        {
            Class = className,
            Id = key
        };
        using HttpRequestMessage request = requestBuilder.Build();

        (HttpResponseMessage response, string _) = await this.ExecuteHttpRequestAsync(request, cancel).ConfigureAwait(false);

        try
        {
            response.EnsureSuccessStatusCode();
            this._log.LogTrace("Vector deleted");
        }
        catch (HttpRequestException e)
        {
            this._log.LogError(e, "Vector delete request failed: {0}", e.Message);
        }
    }

    /// <inheritdoc />
    public async Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancel = default)
    {
        await Task.WhenAll(keys.Select(async k => await this.RemoveAsync(collectionName, k, cancel).ConfigureAwait(false))).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(
        string collectionName,
        Embedding<float> embedding,
        int limit,
        double minRelevanceScore = 0,
        bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        this._log.LogTrace("Searching top {0} nearest vectors", limit);
        Verify.NotNull(embedding, "The given vector is NULL");
        string className = ToWeaviateFriendlyClassName(collectionName);

        using HttpRequestMessage request = new GraphGetRequest
        {
            Class = className,
            Vector = embedding.Vector,
            Distance = minRelevanceScore,
            Limit = limit,
            WithVector = withEmbeddings
        }.Build();

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancel).ConfigureAwait(false);
        response.EnsureSuccessStatusCode();

        GraphResponse? data = JsonSerializer.Deserialize<GraphResponse>(responseContent, s_jsonSerializerOptions);

        if (data == null)
        {
            this._log.LogWarning("Unable to deserialize Search response");
            yield break;
        }

        List<(MemoryRecord, double)> result = new();
        JsonArray jsonArray = data.Data["Get"]![className]!.AsArray();

        // ReSharper disable once LoopCanBeConvertedToQuery
        foreach (JsonNode? json in jsonArray)
        {
            string id = json!["_additional"]!["id"]!.GetValue<string>();
            IEnumerable<float> floats = json["_additional"]!["vector"]!.AsArray().Select(a => a!.GetValue<float>());
            string text = json["sk_text"]!.GetValue<string>();
            string description = json["sk_description"]!.GetValue<string>();
            Embedding<float> vector = new(floats);
            string additionalMetadata = json["sk_additional_metadata"]!.GetValue<string>();
            string key = json["sk_id"]!.GetValue<string>();
            string timestamp = json["sk_timestamp"]!.GetValue<string>();

            MemoryRecord memoryRecord = MemoryRecord.LocalRecord(
                id,
                text,
                description,
                vector,
                additionalMetadata,
                key,
                Convert.ToDateTime(timestamp, CultureInfo.InvariantCulture));

            double distance = json["_additional"]!["distance"]!.GetValue<double>();

            result.Add((memoryRecord, distance));
        }

        foreach ((MemoryRecord, double) kv in result)
        {
            yield return kv;
        }
    }

    /// <inheritdoc />
    public async Task<(MemoryRecord, double)?> GetNearestMatchAsync(
        string collectionName,
        Embedding<float> embedding,
        double minRelevanceScore = 0,
        bool withEmbedding = false,
        CancellationToken cancel = default)
    {
        IAsyncEnumerable<(MemoryRecord, double)> results = this.GetNearestMatchesAsync(
            collectionName,
            embedding,
            minRelevanceScore: minRelevanceScore,
            limit: 1,
            withEmbeddings: withEmbedding,
            cancel: cancel);

        (MemoryRecord, double) record = await results.FirstOrDefaultAsync(cancel).ConfigureAwait(false);

        return (record.Item1, record.Item2);
    }

    // Get a class description, useful for checking name collisions
    private static string ToWeaviateFriendlyClassDescription(string collectionName)
    {
        return $"Semantic Kernel memory store for collection: {collectionName}";
    }

    // Convert a collectionName to a valid Weaviate class name
    private static string ToWeaviateFriendlyClassName(string collectionName)
    {
        // Prefix class names with SK to ensure proper case for Weaviate Classes
        return $"SK{s_classNameRegEx.Replace(collectionName, string.Empty)}";
    }

    // Check to see if a class name is possibly a semantic kernel collection
    private static bool IsPossibleSemanticKernelCollection(string collectionName)
    {
        if (!collectionName.StartsWith("SK", StringComparison.Ordinal))
        {
            return false;
        }

        string remainder = collectionName.Substring(2);
#pragma warning disable CA1308
        return remainder.Equals(remainder.ToLowerInvariant(), StringComparison.Ordinal);
#pragma warning restore CA1308
    }

    // Execute the HTTP request
    private async Task<(HttpResponseMessage response, string responseContent)> ExecuteHttpRequestAsync(
        HttpRequestMessage request,
        CancellationToken cancel = default)
    {
        HttpResponseMessage response = await this._httpClient.SendAsync(request, cancel).ConfigureAwait(false);
        string? responseContent = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
        this._log.LogTrace("Weaviate responded with {0}", response.StatusCode);
        return (response, responseContent);
    }

    private static MemoryRecordMetadata ToMetadata(WeaviateObject weaviateObject)
    {
        if (weaviateObject.Properties == null)
        {
#pragma warning disable CA2208
            throw new ArgumentNullException(nameof(weaviateObject.Properties));
#pragma warning restore CA2208
        }

        return new(
            false,
            string.Empty,
            weaviateObject.Properties["sk_id"].ToString(),
            weaviateObject.Properties["sk_description"].ToString(),
            weaviateObject.Properties["sk_text"].ToString(),
            weaviateObject.Properties["sk_additional_metadata"].ToString()
        );
    }

    protected virtual void Dispose(bool disposing)
    {
        if (this._disposed)
        {
            return;
        }

        if (disposing)
        {
            // Clean-up the HttpClient if we created it.
            if (this._isSelfManagedHttpClient)
            {
                this._httpClient.Dispose();
            }
        }

        this._disposed = true;
    }
}
