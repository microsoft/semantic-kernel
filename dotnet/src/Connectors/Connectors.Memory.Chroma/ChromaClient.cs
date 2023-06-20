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
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Connectors.Memory.Chroma.Http.ApiSchema;

namespace Microsoft.SemanticKernel.Connectors.Memory.Chroma;

/// <summary>
/// An implementation of a client for the Chroma Vector DB. This class is used to
/// connect, create, delete, and get embeddings data from Chroma Vector DB instance.
/// </summary>
#pragma warning disable CA1001 // Types that own disposable fields should be disposable. Explanation - In this case, there is no need to dispose because either the NonDisposableHttpClientHandler or a custom HTTP client is being used.
public class ChromaClient : IChromaClient
#pragma warning restore CA1001 // Types that own disposable fields should be disposable. Explanation - In this case, there is no need to dispose because either the NonDisposableHttpClientHandler or a custom HTTP client is being used.
{
    public ChromaClient(string endpoint, ILogger? logger = null)
    {
        this._httpClient = new HttpClient(NonDisposableHttpClientHandler.Instance, disposeHandler: false);
        this._httpClient.BaseAddress = new Uri(endpoint);
        this._logger = logger ?? NullLogger<ChromaClient>.Instance;
    }

    public ChromaClient(HttpClient httpClient, string? endpoint = null, ILogger? logger = null)
    {
        if (string.IsNullOrEmpty(httpClient.BaseAddress?.AbsoluteUri) && string.IsNullOrEmpty(endpoint))
        {
            throw new AIException(
                AIException.ErrorCodes.InvalidConfiguration,
                "The HttpClient BaseAddress and endpoint are both null or empty. Please ensure at least one is provided.");
        }

        this._httpClient = httpClient;
        this._logger = logger ?? NullLogger<ChromaClient>.Instance;
    }

    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Creating collection {0}", collectionName);

        using var request = CreateCollectionRequest.Create(collectionName).Build();

        await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);
    }

    public async Task<ChromaCollectionModel?> GetCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Getting collection {0}", collectionName);

        using var request = GetCollectionRequest.Create(collectionName).Build();

        try
        {
            (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);

            var collection = JsonSerializer.Deserialize<ChromaCollectionModel>(responseContent);

            return collection;
        }
        catch (ChromaClientException e) when (e.CollectionDoesNotExistException(collectionName))
        {
            this._logger.LogError("Collection {0} does not exist", collectionName);

            return null;
        }
    }

    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Deleting collection {0}", collectionName);

        using var request = DeleteCollectionRequest.Create(collectionName).Build();

        await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);
    }

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

    #region private ================================================================================

    private const string ApiRoute = "api/v1/";

    private readonly ILogger _logger;
    private readonly HttpClient _httpClient;
    private readonly Uri? _endpoint = null;

    private async Task<(HttpResponseMessage response, string responseContent)> ExecuteHttpRequestAsync(
        HttpRequestMessage request,
        CancellationToken cancellationToken = default)
    {
        string endpoint = this._endpoint?.ToString() ?? this._httpClient.BaseAddress.ToString();
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
            throw new ChromaClientException($"{request.Method.Method} {operationName} operation failed: {e.Message}, {responseContent}", e);
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
