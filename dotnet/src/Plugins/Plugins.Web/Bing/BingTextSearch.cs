// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
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
/// A Bing Text Search implementation that can be used to perform searches using the Bing Web Search API.
/// </summary>
public sealed class BingTextSearch : ITextSearch<TextSearchResult>, ITextSearch<BingWebPage>, ITextSearch<string>
{
    /// <summary>
    /// Create an instance of the <see cref="BingTextSearch"/> with API key authentication.
    /// </summary>
    /// <param name="apiKey">The API key credential used to authenticate requests against the Search service.</param>
    /// <param name="options">Options used when creating this instance of <see cref="BingTextSearch"/>.</param>
    public BingTextSearch(string apiKey, BingTextSearchOptions? options = null)
    {
        Verify.NotNullOrWhiteSpace(apiKey);

        this._apiKey = apiKey;
        this._uri = new Uri(options?.Endpoint ?? DefaultUri);
        this._logger = options?.LoggerFactory?.CreateLogger(typeof(BingTextSearch)) ?? NullLogger.Instance;
        this._httpClient = options?.HttpClient ?? HttpClientProvider.GetHttpClient();
        this._httpClient.DefaultRequestHeaders.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
        this._httpClient.DefaultRequestHeaders.Add(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(typeof(BingTextSearch)));
        this._mapToString = options?.MapToString ?? DefaultMapToString;
        this._mapToTextSearchResult = options?.MapToTextSearchResult ?? DefaultMapToTextSearchResult;
    }

    /// <inheritdoc/>
    async Task<KernelSearchResults<TextSearchResult>> ITextSearch<TextSearchResult>.SearchAsync(string query, SearchOptions? searchOptions, CancellationToken cancellationToken)
    {
        BingSearchResponse<BingWebPage>? searchResponse = await this.ExecuteSearchAsync(query, searchOptions, cancellationToken).ConfigureAwait(false);

        return new KernelSearchResults<TextSearchResult>(searchResponse, this.GetResultsAsTextSearchResultAsync(searchResponse, cancellationToken), 1, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    async Task<KernelSearchResults<BingWebPage>> ITextSearch<BingWebPage>.SearchAsync(string query, SearchOptions? searchOptions, CancellationToken cancellationToken)
    {
        BingSearchResponse<BingWebPage>? searchResponse = await this.ExecuteSearchAsync(query, searchOptions, cancellationToken).ConfigureAwait(false);

        return new KernelSearchResults<BingWebPage>(searchResponse, this.GetResultsAsWebPageAsync(searchResponse, cancellationToken), 1, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    async Task<KernelSearchResults<string>> ITextSearch<string>.SearchAsync(string query, SearchOptions? searchOptions, CancellationToken cancellationToken)
    {
        BingSearchResponse<BingWebPage>? searchResponse = await this.ExecuteSearchAsync(query, searchOptions, cancellationToken).ConfigureAwait(false);

        return new KernelSearchResults<string>(searchResponse, this.GetResultsAsStringAsync(searchResponse, cancellationToken), 1, GetResultsMetadata(searchResponse));
    }

    #region private

    private readonly ILogger _logger;
    private readonly HttpClient _httpClient;
    private readonly string? _apiKey;
    private readonly Uri? _uri = null;
    private readonly MapBingWebPageToString _mapToString;
    private readonly MapBingWebPageToTextSearchResult _mapToTextSearchResult;

    private const string DefaultUri = "https://api.bing.microsoft.com/v7.0/search";

    /// <summary>
    /// Execute a Bing search query and return the results.
    /// </summary>
    /// <param name="query">What to search for.</param>
    /// <param name="searchSettings">Search options.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    private async Task<BingSearchResponse<BingWebPage>?> ExecuteSearchAsync(string query, SearchOptions? searchSettings = null, CancellationToken cancellationToken = default)
    {
        searchSettings ??= new SearchOptions();
        var count = searchSettings.Count;
        var offset = searchSettings.Offset;
        using HttpResponseMessage response = await this.SendGetRequestAsync(query, count, offset, cancellationToken).ConfigureAwait(false);

        this._logger.LogDebug("Response received: {StatusCode}", response.StatusCode);

        string json = await response.Content.ReadAsStringWithExceptionMappingAsync().ConfigureAwait(false);

        // Sensitive data, logging as trace, disabled by default
        this._logger.LogTrace("Response content received: {Data}", json);

        return JsonSerializer.Deserialize<BingSearchResponse<BingWebPage>>(json);
    }

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
    /// Return the search results as instances of <see cref="BingWebPage"/>.
    /// </summary>
    /// <param name="searchResponse">Response containing the web pages matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<BingWebPage> GetResultsAsWebPageAsync(BingSearchResponse<BingWebPage>? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
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
    /// Return the search results as instances of <see cref="TextSearchResult"/>.
    /// </summary>
    /// <param name="searchResponse">Response containing the web pages matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<TextSearchResult> GetResultsAsTextSearchResultAsync(BingSearchResponse<BingWebPage>? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse is null || searchResponse.WebPages is null || searchResponse.WebPages.Value is null)
        {
            yield break;
        }

        foreach (var webPage in searchResponse.WebPages.Value)
        {
            yield return this._mapToTextSearchResult(webPage);
            await Task.Yield();
        }
    }

    /// <summary>
    /// Return the search results as instances of <see cref="TextSearchResult"/>.
    /// </summary>
    /// <param name="searchResponse">Response containing the web pages matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<string> GetResultsAsStringAsync(BingSearchResponse<BingWebPage>? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse is null || searchResponse.WebPages is null || searchResponse.WebPages.Value is null)
        {
            yield break;
        }

        foreach (var webPage in searchResponse.WebPages.Value)
        {
            yield return this._mapToString(webPage);
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

    /// <summary>
    /// Default implementation which maps from a <see cref="BingWebPage"/> to a <see cref="string"/>
    /// </summary>
    private static string DefaultMapToString(BingWebPage webPage)
    {
        return webPage.Snippet ?? string.Empty;
    }

    /// <summary>
    /// Default implementation which maps from a <see cref="BingWebPage"/> to a <see cref="TextSearchResult"/>
    /// </summary>
    private static TextSearchResult DefaultMapToTextSearchResult(BingWebPage webPage)
    {
        return new TextSearchResult(webPage.Name, webPage.Snippet, webPage.Url, webPage);
    }

    #endregion
}
