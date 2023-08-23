// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Connectors.Memory.Chroma.Http.ApiSchema;
using Microsoft.SemanticKernel.Connectors.Memory.Chroma.Http.ApiSchema.Internal;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.Memory.Chroma;

/// <summary>
/// An implementation of a client for the Chroma Vector DB. This class is used to
/// create, delete, and get embeddings data from Chroma Vector DB instance.
/// </summary>
#pragma warning disable CA1001 // Types that own disposable fields should be disposable. Explanation - In this case, there is no need to dispose because either the NonDisposableHttpClientHandler or a custom HTTP client is being used.
public class ChromaClient : IChromaClient
#pragma warning restore CA1001 // Types that own disposable fields should be disposable. Explanation - In this case, there is no need to dispose because either the NonDisposableHttpClientHandler or a custom HTTP client is being used.
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ChromaClient"/> class.
    /// </summary>
    /// <param name="endpoint">Chroma server endpoint URL.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public ChromaClient(string endpoint, ILoggerFactory? loggerFactory = null)
    {
        this._httpClient = new HttpClient(NonDisposableHttpClientHandler.Instance, disposeHandler: false);
        this._endpoint = endpoint;
        this._logger = loggerFactory is not null ? loggerFactory.CreateLogger(nameof(ChromaClient)) : NullLogger.Instance;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChromaClient"/> class.
    /// </summary>
    /// <param name="httpClient">The <see cref="HttpClient"/> instance used for making HTTP requests.</param>
    /// <param name="endpoint">Chroma server endpoint URL.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <exception cref="SKException">Occurs when <see cref="HttpClient"/> doesn't have base address and endpoint parameter is not provided.</exception>
    public ChromaClient(HttpClient httpClient, string? endpoint = null, ILoggerFactory? loggerFactory = null)
    {
        if (string.IsNullOrEmpty(httpClient.BaseAddress?.AbsoluteUri) && string.IsNullOrEmpty(endpoint))
        {
            throw new SKException("The HttpClient BaseAddress and endpoint are both null or empty. Please ensure at least one is provided.");
        }

        this._httpClient = httpClient;
        this._endpoint = endpoint;
        this._logger = loggerFactory is not null ? loggerFactory.CreateLogger(nameof(ChromaClient)) : NullLogger.Instance;
    }

    /// <inheritdoc />
    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Creating collection {0}", collectionName);

        using var request = CreateCollectionRequest.Create(collectionName).Build();

        await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task<ChromaCollectionModel?> GetCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Getting collection {0}", collectionName);

        using var request = GetCollectionRequest.Create(collectionName).Build();

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);

        var collection = JsonSerializer.Deserialize<ChromaCollectionModel>(responseContent);

        return collection;
    }

    /// <inheritdoc />
    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Deleting collection {0}", collectionName);

        using var request = DeleteCollectionRequest.Create(collectionName).Build();

        await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> ListCollectionsAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Listing collections");

        using var request = ListCollectionsRequest.Create().Build();

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);

        var collections = JsonSerializer.Deserialize<List<ChromaCollectionModel>>(responseContent);

        foreach (var collection in collections!)
        {
            yield return collection.Name;
        }
    }

    /// <inheritdoc />
    public async Task UpsertEmbeddingsAsync(string collectionId, string[] ids, ReadOnlyMemory<float>[] embeddings, object[]? metadatas = null, CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Upserting embeddings to collection with id: {0}", collectionId);

        using var request = UpsertEmbeddingsRequest.Create(collectionId, ids, embeddings, metadatas).Build();

        await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task<ChromaEmbeddingsModel> GetEmbeddingsAsync(string collectionId, string[] ids, string[]? include = null, CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Getting embeddings from collection with id: {0}", collectionId);

        using var request = GetEmbeddingsRequest.Create(collectionId, ids, include).Build();

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);

        var embeddings = JsonSerializer.Deserialize<ChromaEmbeddingsModel>(responseContent);

        return embeddings ?? new ChromaEmbeddingsModel();
    }

    /// <inheritdoc />
    public async Task DeleteEmbeddingsAsync(string collectionId, string[] ids, CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Deleting embeddings from collection with id: {0}", collectionId);

        using var request = DeleteEmbeddingsRequest.Create(collectionId, ids).Build();

        await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task<ChromaQueryResultModel> QueryEmbeddingsAsync(string collectionId, ReadOnlyMemory<float>[] queryEmbeddings, int nResults, string[]? include = null, CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Query embeddings in collection with id: {0}", collectionId);

        using var request = QueryEmbeddingsRequest.Create(collectionId, queryEmbeddings, nResults, include).Build();

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);

        var queryResult = JsonSerializer.Deserialize<ChromaQueryResultModel>(responseContent);

        return queryResult ?? new ChromaQueryResultModel();
    }

    #region private ================================================================================

    private const string ApiRoute = "api/v1/";

    private readonly ILogger _logger;
    private readonly HttpClient _httpClient;
    private readonly string? _endpoint = null;

    private async Task<(HttpResponseMessage response, string responseContent)> ExecuteHttpRequestAsync(
        HttpRequestMessage request,
        CancellationToken cancellationToken = default)
    {
        string endpoint = this._endpoint ?? this._httpClient.BaseAddress.ToString();
        endpoint = this.SanitizeEndpoint(endpoint);

        string operationName = request.RequestUri.ToString();

        request.RequestUri = new Uri(new Uri(endpoint), operationName);

        HttpResponseMessage response = await this._httpClient.SendAsync(request, cancellationToken).ConfigureAwait(false);

        string responseContent = await response.Content.ReadAsStringAsync().ConfigureAwait(false);

        try
        {
            response.EnsureSuccessStatusCode();
        }
        catch (HttpRequestException e)
        {
            this._logger.LogError(e, "{0} {1} operation failed: {2}, {3}", request.Method.Method, operationName, e.Message, responseContent);
            throw new SKException($"{request.Method.Method} {operationName} operation failed: {e.Message}, {responseContent}", e);
        }

        return (response, responseContent);
    }

    private string SanitizeEndpoint(string endpoint)
    {
        StringBuilder builder = new(endpoint);

        if (!endpoint.EndsWith("/", StringComparison.Ordinal))
        {
            builder.Append('/');
        }

        builder.Append(ApiRoute);

        return builder.ToString();
    }

    #endregion
}
