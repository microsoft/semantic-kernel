// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Search;

namespace Microsoft.SemanticKernel.Plugins.Web.Bing;

/// <summary>
/// A Bing Search service that creates and recalls memories associated with text.
/// </summary>
public sealed class BingTextSearchService : ITextSearchService
{
    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes { get; }

    /// <summary>
    /// Create an instance of the <see cref="BingTextSearchService"/> connector with API key authentication.
    /// </summary>
    /// <param name="endpoint">Required. The URI endpoint of the Bing search service. The URI must use HTTPS.</param>
    /// <param name="apiKey">Required. The API key credential used to authenticate requests against the Search service.</param>
    /// <param name="httpClient">The HTTP client to use for making requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public BingTextSearchService(string endpoint, string apiKey, HttpClient? httpClient = null, ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(apiKey);

        this._uri = new Uri(endpoint ?? DefaultUri);
        this._apiKey = apiKey;
        this._logger = loggerFactory?.CreateLogger(typeof(BingTextSearchService)) ?? NullLogger.Instance;
        this._httpClient = httpClient ?? HttpClientProvider.GetHttpClient();
        this._httpClient.DefaultRequestHeaders.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
        this._httpClient.DefaultRequestHeaders.Add(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(typeof(BingTextSearchService)));

        this.Attributes = new Dictionary<string, object?>();
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<T>> SearchAsync<T>(string query, SearchExecutionSettings? searchSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default) where T : class
    {
        searchSettings ??= new SearchExecutionSettings();
        var count = searchSettings.Count;
        var offset = searchSettings.Offset;
        using HttpResponseMessage response = await this.SendGetRequestAsync(query, count, offset, cancellationToken).ConfigureAwait(false);

        this._logger.LogDebug("Response received: {StatusCode}", response.StatusCode);

        string json = await response.Content.ReadAsStringWithExceptionMappingAsync().ConfigureAwait(false);

        // Sensitive data, logging as trace, disabled by default
        this._logger.LogTrace("Response content received: {Data}", json);

        BingSearchResponse<T>? searchResponse = null;
        if (typeof(T) == typeof(string))
        {
            var webPages = JsonSerializer.Deserialize<BingSearchResponse<BingWebPage>>(json);
            if (webPages is not null && webPages.WebPages is not null)
            {
                searchResponse = new BingSearchResponse<T>()
                {
                    Type = webPages.Type,
                    QueryContext = webPages.QueryContext,
                    WebPages = new BingWebPages<T>()
                    {
                        Id = webPages.WebPages.Id,
                        SomeResultsRemoved = webPages.WebPages.SomeResultsRemoved,
                        TotalEstimatedMatches = webPages.WebPages.TotalEstimatedMatches,
                        Value = webPages?.WebPages?.Value?.Select(x => x.Snippet).ToList() as List<T> ?? [],
                    },
                };
            }
        }
        else if (typeof(T) == typeof(TextSearchResult))
        {
            var webPages = JsonSerializer.Deserialize<BingSearchResponse<BingWebPage>>(json);
            if (webPages is not null && webPages.WebPages is not null)
            {
                searchResponse = new BingSearchResponse<T>()
                {
                    Type = webPages.Type,
                    QueryContext = webPages.QueryContext,
                    WebPages = new BingWebPages<T>()
                    {
                        Id = webPages.WebPages.Id,
                        SomeResultsRemoved = webPages.WebPages.SomeResultsRemoved,
                        TotalEstimatedMatches = webPages.WebPages.TotalEstimatedMatches,
                        Value = webPages?.WebPages?.Value?.Select(x => new TextSearchResult(x.Name, x.Snippet, x.Url, x)).ToList() as List<T> ?? [],
                    },
                };
            }
        }
        else
        {
            searchResponse = JsonSerializer.Deserialize<BingSearchResponse<T>>(json);
        }

        return new KernelSearchResults<T>(searchResponse, this.GetResultsAsync(searchResponse, cancellationToken), 1, GetResultsMetadata(searchResponse));
    }

    #region private

    private readonly ILogger _logger;
    private readonly HttpClient _httpClient;
    private readonly string? _apiKey;
    private readonly Uri? _uri = null;

    private const string DefaultUri = "https://api.bing.microsoft.com/v7.0/search";

    /// <summary>
    /// Sends a GET request to the specified URI.
    /// </summary>
    /// <param name="query">The query string.</param>
    /// <param name="count">The number of results to return.</param>
    /// <param name="offset">The index of the first result to return.</param>
    /// <param name="cancellationToken">A cancellation token to cancel the request.</param>
    /// <returns>A <see cref="HttpResponseMessage"/> representing the response from the request.</returns>
    private async Task<HttpResponseMessage> SendGetRequestAsync(string query, int count = 1, int offset = 0, CancellationToken cancellationToken = default)
    {
        if (count is <= 0 or >= 50)
        {
            throw new ArgumentOutOfRangeException(nameof(count), count, $"{nameof(count)} value must be greater than 0 and less than 50.");
        }

        Uri uri = new($"{this._uri}?q={Uri.EscapeDataString(query.Trim())}&count={count}&offset={offset}");

        using var httpRequestMessage = new HttpRequestMessage(HttpMethod.Get, uri);

        if (!string.IsNullOrEmpty(this._apiKey))
        {
            httpRequestMessage.Headers.Add("Ocp-Apim-Subscription-Key", this._apiKey);
        }

        return await this._httpClient.SendWithSuccessCheckAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Return the search results.
    /// </summary>
    /// <typeparam name="T">The .NET type that maps to the index schema. Instances of this type
    /// can be retrieved as documents from the index.</typeparam>
    /// <param name="searchResponse">Response containing the web pages matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<T> GetResultsAsync<T>(BingSearchResponse<T>? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken) where T : class
    {
        if (searchResponse is null || searchResponse.WebPages is null || searchResponse.WebPages.Value is null)
        {
            yield break;
        }

        foreach (var webPage in searchResponse.WebPages.Value)
        {
            yield return webPage;
            await Task.Yield();
        }
    }

    /// <summary>
    /// Return the results metadata.
    /// </summary>
    /// <typeparam name="T">The .NET type that maps to the index schema. Instances of this type
    /// can be retrieved as documents from the index.</typeparam>
    /// <param name="searchResponse">Response containing the documents matching the query.</param>
    private static Dictionary<string, object?>? GetResultsMetadata<T>(BingSearchResponse<T>? searchResponse) where T : class
    {
        return new Dictionary<string, object?>()
        {
            { "AlteredQuery", searchResponse?.QueryContext?.AlteredQuery },
        };
    }
    #endregion
}
