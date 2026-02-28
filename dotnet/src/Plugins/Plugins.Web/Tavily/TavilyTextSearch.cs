// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable CS0618 // Obsolete ITextSearch, TextSearchOptions, TextSearchFilter, FilterClause - backward compatibility

using System;
using System.Collections.Generic;
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

namespace Microsoft.SemanticKernel.Plugins.Web.Tavily;

/// <summary>
/// A Tavily Text Search implementation that can be used to perform searches using the Tavily Web Search API.
/// </summary>
public sealed class TavilyTextSearch : ITextSearch, ITextSearch<TavilyWebPage>
{
    /// <summary>
    /// Create an instance of the <see cref="TavilyTextSearch"/> with API key authentication.
    /// </summary>
    /// <param name="apiKey">The API key credential used to authenticate requests against the Search service.</param>
    /// <param name="options">Options used when creating this instance of <see cref="TavilyTextSearch"/>.</param>
    public TavilyTextSearch(string apiKey, TavilyTextSearchOptions? options = null)
    {
        Verify.NotNullOrWhiteSpace(apiKey);

        this._apiKey = apiKey;
        this._uri = options?.Endpoint ?? new Uri(DefaultUri);
        this._searchOptions = options;
        this._logger = options?.LoggerFactory?.CreateLogger(typeof(TavilyTextSearch)) ?? NullLogger.Instance;
        this._httpClient = options?.HttpClient ?? HttpClientProvider.GetHttpClient();
        this._httpClient.DefaultRequestHeaders.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
        this._httpClient.DefaultRequestHeaders.Add(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(typeof(TavilyTextSearch)));
        this._stringMapper = options?.StringMapper ?? s_defaultStringMapper;
        this._resultMapper = options?.ResultMapper ?? s_defaultResultMapper;
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<string>> SearchAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        searchOptions ??= new TextSearchOptions();
        var filters = ExtractFiltersFromLegacy(searchOptions.Filter);
        TavilySearchResponse? searchResponse = await this.ExecuteSearchAsync(query, searchOptions.Top, searchOptions.Skip, filters, cancellationToken).ConfigureAwait(false);

        long? totalCount = null;

        return new KernelSearchResults<string>(this.GetResultsAsStringAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<TextSearchResult>> GetTextSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        searchOptions ??= new TextSearchOptions();
        var filters = ExtractFiltersFromLegacy(searchOptions.Filter);
        TavilySearchResponse? searchResponse = await this.ExecuteSearchAsync(query, searchOptions.Top, searchOptions.Skip, filters, cancellationToken).ConfigureAwait(false);

        long? totalCount = null;

        return new KernelSearchResults<TextSearchResult>(this.GetResultsAsTextSearchResultAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<object>> GetSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        searchOptions ??= new TextSearchOptions();
        var filters = ExtractFiltersFromLegacy(searchOptions.Filter);
        TavilySearchResponse? searchResponse = await this.ExecuteSearchAsync(query, searchOptions.Top, searchOptions.Skip, filters, cancellationToken).ConfigureAwait(false);

        long? totalCount = null;

        return new KernelSearchResults<object>(this.GetSearchResultsAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    #region Generic ITextSearch<TavilyWebPage> Implementation

    /// <inheritdoc/>
    async Task<KernelSearchResults<string>> ITextSearch<TavilyWebPage>.SearchAsync(string query, TextSearchOptions<TavilyWebPage>? searchOptions, CancellationToken cancellationToken)
    {
        var (modifiedQuery, top, skip, includeTotalCount, filters) = ExtractSearchParameters(query, searchOptions);
        TavilySearchResponse? searchResponse = await this.ExecuteSearchAsync(modifiedQuery, top, skip, filters, cancellationToken).ConfigureAwait(false);

        long? totalCount = null;

        return new KernelSearchResults<string>(this.GetResultsAsStringAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    async Task<KernelSearchResults<TextSearchResult>> ITextSearch<TavilyWebPage>.GetTextSearchResultsAsync(string query, TextSearchOptions<TavilyWebPage>? searchOptions, CancellationToken cancellationToken)
    {
        var (modifiedQuery, top, skip, includeTotalCount, filters) = ExtractSearchParameters(query, searchOptions);
        TavilySearchResponse? searchResponse = await this.ExecuteSearchAsync(modifiedQuery, top, skip, filters, cancellationToken).ConfigureAwait(false);

        long? totalCount = null;

        return new KernelSearchResults<TextSearchResult>(this.GetResultsAsTextSearchResultAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    async Task<KernelSearchResults<TavilyWebPage>> ITextSearch<TavilyWebPage>.GetSearchResultsAsync(string query, TextSearchOptions<TavilyWebPage>? searchOptions, CancellationToken cancellationToken)
    {
        var (modifiedQuery, top, skip, includeTotalCount, filters) = ExtractSearchParameters(query, searchOptions);
        TavilySearchResponse? searchResponse = await this.ExecuteSearchAsync(modifiedQuery, top, skip, filters, cancellationToken).ConfigureAwait(false);

        long? totalCount = null;

        return new KernelSearchResults<TavilyWebPage>(this.GetResultsAsWebPageAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    #endregion

    #region LINQ-to-Tavily Conversion Logic

    /// <summary>
    /// Extracts search parameters from generic <see cref="TextSearchOptions{TRecord}"/>.
    /// This is the primary entry point for the LINQ-based filtering path.
    /// Tavily supports query modification via Title.Contains() which appends terms to the query.
    /// </summary>
    private static (string ModifiedQuery, int Top, int Skip, bool IncludeTotalCount, List<(string FieldName, object Value)> Filters) ExtractSearchParameters<TRecord>(string query, TextSearchOptions<TRecord>? searchOptions)
    {
        var top = searchOptions?.Top ?? 3;
        var skip = searchOptions?.Skip ?? 0;
        var includeTotalCount = searchOptions?.IncludeTotalCount ?? false;

        if (searchOptions?.Filter == null)
        {
            return (query, top, skip, includeTotalCount, []);
        }

        var filters = new List<(string FieldName, object Value)>();
        var queryTerms = new List<string>();

        ExtractFiltersFromExpression(searchOptions.Filter.Body, filters, queryTerms);

        // Append query terms from Title.Contains() to the search query
        var modifiedQuery = queryTerms.Count > 0
            ? $"{query} {string.Join(" ", queryTerms)}".Trim()
            : query;

        return (modifiedQuery, top, skip, includeTotalCount, filters);
    }

    /// <summary>
    /// Walks a LINQ expression tree and extracts Tavily API filter key-value pairs and query terms directly.
    /// Supports equality expressions, Contains() method calls, and logical AND/OR operators.
    /// </summary>
    /// <param name="expression">The expression to analyze.</param>
    /// <param name="filters">The list to add filter key-value pairs to.</param>
    /// <param name="queryTerms">The list to add query modification terms to.</param>
    private static void ExtractFiltersFromExpression(Expression expression, List<(string FieldName, object Value)> filters, List<string> queryTerms)
    {
        switch (expression)
        {
            case BinaryExpression { NodeType: ExpressionType.AndAlso or ExpressionType.OrElse } binaryExpr:
                // Handle AND/OR expressions by recursively analyzing both sides
                ExtractFiltersFromExpression(binaryExpr.Left, filters, queryTerms);
                ExtractFiltersFromExpression(binaryExpr.Right, filters, queryTerms);
                break;

            case BinaryExpression { NodeType: ExpressionType.Equal } binaryExpr:
                ProcessEqualityClause(binaryExpr, filters);
                break;

            case BinaryExpression { NodeType: ExpressionType.NotEqual } binaryExpr:
                ProcessInequalityClause(binaryExpr);
                break;

            case BinaryExpression binaryExpr:
                throw new NotSupportedException($"Binary expression type '{binaryExpr.NodeType}' is not supported. Supported operators: AndAlso (&&), OrElse (||), Equal (==), NotEqual (!=).");

            case UnaryExpression { NodeType: ExpressionType.Not } unaryExpr:
                ProcessNotExpression(unaryExpr);
                break;

            case MethodCallExpression methodCall:
                ProcessMethodCallClause(methodCall, filters, queryTerms);
                break;

            default:
                throw new NotSupportedException($"Expression type '{expression.NodeType}' is not supported in Tavily search filters.");
        }
    }

    /// <summary>
    /// Processes an equality expression and maps the property to a Tavily API filter directly.
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
            var mappedFieldName = MapPropertyToTavilyFilter(propertyName);
            if (mappedFieldName != null)
            {
                filters.Add((mappedFieldName, value));
            }
            else
            {
                throw new NotSupportedException(
                    $"Property '{propertyName}' cannot be mapped to Tavily API filters. " +
                    $"Supported properties: {string.Join(", ", s_validFieldNames)}. " +
                    "Example: page => page.Topic == \"general\" && page.TimeRange == \"week\"");
            }
        }
        else
        {
            throw new NotSupportedException("Unable to extract property name and value from equality expression.");
        }
    }

    /// <summary>
    /// Processes an inequality expression — not supported by Tavily API.
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

        if (propertyName != null)
        {
            throw new NotSupportedException($"Inequality operator (!=) is not directly supported for property '{propertyName}'. Use NOT operator instead: !(page.{propertyName} == value).");
        }

        throw new NotSupportedException("Unable to extract property name and value from inequality expression.");
    }

    /// <summary>
    /// Processes a NOT (negation) expression — not supported by Tavily API.
    /// </summary>
    private static void ProcessNotExpression(UnaryExpression unaryExpr)
    {
        if (unaryExpr.Operand is BinaryExpression binaryExpr && binaryExpr.NodeType == ExpressionType.Equal)
        {
            throw new NotSupportedException("NOT operator (!) with equality is not directly supported. Most web search APIs don't support negative filtering.");
        }

        throw new NotSupportedException("NOT operator (!) is only supported with simple equality expressions.");
    }

    /// <summary>
    /// Processes a method call expression (Contains) and maps to filters or query terms directly.
    /// </summary>
    private static void ProcessMethodCallClause(MethodCallExpression methodCall, List<(string FieldName, object Value)> filters, List<string> queryTerms)
    {
        if (methodCall.Method.Name == "Contains")
        {
            if (methodCall.Object is MemberExpression member)
            {
                // Instance method: property.Contains(value) - e.g., page.IncludeDomain.Contains("wikipedia.org")
                var propertyName = member.Member.Name;
                var value = ExtractValue(methodCall.Arguments[0]);

                if (value != null)
                {
                    if (propertyName.EndsWith("Domain", StringComparison.OrdinalIgnoreCase))
                    {
                        // For Contains on domain properties, map to equality filter
                        var mappedFieldName = MapPropertyToTavilyFilter(propertyName);
                        if (mappedFieldName != null)
                        {
                            filters.Add((mappedFieldName, value));
                        }
                    }
                    else if (propertyName.Equals("Title", StringComparison.OrdinalIgnoreCase))
                    {
                        // For Title.Contains(), add the term to the search query
                        queryTerms.Add(value.ToString() ?? string.Empty);
                    }
                    else
                    {
                        throw new NotSupportedException($"Contains method is only supported for domain properties (IncludeDomain, ExcludeDomain) and Title, not '{propertyName}'.");
                    }
                }
            }
            else
            {
                throw new NotSupportedException(
                    "Collection Contains filters (e.g., array.Contains(page.Property)) are not supported by Tavily Search API. " +
                    "Consider either: (1) performing multiple separate searches for each value, or " +
                    "(2) retrieving broader results and filtering on the client side.");
            }
        }
        else
        {
            throw new NotSupportedException($"Method '{methodCall.Method.Name}' is not supported in Tavily search filters. Only 'Contains' is supported.");
        }
    }

    /// <summary>
    /// Maps TavilyWebPage property names to Tavily API filter parameter names.
    /// </summary>
    /// <param name="propertyName">The property name from TavilyWebPage.</param>
    /// <returns>The corresponding Tavily API parameter name, or null if not mappable.</returns>
    private static string? MapPropertyToTavilyFilter(string propertyName) =>
        propertyName.ToUpperInvariant() switch
        {
            "TOPIC" => Topic,
            "TIMERANGE" => TimeRange,
            "DAYS" => Days,
            "INCLUDEDOMAIN" => IncludeDomain,
            "EXCLUDEDOMAIN" => ExcludeDomain,
            _ => null // Property not mappable to Tavily filters
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
    private readonly Uri? _uri = null;
    private readonly TavilyTextSearchOptions? _searchOptions;
    private readonly ITextSearchStringMapper _stringMapper;
    private readonly ITextSearchResultMapper _resultMapper;

    private static readonly ITextSearchStringMapper s_defaultStringMapper = new DefaultTextSearchStringMapper();
    private static readonly ITextSearchResultMapper s_defaultResultMapper = new DefaultTextSearchResultMapper();

    private const string DefaultUri = "https://api.tavily.com/search";

    private const string Topic = "topic";
    private const string TimeRange = "time_range";
    private const string Days = "days";
    private const string IncludeDomain = "include_domain";
    private const string ExcludeDomain = "exclude_domain";

    private static readonly string[] s_validFieldNames = [Topic, TimeRange, Days, IncludeDomain, ExcludeDomain];

    /// <summary>
    /// Execute a Tavily search query and return the results.
    /// </summary>
    /// <param name="query">What to search for.</param>
    /// <param name="top">Number of results to return.</param>
    /// <param name="skip">Number of results to skip.</param>
    /// <param name="filters">Pre-extracted filter key-value pairs.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    private async Task<TavilySearchResponse?> ExecuteSearchAsync(string query, int top, int skip, List<(string FieldName, object Value)> filters, CancellationToken cancellationToken)
    {
        using HttpResponseMessage response = await this.SendGetRequestAsync(query, top, skip, filters, cancellationToken).ConfigureAwait(false);

        this._logger.LogDebug("Response received: {StatusCode}", response.StatusCode);

        string json = await response.Content.ReadAsStringWithExceptionMappingAsync(cancellationToken).ConfigureAwait(false);

        // Sensitive data, logging as trace, disabled by default
        this._logger.LogTrace("Response content received: {Data}", json);

        return JsonSerializer.Deserialize<TavilySearchResponse>(json);
    }

    /// <summary>
    /// Sends a POST request to the specified URI.
    /// </summary>
    /// <param name="query">The query string.</param>
    /// <param name="top">Number of results to return.</param>
    /// <param name="skip">Number of results to skip.</param>
    /// <param name="filters">Pre-extracted filter key-value pairs.</param>
    /// <param name="cancellationToken">A cancellation token to cancel the request.</param>
    /// <returns>A <see cref="HttpResponseMessage"/> representing the response from the request.</returns>
    private async Task<HttpResponseMessage> SendGetRequestAsync(string query, int top, int skip, List<(string FieldName, object Value)> filters, CancellationToken cancellationToken)
    {
        if (top is <= 0 or > 50)
        {
            throw new ArgumentOutOfRangeException(nameof(top), top, $"{nameof(top)} count value must be greater than 0 and have a maximum value of 50.");
        }

        var requestContent = this.BuildRequestContent(query, top, skip, filters);

        using var httpRequestMessage = new HttpRequestMessage(HttpMethod.Post, this._uri)
        {
            Content = GetJsonContent(requestContent)
        };

        if (!string.IsNullOrEmpty(this._apiKey))
        {
            httpRequestMessage.Headers.Add("Authorization", $"Bearer {this._apiKey}");
        }

        return await this._httpClient.SendWithSuccessCheckAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Return the search results as instances of <see cref="TavilySearchResult"/>.
    /// </summary>
    /// <param name="searchResponse">Response containing the web pages matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<object> GetSearchResultsAsync(TavilySearchResponse? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse is null || searchResponse.Results is null)
        {
            yield break;
        }

        foreach (var result in searchResponse.Results)
        {
            yield return result;
            await Task.Yield();
        }

        if (this._searchOptions?.IncludeImages ?? false && searchResponse.Images is not null)
        {
            foreach (var image in searchResponse.Images!)
            {
                yield return image;
                await Task.Yield();
            }
        }
    }

    /// <summary>
    /// Return the search results as instances of <see cref="TavilyWebPage"/>.
    /// </summary>
    /// <param name="searchResponse">Response containing the web pages matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<TavilyWebPage> GetResultsAsWebPageAsync(TavilySearchResponse? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse is null || searchResponse.Results is null)
        {
            yield break;
        }

        foreach (var result in searchResponse.Results)
        {
            yield return TavilyWebPage.FromSearchResult(result);
            await Task.Yield();
        }

        if (this._searchOptions?.IncludeImages ?? false && searchResponse.Images is not null)
        {
            foreach (var image in searchResponse.Images!)
            {
                //For images, create a basic TavilyWebPage representation
                Uri? imageUri = string.IsNullOrWhiteSpace(image.Url) ? null : new Uri(image.Url);
                yield return new TavilyWebPage(
                    title: "Image Result",
                    url: imageUri,
                    content: image.Description ?? string.Empty,
                    score: 0.0
                );
                await Task.Yield();
            }
        }
    }

    /// <summary>
    /// Return the search results as instances of <see cref="TextSearchResult"/>.
    /// </summary>
    /// <param name="searchResponse">Response containing the web pages matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<TextSearchResult> GetResultsAsTextSearchResultAsync(TavilySearchResponse? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse is null || searchResponse.Results is null)
        {
            yield break;
        }

        foreach (var result in searchResponse.Results)
        {
            yield return this._resultMapper.MapFromResultToTextSearchResult(result);
            await Task.Yield();
        }

        if (this._searchOptions?.IncludeImages ?? false && searchResponse.Images is not null)
        {
            foreach (var image in searchResponse.Images!)
            {
                yield return this._resultMapper.MapFromResultToTextSearchResult(image);
                await Task.Yield();
            }
        }
    }

    /// <summary>
    /// Return the search results as instances of <see cref="TextSearchResult"/>.
    /// </summary>
    /// <param name="searchResponse">Response containing the web pages matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<string> GetResultsAsStringAsync(TavilySearchResponse? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse is null || searchResponse.Results is null)
        {
            yield break;
        }

        if (this._searchOptions?.IncludeAnswer ?? false)
        {
            yield return searchResponse.Answer ?? string.Empty;
            await Task.Yield();
        }

        foreach (var result in searchResponse.Results)
        {
            yield return this._stringMapper.MapFromResultToString(result);
            await Task.Yield();
        }

        if (this._searchOptions?.IncludeImages ?? false && searchResponse.Images is not null)
        {
            foreach (var image in searchResponse.Images!)
            {
                yield return this._stringMapper.MapFromResultToString(image);
                await Task.Yield();
            }
        }
    }

    /// <summary>
    /// Return the results metadata.
    /// </summary>
    /// <param name="searchResponse">Response containing the documents matching the query.</param>
    private static Dictionary<string, object?>? GetResultsMetadata(TavilySearchResponse? searchResponse)
    {
        return new Dictionary<string, object?>()
        {
            { "ResponseTime", searchResponse?.ResponseTime },
        };
    }

    /// <summary>
    /// Default implementation which maps from a <see cref="TavilySearchResult"/> to a <see cref="string"/>
    /// </summary>
    private sealed class DefaultTextSearchStringMapper : ITextSearchStringMapper
    {
        /// <inheritdoc />
        public string MapFromResultToString(object result)
        {
            if (result is TavilySearchResult searchResult)
            {
                return searchResult.RawContent ?? searchResult.Content ?? string.Empty;
            }
            else if (result is TavilyImageResult imageResult)
            {
                return imageResult.Description ?? string.Empty;
            }
            throw new ArgumentException("Result must be a TavilySearchResult", nameof(result));
        }
    }

    /// <summary>
    /// Default implementation which maps from a <see cref="TavilySearchResult"/> to a <see cref="TextSearchResult"/>
    /// </summary>
    private sealed class DefaultTextSearchResultMapper : ITextSearchResultMapper
    {
        /// <inheritdoc />
        public TextSearchResult MapFromResultToTextSearchResult(object result)
        {
            if (result is TavilySearchResult searchResult)
            {
                return new TextSearchResult(searchResult.RawContent ?? searchResult.Content ?? string.Empty) { Name = searchResult.Title, Link = searchResult.Url };
            }
            else if (result is TavilyImageResult imageResult)
            {
                var uri = new Uri(imageResult.Url);
                var name = uri.Segments[^1];
                return new TextSearchResult(imageResult.Description ?? string.Empty) { Name = name, Link = imageResult.Url };
            }
            throw new ArgumentException("Result must be a TavilySearchResult", nameof(result));
        }
    }

    /// <summary>
    /// Extracts filter key-value pairs from a legacy <see cref="TextSearchFilter"/>.
    /// This shim converts the obsolete FilterClause-based format to the internal (FieldName, Value) list.
    /// It will be removed when the legacy ITextSearch interface is retired.
    /// </summary>
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
                        $"Filter clause type '{clause.GetType().Name}' is not supported by Tavily Text Search. Only EqualToFilterClause is supported.");
                }
            }
        }
        return filters;
    }

