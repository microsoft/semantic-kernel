// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;
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

namespace Microsoft.SemanticKernel.Plugins.Web.Bing;

/// <summary>
/// A Bing Text Search implementation that can be used to perform searches using the Bing Web Search API.
/// </summary>
#pragma warning disable CS0618 // ITextSearch is obsolete - this class provides backward compatibility
public sealed class BingTextSearch : ITextSearch, ITextSearch<BingWebPage>
#pragma warning restore CS0618
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
        this._uri = options?.Endpoint ?? new Uri(DefaultUri);
        this._logger = options?.LoggerFactory?.CreateLogger(typeof(BingTextSearch)) ?? NullLogger.Instance;
        this._httpClient = options?.HttpClient ?? HttpClientProvider.GetHttpClient();
        this._httpClient.DefaultRequestHeaders.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
        this._httpClient.DefaultRequestHeaders.Add(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(typeof(BingTextSearch)));
        this._stringMapper = options?.StringMapper ?? s_defaultStringMapper;
        this._resultMapper = options?.ResultMapper ?? s_defaultResultMapper;
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<string>> SearchAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        searchOptions ??= new TextSearchOptions();
        BingSearchResponse<BingWebPage>? searchResponse = await this.ExecuteSearchAsync(query, searchOptions, cancellationToken).ConfigureAwait(false);

        long? totalCount = searchOptions.IncludeTotalCount ? searchResponse?.WebPages?.TotalEstimatedMatches : null;

        return new KernelSearchResults<string>(this.GetResultsAsStringAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<TextSearchResult>> GetTextSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        searchOptions ??= new TextSearchOptions();
        BingSearchResponse<BingWebPage>? searchResponse = await this.ExecuteSearchAsync(query, searchOptions, cancellationToken).ConfigureAwait(false);

        long? totalCount = searchOptions.IncludeTotalCount ? searchResponse?.WebPages?.TotalEstimatedMatches : null;

        return new KernelSearchResults<TextSearchResult>(this.GetResultsAsTextSearchResultAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<object>> GetSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        searchOptions ??= new TextSearchOptions();
        BingSearchResponse<BingWebPage>? searchResponse = await this.ExecuteSearchAsync(query, searchOptions, cancellationToken).ConfigureAwait(false);

        long? totalCount = searchOptions.IncludeTotalCount ? searchResponse?.WebPages?.TotalEstimatedMatches : null;

        return new KernelSearchResults<object>(this.GetResultsAsWebPageAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    Task<KernelSearchResults<string>> ITextSearch<BingWebPage>.SearchAsync(string query, TextSearchOptions<BingWebPage>? searchOptions, CancellationToken cancellationToken)
    {
        var legacyOptions = searchOptions != null ? ConvertToLegacyOptions(searchOptions) : new TextSearchOptions();
        return this.SearchAsync(query, legacyOptions, cancellationToken);
    }

    /// <inheritdoc/>
    Task<KernelSearchResults<TextSearchResult>> ITextSearch<BingWebPage>.GetTextSearchResultsAsync(string query, TextSearchOptions<BingWebPage>? searchOptions, CancellationToken cancellationToken)
    {
        var legacyOptions = searchOptions != null ? ConvertToLegacyOptions(searchOptions) : new TextSearchOptions();
        return this.GetTextSearchResultsAsync(query, legacyOptions, cancellationToken);
    }

    /// <inheritdoc/>
    Task<KernelSearchResults<object>> ITextSearch<BingWebPage>.GetSearchResultsAsync(string query, TextSearchOptions<BingWebPage>? searchOptions, CancellationToken cancellationToken)
    {
        var legacyOptions = searchOptions != null ? ConvertToLegacyOptions(searchOptions) : new TextSearchOptions();
        return this.GetSearchResultsAsync(query, legacyOptions, cancellationToken);
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

    // See https://learn.microsoft.com/en-us/bing/search-apis/bing-web-search/reference/query-parameters
    private static readonly string[] s_queryParameters = ["answerCount", "cc", "freshness", "mkt", "promote", "responseFilter", "safeSearch", "setLang", "textDecorations", "textFormat"];
    private static readonly string[] s_advancedSearchKeywords = ["contains", "ext", "filetype", "inanchor", "inbody", "intitle", "ip", "language", "loc", "location", "prefer", "site", "feed", "hasfeed", "url"];

    private const string DefaultUri = "https://api.bing.microsoft.com/v7.0/search";

    /// <summary>
    /// Converts generic TextSearchOptions with LINQ filtering to legacy TextSearchOptions.
    /// Attempts to translate simple LINQ expressions to Bing API filters where possible.
    /// </summary>
    /// <param name="genericOptions">The generic search options with LINQ filtering.</param>
    /// <returns>Legacy TextSearchOptions with equivalent filtering, or null if no conversion possible.</returns>
    private static TextSearchOptions ConvertToLegacyOptions(TextSearchOptions<BingWebPage> genericOptions)
    {
        return new TextSearchOptions
        {
            Top = genericOptions.Top,
            Skip = genericOptions.Skip,
            Filter = genericOptions.Filter != null ? ConvertLinqExpressionToBingFilter(genericOptions.Filter) : null
        };
    }

    /// <summary>
    /// Converts a LINQ expression to a TextSearchFilter compatible with Bing API.
    /// Only supports simple property equality expressions that map to Bing's filter capabilities.
    /// </summary>
    /// <param name="linqExpression">The LINQ expression to convert.</param>
    /// <returns>A TextSearchFilter with equivalent filtering.</returns>
    /// <exception cref="NotSupportedException">Thrown when the expression cannot be converted to Bing filters.</exception>
    private static TextSearchFilter ConvertLinqExpressionToBingFilter<TRecord>(Expression<Func<TRecord, bool>> linqExpression)
    {
        if (linqExpression.Body is BinaryExpression binaryExpr && binaryExpr.NodeType == ExpressionType.Equal)
        {
            // Handle simple equality: record.PropertyName == "value"
            if (binaryExpr.Left is MemberExpression memberExpr && binaryExpr.Right is ConstantExpression constExpr)
            {
                string propertyName = memberExpr.Member.Name;
                object? value = constExpr.Value;

                // Map BingWebPage properties to Bing API filter names
                string? bingFilterName = MapPropertyToBingFilter(propertyName);
                if (bingFilterName != null && value != null)
                {
                    return new TextSearchFilter().Equality(bingFilterName, value);
                }
            }
        }

        throw new NotSupportedException(
            "LINQ expression '" + linqExpression + "' cannot be converted to Bing API filters. " +
            "Only simple equality expressions like 'page => page.Language == \"en\"' are supported, " +
            "and only for properties that map to Bing API parameters: " +
            string.Join(", ", s_queryParameters.Concat(s_advancedSearchKeywords)));
    }

    /// <summary>
    /// Maps BingWebPage property names to Bing API filter field names.
    /// </summary>
    /// <param name="propertyName">The BingWebPage property name.</param>
    /// <returns>The corresponding Bing API filter name, or null if not mappable.</returns>
    private static string? MapPropertyToBingFilter(string propertyName)
    {
        return propertyName.ToUpperInvariant() switch
        {
            // Map BingWebPage properties to Bing API equivalents
            "LANGUAGE" => "language",           // Maps to advanced search
            "URL" => "url",                    // Maps to advanced search
            "DISPLAYURL" => "site",            // Maps to site: search
            "NAME" => "intitle",               // Maps to title search
            "SNIPPET" => "inbody",             // Maps to body content search

            // Direct API parameters (if we ever extend BingWebPage with metadata)
            "MKT" => "mkt",                    // Market/locale
            "FRESHNESS" => "freshness",        // Date freshness
            "SAFESEARCH" => "safeSearch",      // Safe search setting

            _ => null // Property not mappable to Bing filters
        };
    }

    /// <summary>
    /// Execute a Bing search query and return the results.
    /// </summary>
    /// <param name="query">What to search for.</param>
    /// <param name="searchOptions">Search options.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    private async Task<BingSearchResponse<BingWebPage>?> ExecuteSearchAsync(string query, TextSearchOptions searchOptions, CancellationToken cancellationToken = default)
    {
        using HttpResponseMessage response = await this.SendGetRequestAsync(query, searchOptions, cancellationToken).ConfigureAwait(false);

        this._logger.LogDebug("Response received: {StatusCode}", response.StatusCode);

        string json = await response.Content.ReadAsStringWithExceptionMappingAsync(cancellationToken).ConfigureAwait(false);

        // Sensitive data, logging as trace, disabled by default
        this._logger.LogTrace("Response content received: {Data}", json);

        return JsonSerializer.Deserialize<BingSearchResponse<BingWebPage>>(json);
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
        if (searchOptions.Top is <= 0 or > 50)
        {
            throw new ArgumentOutOfRangeException(nameof(searchOptions), searchOptions, $"{nameof(searchOptions)} count value must be greater than 0 and have a maximum value of 50.");
        }

        Uri uri = new($"{this._uri}?q={BuildQuery(query, searchOptions)}");

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
    private async IAsyncEnumerable<object> GetResultsAsWebPageAsync(BingSearchResponse<BingWebPage>? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
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
            yield return this._resultMapper.MapFromResultToTextSearchResult(webPage);
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
            yield return this._stringMapper.MapFromResultToString(webPage);
            await Task.Yield();
        }
    }

    /// <summary>
    /// Return the results metadata.
    /// </summary>
    /// <param name="searchResponse">Response containing the documents matching the query.</param>
    private static Dictionary<string, object?>? GetResultsMetadata(BingSearchResponse<BingWebPage>? searchResponse)
    {
        return new Dictionary<string, object?>()
        {
            { "AlteredQuery", searchResponse?.QueryContext?.AlteredQuery },
        };
    }

    /// <summary>
    /// Default implementation which maps from a <see cref="BingWebPage"/> to a <see cref="string"/>
    /// </summary>
    private sealed class DefaultTextSearchStringMapper : ITextSearchStringMapper
    {
        /// <inheritdoc />
        public string MapFromResultToString(object result)
        {
            if (result is not BingWebPage webPage)
            {
                throw new ArgumentException("Result must be a BingWebPage", nameof(result));
            }

            return webPage.Snippet ?? string.Empty;
        }
    }

    /// <summary>
    /// Default implementation which maps from a <see cref="BingWebPage"/> to a <see cref="TextSearchResult"/>
    /// </summary>
    private sealed class DefaultTextSearchResultMapper : ITextSearchResultMapper
    {
        /// <inheritdoc />
        public TextSearchResult MapFromResultToTextSearchResult(object result)
        {
            if (result is not BingWebPage webPage)
            {
                throw new ArgumentException("Result must be a BingWebPage", nameof(result));
            }

            return new TextSearchResult(webPage.Snippet ?? string.Empty) { Name = webPage.Name, Link = webPage.Url };
        }
    }

#pragma warning disable CS0618 // FilterClause is obsolete
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
                    if (s_advancedSearchKeywords.Contains(equalityFilterClause.FieldName, StringComparer.OrdinalIgnoreCase) && equalityFilterClause.Value is not null)
                    {
                        fullQuery.Append($"+{equalityFilterClause.FieldName}%3A").Append(Uri.EscapeDataString(equalityFilterClause.Value.ToString()!));
                    }
                    else if (s_queryParameters.Contains(equalityFilterClause.FieldName, StringComparer.OrdinalIgnoreCase) && equalityFilterClause.Value is not null)
                    {
                        string? queryParam = s_queryParameters.FirstOrDefault(s => s.Equals(equalityFilterClause.FieldName, StringComparison.OrdinalIgnoreCase));
                        queryParams.Append('&').Append(queryParam!).Append('=').Append(Uri.EscapeDataString(equalityFilterClause.Value.ToString()!));
                    }
                    else
                    {
                        throw new ArgumentException($"Unknown equality filter clause field name '{equalityFilterClause.FieldName}', must be one of {string.Join(",", s_queryParameters)},{string.Join(",", s_advancedSearchKeywords)}", nameof(searchOptions));
                    }
                }
            }
        }

        fullQuery.Append($"&count={searchOptions.Top}&offset={searchOptions.Skip}{queryParams}");

        return fullQuery.ToString();
    }
#pragma warning restore CS0618 // FilterClause is obsolete

    #endregion
}
