// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Plugins.Web.Brave;

/// <summary>
/// A Brave Text Search implementation that can be used to perform searches using the Brave Web Search API.
/// </summary>
public sealed class BraveTextSearch : ITextSearch
{
    /// <summary>
    /// Create an instance of the <see cref="BraveTextSearch"/> with API key authentication.
    /// </summary>
    /// <param name="apiKey">The API key credential used to authenticate requests against the Search service.</param>
    /// <param name="options">Options used when creating this instance of <see cref="BraveTextSearch"/>.</param>
    public BraveTextSearch(string apiKey, BraveTextSearchOptions? options = null)
    {
        Verify.NotNullOrWhiteSpace(apiKey);

        this._apiKey = apiKey;
        this._uri = options?.Endpoint ?? new Uri(DefaultUri);
        this._logger = options?.LoggerFactory?.CreateLogger(typeof(BraveTextSearch)) ?? NullLogger.Instance;

        this._httpClient = options?.HttpClient ?? HttpClientProvider.GetHttpClient();

        this._httpClient.DefaultRequestHeaders.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
        this._httpClient.DefaultRequestHeaders.Add(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(typeof(BraveTextSearch)));

        this._stringMapper = options?.StringMapper ?? s_defaultStringMapper;
        this._resultMapper = options?.ResultMapper ?? s_defaultResultMapper;
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<string>> SearchAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = new CancellationToken())
    {
        searchOptions ??= new TextSearchOptions();
        BraveSearchResponse<BraveWebResult>? searchResponse = await this.ExecuteSearchAsync(query, searchOptions, cancellationToken).ConfigureAwait(false);

        long? totalCount = searchOptions.IncludeTotalCount ? searchResponse?.Web?.Results.Count : null;

        return new KernelSearchResults<string>(this.GetResultsAsStringAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<TextSearchResult>> GetTextSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = new CancellationToken())
    {
        searchOptions ??= new TextSearchOptions();
        BraveSearchResponse<BraveWebResult>? searchResponse = await this.ExecuteSearchAsync(query, searchOptions, cancellationToken).ConfigureAwait(false);

        long? totalCount = searchOptions.IncludeTotalCount ? searchResponse?.Web?.Results.Count : null;

        return new KernelSearchResults<TextSearchResult>(this.GetResultsAsTextSearchResultAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<object>> GetSearchResultsAsync(string query, TextSearchOptions? searchOptions = null,
        CancellationToken cancellationToken = new CancellationToken())
    {
        searchOptions ??= new TextSearchOptions();
        BraveSearchResponse<BraveWebResult>?  searchResponse = await this.ExecuteSearchAsync(query, searchOptions, cancellationToken).ConfigureAwait(false);

        long? totalCount = searchOptions.IncludeTotalCount ? searchResponse?.Web?.Results.Count : null;

        return new KernelSearchResults<object>(this.GetResultsAsWebPageAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    #region private

    private readonly ILogger _logger;
    private readonly HttpClient _httpClient;
    private readonly string? _apiKey;
    private readonly Uri? _uri = null;
    private readonly ITextSearchStringMapper _stringMapper;
    private readonly ITextSearchResultMapper _resultMapper;

    private static readonly ITextSearchStringMapper s_defaultStringMapper = new DefaultTextSearchStringMapper();
    private static readonly ITextSearchResultMapper s_defaultResultMapper = new DefaultTextSearchResultMapper();

    // See https://api-dashboard.search.brave.com/app/documentation/web-search/query#WebSearchAPIQueryParameters
    private static readonly string[] s_queryParameters = ["country", "search_lang","ui_lang",  "safesearch", "freshness","text_decorations" , "spellcheck","result_filter","googles","units" ,"extra_snippets","summary"];

    private const string DefaultUri = "https://api.search.brave.com/res/v1/web/search";

    /// <summary>
    /// Execute a Bing search query and return the results.
    /// </summary>
    /// <param name="query">What to search for.</param>
    /// <param name="searchOptions">Search options.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    private async Task<BraveSearchResponse<BraveWebResult>?> ExecuteSearchAsync(string query, TextSearchOptions searchOptions, CancellationToken cancellationToken = default)
    {
        using HttpResponseMessage response = await this.SendGetRequestAsync(query, searchOptions, cancellationToken).ConfigureAwait(false);

        this._logger.LogDebug("Response received: {StatusCode}", response.StatusCode);

        string json = await response.Content.ReadAsStringWithExceptionMappingAsync(cancellationToken).ConfigureAwait(false);

        // Sensitive data, logging as trace, disabled by default
        this._logger.LogTrace("Response content received: {Data}", json);

        return JsonSerializer.Deserialize<BraveSearchResponse<BraveWebResult>>(json);
    }

    /// <summary>
    /// Sends a GET request to the specified URI.
    /// </summary>
    /// <param name="query">The query string.</param>
    /// <param name="searchOptions">The search options.</param>
    /// <param name="cancellationToken">A cancellation token to cancel the request.</param>
    /// <returns>A <see cref="HttpResponseMessage"/> representing the response from the request.</returns>
    private async Task<HttpResponseMessage> SendGetRequestAsync(string query, TextSearchOptions searchOptions, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(query) ;

        if (searchOptions.Top is <= 0 or >= 21)
        {
            throw new ArgumentOutOfRangeException(nameof(searchOptions), searchOptions.Top, $"{nameof(searchOptions.Top)} value must be greater than 0 and less than 21.");
        }

        if (searchOptions.Skip is < 0 or > 10)
        {
            throw new ArgumentOutOfRangeException(nameof(searchOptions),searchOptions.Skip, $"{nameof(searchOptions.Skip)} value must be equal or greater than 0 and less than 10.");
        }

        Uri uri = new($"{this._uri}?q={BuildQuery(query, searchOptions)}");

        using var httpRequestMessage = new HttpRequestMessage(HttpMethod.Get, uri);

        if (!string.IsNullOrEmpty(this._apiKey))
        {
            httpRequestMessage.Headers.Add("X-Subscription-Token", this._apiKey);
        }

        return await this._httpClient.SendWithSuccessCheckAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Return the search results as instances of <see cref="BraveWebResult"/>.
    /// </summary>
    /// <param name="searchResponse">Response containing the web pages matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<object> GetResultsAsWebPageAsync(BraveSearchResponse<BraveWebResult>? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse is null ||  searchResponse.Web  is null ||  searchResponse.Web.Results is []  )
        {
            yield break;
        }

        foreach (var webPage in searchResponse.Web.Results)
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
    private async IAsyncEnumerable<TextSearchResult> GetResultsAsTextSearchResultAsync(BraveSearchResponse<BraveWebResult>? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse is null || searchResponse.Web  is null ||  searchResponse.Web.Results is []  )
        {
            yield break;
        }

        foreach (var webPage in searchResponse.Web.Results)
        {
            yield return this._resultMapper.MapFromResultToTextSearchResult(webPage);
            await Task.Yield();
        }
    }

    /// <summary>
    /// Return the search results as instances of <see cref="TextSearchResult"/>.
    /// </summary>
    /// <param name="searchResponse">Response containing the web pages matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<string> GetResultsAsStringAsync(BraveSearchResponse<BraveWebResult>? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse is null || searchResponse.Web is null || searchResponse.Web.Results is [])
        {
            yield break;
        }

        foreach (var webPage in searchResponse.Web.Results)
        {
            yield return this._stringMapper.MapFromResultToString(webPage);
            await Task.Yield();
        }
    }

    /// <summary>
    /// Return the result's metadata.
    /// </summary>
    /// <param name="searchResponse">Response containing the documents matching the query.</param>
    private static Dictionary<string, object?>? GetResultsMetadata(BraveSearchResponse<BraveWebResult>? searchResponse)
    {
        return new Dictionary<string, object?>()
        {
            {"OriginalQuery",searchResponse?.Query?.Original},
            {"AlteredQuery",searchResponse?.Query?.Altered },
            {"IsSafeSearchEnable",searchResponse?.Query?.IsSafeSearchEnable}
        };
    }

    /// <summary>
    /// Default implementation which maps from a <see cref="BraveWebResult"/> to a <see cref="string"/>
    /// </summary>
    private sealed class DefaultTextSearchStringMapper : ITextSearchStringMapper
    {
        /// <inheritdoc />
        public string MapFromResultToString(object result)
        {
            if (result is not BraveWebResult webPage)
            {
                throw new ArgumentException("Result must be a BraveWebResult", nameof(result));
            }

            return webPage.Description ?? string.Empty;
        }
    }

    /// <summary>
    /// Default implementation which maps from a <see cref="BraveWebResult"/> to a <see cref="TextSearchResult"/>
    /// </summary>
    private sealed class DefaultTextSearchResultMapper : ITextSearchResultMapper
    {
        /// <inheritdoc />
        public TextSearchResult MapFromResultToTextSearchResult(object result)
        {
            if (result is not BraveWebResult webPage)
            {
                throw new ArgumentException("Result must be a BraveWebResult", nameof(result));
            }

            return new TextSearchResult(webPage.Description ?? string.Empty) { Name = webPage.Title, Link = webPage.Url };
        }
    }

    /// <summary>
    /// Build a query string from the <see cref="TextSearchOptions"/>
    /// </summary>
    /// <param name="query">The query.</param>
    /// <param name="searchOptions">The search options.</param>
    private static string BuildQuery(string query, TextSearchOptions searchOptions)
    {
        StringBuilder fullQuery = new();
        fullQuery.Append(Uri.EscapeDataString(query.Trim()));
        StringBuilder queryParams = new();
        if (searchOptions.Filter is not null)
        {
            var filterClauses = searchOptions.Filter.FilterClauses;

            foreach (var filterClause in filterClauses)
            {
                if (filterClause is EqualToFilterClause equalityFilterClause)
                {
                    // if (s_advancedSearchKeywords.Contains(equalityFilterClause.FieldName, StringComparer.OrdinalIgnoreCase) && equalityFilterClause.Value is not null)
                    // {
                    //     fullQuery.Append($"+{equalityFilterClause.FieldName}%3A").Append(Uri.EscapeDataString(equalityFilterClause.Value.ToString()!));
                    // }
                    if (s_queryParameters.Contains(equalityFilterClause.FieldName, StringComparer.OrdinalIgnoreCase) && equalityFilterClause.Value is not null)
                    {
                        string? queryParam = s_queryParameters.FirstOrDefault(s => s.Equals(equalityFilterClause.FieldName, StringComparison.OrdinalIgnoreCase));
                        queryParams.Append('&').Append(queryParam!).Append('=').Append(Uri.EscapeDataString(equalityFilterClause.Value.ToString()!));
                    }
                    else
                    {
                        throw new ArgumentException($"Unknown equality filter clause field name '{equalityFilterClause.FieldName}', must be one of {string.Join(",", s_queryParameters)}", nameof(searchOptions));
                    }
                }
            }
        }

        fullQuery.Append($"&count={searchOptions.Top}&offset={searchOptions.Skip}{queryParams}");

        return fullQuery.ToString();
    }

    #endregion
}