    /// <summary>
    /// Build a Tavily API request from pre-extracted filter key-value pairs.
    /// Both LINQ and legacy paths converge here after producing the same (FieldName, Value) list.
    /// </summary>
    /// <param name="query">The query.</param>
    /// <param name="top">Number of results to return.</param>
    /// <param name="skip">Number of results to skip.</param>
    /// <param name="filters">Pre-extracted filter key-value pairs.</param>
    private TavilySearchRequest BuildRequestContent(string query, int top, int skip, List<(string FieldName, object Value)> filters)
    {
        string? topic = null;
        string? timeRange = null;
        int? days = null;
        int? maxResults = top - skip;
        IList<string>? includeDomains = null;
        IList<string>? excludeDomains = null;

        foreach (var (fieldName, value) in filters)
        {
            if (fieldName.Equals(Topic, StringComparison.OrdinalIgnoreCase) && value is not null)
            {
                topic = value.ToString()!;
            }
            else if (fieldName.Equals(TimeRange, StringComparison.OrdinalIgnoreCase) && value is not null)
            {
                timeRange = value.ToString()!;
            }
            else if (fieldName.Equals(Days, StringComparison.OrdinalIgnoreCase) && value is not null)
            {
                days = Convert.ToInt32(value);
            }
            else if (fieldName.Equals(IncludeDomain, StringComparison.OrdinalIgnoreCase) && value is not null)
            {
                var includeDomain = value.ToString()!;
                includeDomains ??= [];
                includeDomains.Add(includeDomain);
            }
            else if (fieldName.Equals(ExcludeDomain, StringComparison.OrdinalIgnoreCase) && value is not null)
            {
                var excludeDomain = value.ToString()!;
                excludeDomains ??= [];
                excludeDomains.Add(excludeDomain);
            }
            else
            {
                throw new ArgumentException($"Unknown equality filter clause field name '{fieldName}', must be one of {string.Join(",", s_validFieldNames)}", nameof(filters));
            }
        }

        return new TavilySearchRequest(
            query,
            topic,
            timeRange,
            days,
#pragma warning disable CA1308 // Lower is preferred over uppercase
            this._searchOptions?.SearchDepth?.ToString()?.ToLowerInvariant(),
#pragma warning restore CA1308
            this._searchOptions?.ChunksPerSource,
            this._searchOptions?.IncludeImages,
            this._searchOptions?.IncludeImageDescriptions,
            this._searchOptions?.IncludeAnswer,
            this._searchOptions?.IncludeRawContent,
            maxResults,
            includeDomains,
            excludeDomains);
    }

    private static readonly JsonSerializerOptions s_jsonOptionsCache = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    };

    private static StringContent? GetJsonContent(object? payload)
    {
        if (payload is null)
        {
            return null;
        }

        string strPayload = payload as string ?? JsonSerializer.Serialize(payload, s_jsonOptionsCache);
        return new(strPayload, Encoding.UTF8, "application/json");
    }

    #endregion
}
