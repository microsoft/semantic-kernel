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
        BraveSearchResponse<BraveWebResult>? searchResponse = await this.ExecuteSearchAsync(query, searchOptions, cancellationToken).ConfigureAwait(false);

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
    private static readonly string[] s_queryParameters = ["country", "search_lang", "ui_lang", "safesearch", "text_decorations", "spellcheck", "result_filter", "units", "extra_snippets"];

    private static readonly string[] s_safeSearch = ["off", "moderate", "strict"];

    private static readonly string[] s_resultFilter = ["discussions", "faq", "infobox", "news", "query", "summarizer", "videos", "web", "locations"];

    // See https://api-dashboard.search.brave.com/app/documentation/web-search/codes
    private static readonly string[] s_countryCodes = ["ALL", "AR", "AU", "AT", "BE", "BR", "CA", "CL", "DK", "FI", "FR", "DE", "HK", "IN", "ID", "IT", "JP", "KR", "MY", "MX", "NL", "NZ", "NO", "CN", "PL", "PT", "PH", "RU", "SA", "ZA", "ES", "SE", "CH", "TW", "TR", "GB", "US"];

    private static readonly string[] s_searchLang = ["ar", "eu", "bn", "bg", "ca", "zh-hans", "zh-hant", "hr", "cs", "da", "nl", "en", "en-gb", "et", "fi", "fr", "gl", "de", "gu", "he", "hi", "hu", "is", "it", "jp", "kn", "ko", "lv", "lt", "ms", "ml", "mr", "nb", "pl", "pt-br", "pt-pt", "pa", "ro", "ru", "sr", "sk", "sl", "es", "sv", "ta", "te", "th", "tr", "uk", "vi"];

    private static readonly string[] s_uiCode = ["es-AR", "en-AU", "de-AT", "nl-BE", "fr-BE", "pt-BR", "en-CA", "fr-CA", "es-CL", "da-DK", "fi-FI", "fr-FR", "de-DE", "zh-HK", "en-IN", "en-ID", "it-IT", "ja-JP", "ko-KR", "en-MY", "es-MX", "nl-NL", "en-NZ", "no-NO", "zh-CN", "pl-PL", "en-PH", "ru-RU", "en-ZA", "es-ES", "sv-SE", "fr-CH", "de-CH", "zh-TW", "tr-TR", "en-GB", "en-US", "es-US"];

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
        Verify.NotNull(query);

        if (searchOptions.Top is <= 0 or >= 21)
        {
            throw new ArgumentOutOfRangeException(nameof(searchOptions), searchOptions.Top, $"{nameof(searchOptions.Top)} value must be greater than 0 and less than 21.");
        }

        if (searchOptions.Skip is < 0 or > 10)
        {
            throw new ArgumentOutOfRangeException(nameof(searchOptions), searchOptions.Skip, $"{nameof(searchOptions.Skip)} value must be equal or greater than 0 and less than 10.");
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
        if (searchResponse is null) { yield break; }

        if (searchResponse.Web?.Results is { Count: > 0 } webResults)
        {
            foreach (var webPage in webResults)
            {
                yield return webPage;
                await Task.Yield();
            }
        }
    }

    /// <summary>
    /// Return the search results as instances of <see cref="TextSearchResult"/>.
    /// </summary>
    /// <param name="searchResponse">Response containing the web pages matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<TextSearchResult> GetResultsAsTextSearchResultAsync(BraveSearchResponse<BraveWebResult>? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse is null)
        { yield break; }

        if (searchResponse.Web?.Results is { Count: > 0 } webResults)
        {
            foreach (var webPage in webResults)
            {
                yield return this._resultMapper.MapFromResultToTextSearchResult(webPage);
                await Task.Yield();
            }
        }
    }

    /// <summary>
    /// Return the search results as instances of <see cref="TextSearchResult"/>.
    /// </summary>
    /// <param name="searchResponse">Response containing the web pages matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<string> GetResultsAsStringAsync(BraveSearchResponse<BraveWebResult>? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse is null)
        { yield break; }

        if (searchResponse.Web?.Results is { Count: > 0 } webResults)
        {
            foreach (var webPage in webResults)
            {
                yield return this._stringMapper.MapFromResultToString(webPage);
                await Task.Yield();
            }
        }

        if (searchResponse.News?.Results is { Count: > 0 } newsResults)
        {
            foreach (var newsPage in newsResults)
            {
                yield return this._stringMapper.MapFromResultToString(newsPage);
                await Task.Yield();
            }
        }

        if (searchResponse.Videos?.Results is { Count: > 0 } videoResults)
        {
            foreach (var videoPage in videoResults)
            {
                yield return this._stringMapper.MapFromResultToString(videoPage);
                await Task.Yield();
            }
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
            {"IsSafeSearchEnable",searchResponse?.Query?.IsSafeSearchEnable},
            {"IsSpellCheckOff",searchResponse?.Query?.SpellcheckOff  }
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
                    if (s_queryParameters.Contains(equalityFilterClause.FieldName, StringComparer.OrdinalIgnoreCase) && equalityFilterClause.Value is not null)
                    {
                        string queryParam = s_queryParameters.FirstOrDefault(s => s.Equals(equalityFilterClause.FieldName, StringComparison.OrdinalIgnoreCase))!;

                        CheckQueryValidation(queryParam, equalityFilterClause.Value);

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

    /// <summary>
    /// Validate weather the provide value is acceptable or not
    /// </summary>
    /// <param name="queryParam"></param>
    /// <param name="value"></param>
    private static void CheckQueryValidation(string queryParam, object value)
    {
        switch (queryParam)
        {
            case "country":
                if (value is not string strCountry || !s_countryCodes.Contains(strCountry))
                { throw new ArgumentException($"Country Code must be one of {string.Join(",", s_countryCodes)}", nameof(value)); }
                break;

            case "search_lang":
                if (value is not string strLang || !s_searchLang.Contains(strLang))
                { throw new ArgumentException($"Search Language must be one of {string.Join(",", s_searchLang)}", nameof(value)); }
                break;

            case "ui_lang":
                if (value is not string strUi || !s_uiCode.Contains(strUi))
                { throw new ArgumentException($"UI Language must be one of {string.Join(",", s_uiCode)}", nameof(value)); }
                break;

            case "safesearch":
                if (value is not string safe || !s_safeSearch.Contains(safe))
                { throw new ArgumentException($"SafeSearch allows only: {string.Join(",", s_safeSearch)}", nameof(value)); }
                break;

            case "text_decorations":
                if (value is not bool)
                { throw new ArgumentException("Text Decorations must be of type bool", nameof(value)); }
                break;

            case "spellcheck":
                if (value is not bool)
                { throw new ArgumentException("SpellCheck must be of type bool", nameof(value)); }
                break;

            case "result_filter":
                if (value is string filterStr)
                {
                    var filters = filterStr.Split([","], StringSplitOptions.RemoveEmptyEntries);
                    if (filters.Any(f => !s_resultFilter.Contains(f)))
                    { throw new ArgumentException($"Result Filter allows only: {string.Join(",", s_resultFilter)}", nameof(value)); }
                }
                break;

            case "units":
                if (value is not string strUnit || strUnit is not ("metric" or "imperial"))
                { throw new ArgumentException("Units can only be `metric` or `imperial`", nameof(value)); }
                break;

            case "extra_snippets":
                if (value is not bool)
                { throw new ArgumentException("Extra Snippets must be of type bool", nameof(value)); }
                break;
        }
    }
    #endregion
}
