// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Linq.Expressions;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Plugins.Web.Keenable;

/// <summary>
/// A Keenable Text Search implementation that can be used to perform searches using the Keenable Web Search API.
/// </summary>
/// <remarks>
/// The API key is optional. Without a key the connector calls the public endpoint, which is rate limited per client IP.
/// With a key the connector calls the authenticated endpoint, which lifts those limits.
/// </remarks>
#pragma warning disable CS0618 // ITextSearch is obsolete
public sealed class KeenableTextSearch : ITextSearch, ITextSearch<KeenableWebPage>
#pragma warning restore CS0618
{
    /// <summary>
    /// Create an instance of the <see cref="KeenableTextSearch"/>.
    /// </summary>
    /// <param name="apiKey">Optional API key used to authenticate requests against the Search service. When null or empty the public endpoint is used.</param>
    /// <param name="options">Options used when creating this instance of <see cref="KeenableTextSearch"/>.</param>
    public KeenableTextSearch(string? apiKey = null, KeenableTextSearchOptions? options = null)
    {
        var endpoint = options?.Endpoint ?? new Uri(DefaultUri);
        if (!string.Equals(endpoint.Scheme, Uri.UriSchemeHttps, StringComparison.OrdinalIgnoreCase))
        {
            throw new ArgumentException($"The Keenable endpoint must use HTTPS, got '{endpoint}'. The API key is sent as a request header and must not travel in clear text.", nameof(options));
        }

        this._apiKey = string.IsNullOrWhiteSpace(apiKey) ? null : apiKey;
        this._uri = BuildSearchUri(endpoint, this._apiKey is null);
        this._searchOptions = options;
        this._logger = options?.LoggerFactory?.CreateLogger(typeof(KeenableTextSearch)) ?? NullLogger.Instance;
        this._httpClient = options?.HttpClient ?? HttpClientProvider.GetHttpClient();
        this._httpClient.DefaultRequestHeaders.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
        this._httpClient.DefaultRequestHeaders.Add(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(typeof(KeenableTextSearch)));
        this._stringMapper = options?.StringMapper ?? s_defaultStringMapper;
        this._resultMapper = options?.ResultMapper ?? s_defaultResultMapper;
    }

#pragma warning disable CS0618 // Obsolete ITextSearch, TextSearchOptions, TextSearchFilter, FilterClause

    #region Legacy ITextSearch Implementation

    /// <inheritdoc/>
    public async Task<KernelSearchResults<string>> SearchAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        searchOptions ??= new TextSearchOptions();
        var filters = ExtractFiltersFromLegacy(searchOptions.Filter);
        KeenableSearchResponse? searchResponse = await this.ExecuteSearchAsync(query, searchOptions.Top, searchOptions.Skip, filters, cancellationToken).ConfigureAwait(false);

        // The API does not report a total count.
        long? totalCount = null;

        return new KernelSearchResults<string>(this.GetResultsAsStringAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<TextSearchResult>> GetTextSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        searchOptions ??= new TextSearchOptions();
        var filters = ExtractFiltersFromLegacy(searchOptions.Filter);
        KeenableSearchResponse? searchResponse = await this.ExecuteSearchAsync(query, searchOptions.Top, searchOptions.Skip, filters, cancellationToken).ConfigureAwait(false);

        // The API does not report a total count.
        long? totalCount = null;

        return new KernelSearchResults<TextSearchResult>(this.GetResultsAsTextSearchResultAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<object>> GetSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        searchOptions ??= new TextSearchOptions();
        var filters = ExtractFiltersFromLegacy(searchOptions.Filter);
        KeenableSearchResponse? searchResponse = await this.ExecuteSearchAsync(query, searchOptions.Top, searchOptions.Skip, filters, cancellationToken).ConfigureAwait(false);

        // The API does not report a total count.
        long? totalCount = null;

        return new KernelSearchResults<object>(this.GetResultsAsObjectAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    #endregion

#pragma warning restore CS0618

    #region Generic ITextSearch<KeenableWebPage> Implementation

    /// <inheritdoc/>
    async Task<KernelSearchResults<string>> ITextSearch<KeenableWebPage>.SearchAsync(string query, TextSearchOptions<KeenableWebPage>? searchOptions, CancellationToken cancellationToken)
    {
        var (modifiedQuery, top, skip, filters) = ExtractSearchParameters(query, searchOptions);
        KeenableSearchResponse? searchResponse = await this.ExecuteSearchAsync(modifiedQuery, top, skip, filters, cancellationToken).ConfigureAwait(false);

        // The API does not report a total count.
        long? totalCount = null;

        return new KernelSearchResults<string>(this.GetResultsAsStringAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    async Task<KernelSearchResults<TextSearchResult>> ITextSearch<KeenableWebPage>.GetTextSearchResultsAsync(string query, TextSearchOptions<KeenableWebPage>? searchOptions, CancellationToken cancellationToken)
    {
        var (modifiedQuery, top, skip, filters) = ExtractSearchParameters(query, searchOptions);
        KeenableSearchResponse? searchResponse = await this.ExecuteSearchAsync(modifiedQuery, top, skip, filters, cancellationToken).ConfigureAwait(false);

        // The API does not report a total count.
        long? totalCount = null;

        return new KernelSearchResults<TextSearchResult>(this.GetResultsAsTextSearchResultAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    async Task<KernelSearchResults<KeenableWebPage>> ITextSearch<KeenableWebPage>.GetSearchResultsAsync(string query, TextSearchOptions<KeenableWebPage>? searchOptions, CancellationToken cancellationToken)
    {
        var (modifiedQuery, top, skip, filters) = ExtractSearchParameters(query, searchOptions);
        KeenableSearchResponse? searchResponse = await this.ExecuteSearchAsync(modifiedQuery, top, skip, filters, cancellationToken).ConfigureAwait(false);

        // The API does not report a total count.
        long? totalCount = null;

        return new KernelSearchResults<KeenableWebPage>(this.GetResultsAsWebPageAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    #endregion

    #region LINQ-to-Keenable Conversion Logic

    /// <summary>
    /// Extracts search parameters from generic <see cref="TextSearchOptions{TRecord}"/>.
    /// This is the primary entry point for the LINQ-based filtering path.
    /// Keenable supports query modification via Title.Contains() which appends terms to the query.
    /// </summary>
    private static (string ModifiedQuery, int Top, int Skip, List<(string FieldName, object Value)> Filters) ExtractSearchParameters<TRecord>(string query, TextSearchOptions<TRecord>? searchOptions)
    {
        var top = searchOptions?.Top ?? 3;
        var skip = searchOptions?.Skip ?? 0;

        if (searchOptions?.Filter == null)
        {
            return (query, top, skip, []);
        }

        var filters = new List<(string FieldName, object Value)>();
        var queryTerms = new List<string>();

        ExtractFiltersFromExpression(searchOptions.Filter.Body, filters, queryTerms);

        // Append query terms from Title.Contains() to the search query
        var modifiedQuery = queryTerms.Count > 0
            ? $"{query} {string.Join(" ", queryTerms)}".Trim()
            : query;

        return (modifiedQuery, top, skip, filters);
    }

    /// <summary>
    /// Walks a LINQ expression tree and extracts Keenable API filter key-value pairs and query terms directly.
    /// Supports equality comparisons on Site, PublishedAfter and PublishedBefore, Title.Contains() and Site.Contains(),
    /// combined with logical AND only. OR, NOT and inequality cannot be expressed as a single request and are rejected.
    /// </summary>
    /// <param name="expression">The expression to analyze.</param>
    /// <param name="filters">The list to add filter key-value pairs to.</param>
    /// <param name="queryTerms">The list to add query modification terms to.</param>
    private static void ExtractFiltersFromExpression(Expression expression, List<(string FieldName, object Value)> filters, List<string> queryTerms)
    {
        switch (expression)
        {
            case BinaryExpression { NodeType: ExpressionType.AndAlso } binaryExpr:
                // Handle AND expressions by recursively analyzing both sides; every clause ends up in the same request
                ExtractFiltersFromExpression(binaryExpr.Left, filters, queryTerms);
                ExtractFiltersFromExpression(binaryExpr.Right, filters, queryTerms);
                break;

            case BinaryExpression { NodeType: ExpressionType.OrElse }:
                // A single request cannot express alternatives; merging both sides would silently search only the last one
                throw new NotSupportedException(UnsupportedFilterMessage("Logical OR (||)"));

            case BinaryExpression { NodeType: ExpressionType.Equal } binaryExpr:
                ProcessEqualityClause(binaryExpr, filters);
                break;

            case BinaryExpression { NodeType: ExpressionType.NotEqual } binaryExpr:
                ProcessInequalityClause(binaryExpr);
                break;

            case BinaryExpression binaryExpr:
                throw new NotSupportedException(UnsupportedFilterMessage($"Binary expression type '{binaryExpr.NodeType}'"));

            case UnaryExpression { NodeType: ExpressionType.Not } unaryExpr:
                ProcessNotExpression(unaryExpr);
                break;

            case MethodCallExpression methodCall:
                ProcessMethodCallClause(methodCall, filters, queryTerms);
                break;

            default:
                throw new NotSupportedException(UnsupportedFilterMessage($"Expression type '{expression.NodeType}'"));
        }
    }

    /// <summary>
    /// Processes an equality expression and maps the property to a Keenable API filter directly.
    /// </summary>
    private static void ProcessEqualityClause(BinaryExpression binaryExpr, List<(string FieldName, object Value)> filters)
    {
        string? propertyName = null;
        object? value = null;

        if (binaryExpr.Left is MemberExpression leftMember)
        {
            propertyName = leftMember.Member.Name;
            value = ExtractValue(binaryExpr.Right);
        }
        else if (binaryExpr.Right is MemberExpression rightMember)
        {
            propertyName = rightMember.Member.Name;
            value = ExtractValue(binaryExpr.Left);
        }

        if (propertyName != null && value != null)
        {
            var mappedFieldName = MapPropertyToKeenableFilter(propertyName);
            if (mappedFieldName != null)
            {
                filters.Add((mappedFieldName, value));
            }
            else
            {
                throw new NotSupportedException(
                    $"Property '{propertyName}' cannot be mapped to Keenable API filters. " +
                    $"Supported properties: {string.Join(", ", s_validFieldNames)}. " +
                    "Example: page => page.Site == \"learn.microsoft.com\" && page.PublishedAfter == \"2025-01-01\"");
            }
        }
        else
        {
            throw new NotSupportedException("Unable to extract property name and value from equality expression.");
        }
    }

    /// <summary>
    /// Processes an inequality expression, which is not supported by the Keenable API.
    /// </summary>
    private static void ProcessInequalityClause(BinaryExpression binaryExpr)
    {
        string? propertyName = null;

        if (binaryExpr.Left is MemberExpression leftMember)
        {
            propertyName = leftMember.Member.Name;
        }
        else if (binaryExpr.Right is MemberExpression rightMember)
        {
            propertyName = rightMember.Member.Name;
        }

        throw new NotSupportedException(UnsupportedFilterMessage(propertyName is null
            ? "Inequality operator (!=)"
            : $"Inequality operator (!=) on property '{propertyName}'"));
    }

    /// <summary>
    /// Processes a NOT (negation) expression, which is not supported by the Keenable API.
    /// </summary>
    private static void ProcessNotExpression(UnaryExpression unaryExpr)
    {
        throw new NotSupportedException(UnsupportedFilterMessage($"NOT operator (!) on '{unaryExpr.Operand}'"));
    }

    /// <summary>
    /// Builds the message for an unsupported filter construct, stating what the connector does support.
    /// </summary>
    private static string UnsupportedFilterMessage(string what) =>
        $"{what} is not supported in Keenable search filters. " +
        "Only equality comparisons (==) on Site, PublishedAfter and PublishedBefore, Title.Contains() and Site.Contains(), combined with &&, are supported. " +
        "Apply other conditions client-side or run multiple queries.";

    /// <summary>
    /// Processes a method call expression (Contains) and maps to filters or query terms directly.
    /// </summary>
    private static void ProcessMethodCallClause(MethodCallExpression methodCall, List<(string FieldName, object Value)> filters, List<string> queryTerms)
    {
        if (methodCall.Method.Name == "Contains")
        {
            if (methodCall.Object is MemberExpression member)
            {
                // Instance method: property.Contains(value) - e.g., page.Site.Contains("learn.microsoft.com")
                var propertyName = member.Member.Name;
                var value = ExtractValue(methodCall.Arguments[0]);

                if (value != null)
                {
                    if (propertyName.Equals("Site", StringComparison.OrdinalIgnoreCase))
                    {
                        // For Contains on the site property, map to equality filter
                        filters.Add((Site, value));
                    }
                    else if (propertyName.Equals("Title", StringComparison.OrdinalIgnoreCase))
                    {
                        // For Title.Contains(), add the term to the search query
                        queryTerms.Add(value.ToString() ?? string.Empty);
                    }
                    else
                    {
                        throw new NotSupportedException($"Contains method is only supported for the Site and Title properties, not '{propertyName}'.");
                    }
                }
            }
            else
            {
                throw new NotSupportedException(
                    "Collection Contains filters (e.g., array.Contains(page.Property)) are not supported by Keenable Search API. " +
                    "Consider either: (1) performing multiple separate searches for each value, or " +
                    "(2) retrieving broader results and filtering on the client side.");
            }
        }
        else
        {
            throw new NotSupportedException($"Method '{methodCall.Method.Name}' is not supported in Keenable search filters. Only 'Contains' is supported.");
        }
    }

    /// <summary>
    /// Maps KeenableWebPage property names to Keenable API filter parameter names.
    /// </summary>
    /// <param name="propertyName">The property name from KeenableWebPage.</param>
    /// <returns>The corresponding Keenable API parameter name, or null if not mappable.</returns>
    private static string? MapPropertyToKeenableFilter(string propertyName) =>
        propertyName.ToUpperInvariant() switch
        {
            "SITE" => Site,
            "PUBLISHEDAFTER" => PublishedAfter,
            "PUBLISHEDBEFORE" => PublishedBefore,
            _ => null // Property not mappable to Keenable filters
        };

    /// <summary>
    /// Extracts a constant value from an expression.
    /// </summary>
    /// <param name="expression">The expression to extract the value from.</param>
    /// <returns>The extracted value, or null if extraction failed.</returns>
    private static object? ExtractValue(Expression expression)
    {
        return expression switch
        {
            ConstantExpression constant => constant.Value,
            MemberExpression member => ExtractMemberValue(member),
            _ => throw new NotSupportedException(
                $"Unable to extract value from expression of node type '{expression.NodeType}'. " +
                "Only constant expressions and member access are supported for AOT compatibility. " +
                "Expression: " + expression)
        };
    }

    /// <summary>
    /// Extracts a value from a member expression by walking the member access chain.
    /// </summary>
    /// <param name="memberExpression">The member expression to evaluate.</param>
    /// <returns>The extracted value, or null if extraction failed.</returns>
    private static object? ExtractMemberValue(MemberExpression memberExpression)
    {
        // Recursively evaluate the member's expression (handles nested member access)
        var target = memberExpression.Expression is not null
            ? ExtractValue(memberExpression.Expression)
            : null;

        return memberExpression.Member switch
        {
            System.Reflection.FieldInfo field => field.GetValue(target),
            System.Reflection.PropertyInfo property => property.GetValue(target),
            _ => null
        };
    }

    #endregion

    #region Private Methods

    private readonly ILogger _logger;
    private readonly HttpClient _httpClient;
    private readonly string? _apiKey;
    private readonly Uri _uri;
    private readonly KeenableTextSearchOptions? _searchOptions;
    private readonly ITextSearchStringMapper _stringMapper;
    private readonly ITextSearchResultMapper _resultMapper;

    private static readonly ITextSearchStringMapper s_defaultStringMapper = new DefaultTextSearchStringMapper();
    private static readonly ITextSearchResultMapper s_defaultResultMapper = new DefaultTextSearchResultMapper();

    private const string DefaultUri = "https://api.keenable.ai";
    private const string SearchPath = "v1/search";
    private const string PublicSearchPath = "v1/search/public";
    private const int MaxResults = 50;

    /// <summary>
    /// Header that identifies the calling application to the service. Required by the public endpoint.
    /// </summary>
    private const string TitleHeaderName = "X-Keenable-Title";
    private const string TitleHeaderValue = "semantic-kernel";
    private const string ApiKeyHeaderName = "X-API-Key";

    private const string Site = "site";
    private const string PublishedAfter = "published_after";
    private const string PublishedBefore = "published_before";

    private static readonly string[] s_validFieldNames = [Site, PublishedAfter, PublishedBefore];

    /// <summary>
    /// Build the full search URI from the base endpoint. The public path is used when no API key is configured.
    /// </summary>
    private static Uri BuildSearchUri(Uri endpoint, bool isPublic)
    {
        var baseUri = endpoint.AbsoluteUri.EndsWith("/", StringComparison.Ordinal) ? endpoint : new Uri(endpoint.AbsoluteUri + "/");
        return new Uri(baseUri, isPublic ? PublicSearchPath : SearchPath);
    }

    /// <summary>
    /// Execute a Keenable search query and return the results.
    /// </summary>
    /// <param name="query">What to search for.</param>
    /// <param name="top">Number of results to return.</param>
    /// <param name="skip">Number of results to skip.</param>
    /// <param name="filters">Pre-extracted filter key-value pairs.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    private async Task<KeenableSearchResponse?> ExecuteSearchAsync(string query, int top, int skip, List<(string FieldName, object Value)> filters, CancellationToken cancellationToken)
    {
        using HttpResponseMessage response = await this.SendPostRequestAsync(query, top, skip, filters, cancellationToken).ConfigureAwait(false);

        this._logger.LogDebug("Response received: {StatusCode}", response.StatusCode);

        string json = await response.Content.ReadAsStringWithExceptionMappingAsync(cancellationToken).ConfigureAwait(false);

        // Sensitive data, logging as trace, disabled by default
        this._logger.LogTrace("Response content received: {Data}", json);

        var searchResponse = JsonSerializer.Deserialize<KeenableSearchResponse>(json);

        // The API has no offset parameter, so the request asks for top + skip results and the first skip are dropped here.
        if (skip > 0 && searchResponse?.Results is { Count: > 0 })
        {
            searchResponse.Results = searchResponse.Results.Skip(skip).ToList();
        }

        return searchResponse;
    }

    /// <summary>
    /// Sends a POST request to the search endpoint.
    /// </summary>
    /// <param name="query">The query string.</param>
    /// <param name="top">Number of results to return.</param>
    /// <param name="skip">Number of results to skip.</param>
    /// <param name="filters">Pre-extracted filter key-value pairs.</param>
    /// <param name="cancellationToken">A cancellation token to cancel the request.</param>
    /// <returns>A <see cref="HttpResponseMessage"/> representing the response from the request.</returns>
    private async Task<HttpResponseMessage> SendPostRequestAsync(string query, int top, int skip, List<(string FieldName, object Value)> filters, CancellationToken cancellationToken)
    {
        Verify.NotNull(query);

        if (top is <= 0 or > MaxResults)
        {
            throw new ArgumentOutOfRangeException(nameof(top), top, $"{nameof(top)} count value must be greater than 0 and have a maximum value of {MaxResults}.");
        }

        if (skip < 0 || top + skip > MaxResults)
        {
            throw new ArgumentOutOfRangeException(nameof(skip), skip, $"{nameof(skip)} value must be equal or greater than 0 and {nameof(top)} + {nameof(skip)} must not exceed {MaxResults}.");
        }

        var requestContent = this.BuildRequestContent(query, top, skip, filters);

        using var httpRequestMessage = new HttpRequestMessage(HttpMethod.Post, this._uri)
        {
            Content = GetJsonContent(requestContent)
        };

        httpRequestMessage.Headers.Add(TitleHeaderName, TitleHeaderValue);

        if (!string.IsNullOrEmpty(this._apiKey))
        {
            httpRequestMessage.Headers.Add(ApiKeyHeaderName, this._apiKey);
        }

        return await this._httpClient.SendWithSuccessCheckAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Return the search results as instances of <see cref="KeenableSearchResult"/>.
    /// </summary>
    /// <param name="searchResponse">Response containing the web pages matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<object> GetResultsAsObjectAsync(KeenableSearchResponse? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse?.Results is null)
        {
            yield break;
        }

        foreach (var result in searchResponse.Results)
        {
            yield return result;
            await Task.Yield();
        }
    }

    /// <summary>
    /// Return the search results as instances of <see cref="KeenableWebPage"/>.
    /// </summary>
    /// <param name="searchResponse">Response containing the web pages matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<KeenableWebPage> GetResultsAsWebPageAsync(KeenableSearchResponse? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse?.Results is null)
        {
            yield break;
        }

        foreach (var result in searchResponse.Results)
        {
            yield return KeenableWebPage.FromSearchResult(result);
            await Task.Yield();
        }
    }

    /// <summary>
    /// Return the search results as instances of <see cref="TextSearchResult"/>.
    /// </summary>
    /// <param name="searchResponse">Response containing the web pages matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<TextSearchResult> GetResultsAsTextSearchResultAsync(KeenableSearchResponse? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse?.Results is null)
        {
            yield break;
        }

        foreach (var result in searchResponse.Results)
        {
            yield return this._resultMapper.MapFromResultToTextSearchResult(result);
            await Task.Yield();
        }
    }

    /// <summary>
    /// Return the search results as instances of <see cref="string"/>.
    /// </summary>
    /// <param name="searchResponse">Response containing the web pages matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<string> GetResultsAsStringAsync(KeenableSearchResponse? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse?.Results is null)
        {
            yield break;
        }

        foreach (var result in searchResponse.Results)
        {
            yield return this._stringMapper.MapFromResultToString(result);
            await Task.Yield();
        }
    }

    /// <summary>
    /// Return the results metadata.
    /// </summary>
    /// <param name="searchResponse">Response containing the documents matching the query.</param>
    private static Dictionary<string, object?>? GetResultsMetadata(KeenableSearchResponse? searchResponse)
    {
        return new Dictionary<string, object?>()
        {
            { "Query", searchResponse?.Query },
        };
    }

    /// <summary>
    /// Default implementation which maps from a <see cref="KeenableSearchResult"/> to a <see cref="string"/>
    /// </summary>
    private sealed class DefaultTextSearchStringMapper : ITextSearchStringMapper
    {
        /// <inheritdoc />
        public string MapFromResultToString(object result)
        {
            if (result is not KeenableSearchResult searchResult)
            {
                throw new ArgumentException("Result must be a KeenableSearchResult", nameof(result));
            }

            return searchResult.Text;
        }
    }

    /// <summary>
    /// Default implementation which maps from a <see cref="KeenableSearchResult"/> to a <see cref="TextSearchResult"/>
    /// </summary>
    private sealed class DefaultTextSearchResultMapper : ITextSearchResultMapper
    {
        /// <inheritdoc />
        public TextSearchResult MapFromResultToTextSearchResult(object result)
        {
            if (result is not KeenableSearchResult searchResult)
            {
                throw new ArgumentException("Result must be a KeenableSearchResult", nameof(result));
            }

            return new TextSearchResult(searchResult.Text) { Name = searchResult.Title, Link = searchResult.Url };
        }
    }

    /// <summary>
    /// Extracts filter key-value pairs from a legacy <see cref="TextSearchFilter"/>.
    /// This shim converts the obsolete FilterClause-based format to the internal (FieldName, Value) list.
    /// It will be removed when the legacy ITextSearch interface is retired.
    /// </summary>
#pragma warning disable CS0618 // Obsolete TextSearchFilter, FilterClause
    private static List<(string FieldName, object Value)> ExtractFiltersFromLegacy(TextSearchFilter? filter)
    {
        var filters = new List<(string FieldName, object Value)>();
        if (filter is not null)
        {
            foreach (var clause in filter.FilterClauses)
            {
                if (clause is EqualToFilterClause eq)
                {
                    filters.Add((eq.FieldName, eq.Value));
                }
                else
                {
                    throw new NotSupportedException(
                        $"Filter clause type '{clause.GetType().Name}' is not supported by Keenable Text Search. Only EqualToFilterClause is supported.");
                }
            }
        }
        return filters;
    }
#pragma warning restore CS0618

    /// <summary>
    /// Build a Keenable API request from pre-extracted filter key-value pairs.
    /// Both LINQ and legacy paths converge here after producing the same (FieldName, Value) list.
    /// </summary>
    /// <param name="query">The query.</param>
    /// <param name="top">Number of results to return.</param>
    /// <param name="skip">Number of results to skip.</param>
    /// <param name="filters">Pre-extracted filter key-value pairs.</param>
    private KeenableSearchRequest BuildRequestContent(string query, int top, int skip, List<(string FieldName, object Value)> filters)
    {
        string? site = null;
        string? publishedAfter = null;
        string? publishedBefore = null;

        foreach (var (fieldName, value) in filters)
        {
            if (fieldName.Equals(Site, StringComparison.OrdinalIgnoreCase) && value is not null)
            {
                site = value.ToString()!;
            }
            else if (fieldName.Equals(PublishedAfter, StringComparison.OrdinalIgnoreCase) && value is not null)
            {
                publishedAfter = FormatDate(value);
            }
            else if (fieldName.Equals(PublishedBefore, StringComparison.OrdinalIgnoreCase) && value is not null)
            {
                publishedBefore = FormatDate(value);
            }
            else
            {
                throw new ArgumentException($"Unknown equality filter clause field name '{fieldName}', must be one of {string.Join(",", s_validFieldNames)}", nameof(filters));
            }
        }

        return new KeenableSearchRequest(
            query,
            top + skip,
            this._searchOptions?.SnippetMaxLength,
            publishedAfter,
            publishedBefore,
            site);
    }

    /// <summary>
    /// Format a date filter value as YYYY-MM-DD. Strings are passed through unchanged.
    /// </summary>
    private static string FormatDate(object value) => value switch
    {
        DateTimeOffset dto => dto.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture),
        DateTime dt => dt.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture),
        _ => value.ToString()!,
    };

    private static readonly JsonSerializerOptions s_jsonOptionsCache = new()
    {
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    };

    private static StringContent GetJsonContent(object payload)
    {
        string strPayload = JsonSerializer.Serialize(payload, s_jsonOptionsCache);
        return new(strPayload, Encoding.UTF8, "application/json");
    }

    #endregion
}
