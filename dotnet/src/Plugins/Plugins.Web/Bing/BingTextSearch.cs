// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable CS0618 // Non-generic ITextSearch is obsolete - provides backward compatibility during Phase 2 LINQ migration

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
        this._options = options;
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<string>> SearchAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        searchOptions ??= new TextSearchOptions();
        var filters = ExtractFiltersFromLegacy(searchOptions.Filter);
        BingSearchResponse<BingWebPage>? searchResponse = await this.ExecuteSearchAsync(query, searchOptions.Top, searchOptions.Skip, filters, cancellationToken).ConfigureAwait(false);

        long? totalCount = searchOptions.IncludeTotalCount ? searchResponse?.WebPages?.TotalEstimatedMatches : null;

        return new KernelSearchResults<string>(this.GetResultsAsStringAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<TextSearchResult>> GetTextSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        searchOptions ??= new TextSearchOptions();
        var filters = ExtractFiltersFromLegacy(searchOptions.Filter);
        BingSearchResponse<BingWebPage>? searchResponse = await this.ExecuteSearchAsync(query, searchOptions.Top, searchOptions.Skip, filters, cancellationToken).ConfigureAwait(false);

        long? totalCount = searchOptions.IncludeTotalCount ? searchResponse?.WebPages?.TotalEstimatedMatches : null;

        return new KernelSearchResults<TextSearchResult>(this.GetResultsAsTextSearchResultAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<object>> GetSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        searchOptions ??= new TextSearchOptions();
        var filters = ExtractFiltersFromLegacy(searchOptions.Filter);
        BingSearchResponse<BingWebPage>? searchResponse = await this.ExecuteSearchAsync(query, searchOptions.Top, searchOptions.Skip, filters, cancellationToken).ConfigureAwait(false);

        long? totalCount = searchOptions.IncludeTotalCount ? searchResponse?.WebPages?.TotalEstimatedMatches : null;

        return new KernelSearchResults<object>(this.GetResultsAsWebPageAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    async Task<KernelSearchResults<string>> ITextSearch<BingWebPage>.SearchAsync(string query, TextSearchOptions<BingWebPage>? searchOptions, CancellationToken cancellationToken)
    {
        var (top, skip, includeTotalCount, filters) = ExtractSearchParameters(searchOptions);
        BingSearchResponse<BingWebPage>? searchResponse = await this.ExecuteSearchAsync(query, top, skip, filters, cancellationToken).ConfigureAwait(false);

        long? totalCount = includeTotalCount ? searchResponse?.WebPages?.TotalEstimatedMatches : null;

        return new KernelSearchResults<string>(this.GetResultsAsStringAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    async Task<KernelSearchResults<TextSearchResult>> ITextSearch<BingWebPage>.GetTextSearchResultsAsync(string query, TextSearchOptions<BingWebPage>? searchOptions, CancellationToken cancellationToken)
    {
        var (top, skip, includeTotalCount, filters) = ExtractSearchParameters(searchOptions);
        BingSearchResponse<BingWebPage>? searchResponse = await this.ExecuteSearchAsync(query, top, skip, filters, cancellationToken).ConfigureAwait(false);

        long? totalCount = includeTotalCount ? searchResponse?.WebPages?.TotalEstimatedMatches : null;

        return new KernelSearchResults<TextSearchResult>(this.GetResultsAsTextSearchResultAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    async Task<KernelSearchResults<BingWebPage>> ITextSearch<BingWebPage>.GetSearchResultsAsync(string query, TextSearchOptions<BingWebPage>? searchOptions, CancellationToken cancellationToken)
    {
        var (top, skip, includeTotalCount, filters) = ExtractSearchParameters(searchOptions);
        BingSearchResponse<BingWebPage>? searchResponse = await this.ExecuteSearchAsync(query, top, skip, filters, cancellationToken).ConfigureAwait(false);

        long? totalCount = includeTotalCount ? searchResponse?.WebPages?.TotalEstimatedMatches : null;

        return new KernelSearchResults<BingWebPage>(
            this.GetResultsAsBingWebPageAsync(searchResponse, cancellationToken),
            totalCount,
            GetResultsMetadata(searchResponse));
    }

    #region private

    private readonly ILogger _logger;
    private readonly HttpClient _httpClient;
    private readonly string? _apiKey;
    private readonly Uri? _uri = null;
    private readonly ITextSearchStringMapper _stringMapper;
    private readonly ITextSearchResultMapper _resultMapper;
    private readonly BingTextSearchOptions? _options;

    private static readonly ITextSearchStringMapper s_defaultStringMapper = new DefaultTextSearchStringMapper();
    private static readonly ITextSearchResultMapper s_defaultResultMapper = new DefaultTextSearchResultMapper();

    // See https://learn.microsoft.com/en-us/bing/search-apis/bing-web-search/reference/query-parameters
    private static readonly string[] s_queryParameters = ["answerCount", "cc", "freshness", "mkt", "promote", "responseFilter", "safeSearch", "setLang", "textDecorations", "textFormat"];
    private static readonly string[] s_advancedSearchKeywords = ["contains", "ext", "filetype", "inanchor", "inbody", "intitle", "ip", "language", "loc", "location", "prefer", "site", "feed", "hasfeed", "url"];

    private const string DefaultUri = "https://api.bing.microsoft.com/v7.0/search";

    /// <summary>
    /// Extracts search parameters from generic <see cref="TextSearchOptions{TRecord}"/>.
    /// This is the primary entry point for the LINQ-based filtering path.
    /// </summary>
    private static (int Top, int Skip, bool IncludeTotalCount, List<(string FieldName, object Value)> Filters) ExtractSearchParameters<TRecord>(TextSearchOptions<TRecord>? searchOptions)
    {
        var top = searchOptions?.Top ?? 3;
        var skip = searchOptions?.Skip ?? 0;
        var includeTotalCount = searchOptions?.IncludeTotalCount ?? false;
        var filters = searchOptions?.Filter != null ? ExtractFiltersFromExpression(searchOptions.Filter) : [];
        return (top, skip, includeTotalCount, filters);
    }

    /// <summary>
    /// Walks a LINQ expression tree and extracts Bing API filter key-value pairs directly.
    /// Supports equality, inequality, Contains() method calls, and logical AND operator.
    /// </summary>
    /// <param name="linqExpression">The LINQ expression to walk.</param>
    /// <returns>A list of (FieldName, Value) pairs for Bing API filters.</returns>
    /// <exception cref="NotSupportedException">Thrown when the expression cannot be converted to Bing filters.</exception>
    private static List<(string FieldName, object Value)> ExtractFiltersFromExpression<TRecord>(Expression<Func<TRecord, bool>> linqExpression)
    {
        var filters = new List<(string FieldName, object Value)>();
        ProcessExpression(linqExpression.Body, filters);
        return filters;
    }

    /// <summary>
    /// Recursively processes LINQ expression nodes and builds Bing API filters.
    /// </summary>
    private static void ProcessExpression(Expression expression, List<(string FieldName, object Value)> filters)
    {
        switch (expression)
        {
            case BinaryExpression binaryExpr when binaryExpr.NodeType == ExpressionType.AndAlso:
                // Handle AND: page => page.Language == "en" && page.Name.Contains("AI")
                ProcessExpression(binaryExpr.Left, filters);
                ProcessExpression(binaryExpr.Right, filters);
                break;

            case BinaryExpression binaryExpr when binaryExpr.NodeType == ExpressionType.OrElse:
                // Handle OR: Currently not directly supported by TextSearchFilter
                // Bing API supports OR via multiple queries, but TextSearchFilter doesn't expose this
                throw new NotSupportedException(
                    "Logical OR (||) is not supported by Bing Text Search filters. " +
                    "Consider splitting into multiple search queries.");

            case UnaryExpression unaryExpr when unaryExpr.NodeType == ExpressionType.Not:
                // Handle NOT: page => !page.Language.Equals("en")
                throw new NotSupportedException(
                    "Logical NOT (!) is not directly supported by Bing Text Search advanced operators. " +
                    "Consider restructuring your filter to use positive conditions.");

            case BinaryExpression binaryExpr when binaryExpr.NodeType == ExpressionType.Equal:
                // Handle equality: page => page.Language == "en"
                ProcessEqualityExpression(binaryExpr, filters, isNegated: false);
                break;

            case BinaryExpression binaryExpr when binaryExpr.NodeType == ExpressionType.NotEqual:
                // Handle inequality: page => page.Language != "en"
                // Implemented via Bing's negation syntax (e.g., -language:en)
                ProcessEqualityExpression(binaryExpr, filters, isNegated: true);
                break;

            case MethodCallExpression methodExpr when methodExpr.Method.Name == "Contains":
                // Distinguish between instance method (String.Contains) and static method (Enumerable/MemoryExtensions.Contains)
                if (methodExpr.Object is MemberExpression)
                {
                    // Instance method: page.Name.Contains("value") - SUPPORTED
                    ProcessContainsExpression(methodExpr, filters);
                }
                else if (methodExpr.Object == null)
                {
                    // Static method: could be Enumerable.Contains (C# 13-) or MemoryExtensions.Contains (C# 14+)
                    // Bing API doesn't support OR logic, so collection Contains patterns are not supported
                    if (methodExpr.Method.DeclaringType == typeof(Enumerable) ||
                        (methodExpr.Method.DeclaringType == typeof(MemoryExtensions) && IsMemoryExtensionsContains(methodExpr)))
                    {
                        throw new NotSupportedException(
                            "Collection Contains filters (e.g., array.Contains(page.Property)) are not supported by Bing Search API. " +
                            "Bing's advanced search operators do not support OR logic across multiple values. " +
                            "Supported pattern: Property.Contains(\"value\") for string properties like Name, Snippet, or Url. " +
                            "For multiple value matching, consider alternative approaches or use a different search provider.");
                    }

                    throw new NotSupportedException(
                        $"Contains() method from {methodExpr.Method.DeclaringType?.Name} is not supported.");
                }
                else
                {
                    throw new NotSupportedException(
                        "Contains() must be called on a property (e.g., page.Name.Contains(\"value\")).");
                }
                break;

            default:
                throw new NotSupportedException(
                    $"Expression type '{expression.NodeType}' is not supported for Bing API filters. " +
                    "Supported patterns: equality (==), inequality (!=), Contains(), and logical AND (&&). " +
                    "Available Bing operators: " + string.Join(", ", s_advancedSearchKeywords));
        }
    }

    /// <summary>
    /// Processes equality and inequality expressions (property == value or property != value).
    /// </summary>
    /// <param name="binaryExpr">The binary expression to process.</param>
    /// <param name="filters">The list to add filter key-value pairs to.</param>
    /// <param name="isNegated">True if this is an inequality (!=) expression.</param>
    private static void ProcessEqualityExpression(BinaryExpression binaryExpr, List<(string FieldName, object Value)> filters, bool isNegated)
    {
        // Handle nullable properties with conversions (e.g., bool? == bool becomes Convert(property) == value)
        MemberExpression? memberExpr = binaryExpr.Left as MemberExpression;
        if (memberExpr == null && binaryExpr.Left is UnaryExpression unaryExpr && unaryExpr.NodeType == ExpressionType.Convert)
        {
            memberExpr = unaryExpr.Operand as MemberExpression;
        }

        // Handle conversions on the right side too
        ConstantExpression? constExpr = binaryExpr.Right as ConstantExpression;
        if (constExpr == null && binaryExpr.Right is UnaryExpression rightUnaryExpr && rightUnaryExpr.NodeType == ExpressionType.Convert)
        {
            constExpr = rightUnaryExpr.Operand as ConstantExpression;
        }

        if (memberExpr != null && constExpr != null)
        {
            string propertyName = memberExpr.Member.Name;
            object? value = constExpr.Value;

            string? bingFilterName = MapPropertyToBingFilter(propertyName);
            if (bingFilterName != null && value != null)
            {
                // Convert boolean values to lowercase strings for Bing API compatibility
                // CA1308: Using ToLowerInvariant() is intentional here as Bing API expects boolean values in lowercase format (true/false)
#pragma warning disable CA1308 // Normalize strings to uppercase
                string stringValue = value is bool boolValue ? boolValue.ToString().ToLowerInvariant() : value.ToString() ?? string.Empty;
#pragma warning restore CA1308 // Normalize strings to uppercase

                if (isNegated)
                {
                    // For inequality, wrap the value with a negation marker
                    // This will be processed in BuildQuery to prepend '-' to the advanced search operator
                    // Example: language:en becomes -language:en (excludes pages in English)
                    filters.Add((bingFilterName, $"-{stringValue}"));
                }
                else
                {
                    filters.Add((bingFilterName, stringValue));
                }
            }
            else if (value == null)
            {
                throw new NotSupportedException(
                    $"Null values are not supported in Bing API filters for property '{propertyName}'.");
            }
            else
            {
                throw new NotSupportedException(
                    $"Property '{propertyName}' cannot be mapped to Bing API filters. " +
                    "Supported properties: Language, Url, DisplayUrl, Name, Snippet, IsFamilyFriendly.");
            }
        }
        else
        {
            throw new NotSupportedException(
                "Equality expressions must be in the form 'property == value' or 'property != value'. " +
                "Complex expressions on the left or right side are not supported.");
        }
    }

    /// <summary>
    /// Processes Contains() method calls on string properties.
    /// Maps to Bing's advanced search operators like intitle:, inbody:, url:.
    /// </summary>
    private static void ProcessContainsExpression(MethodCallExpression methodExpr, List<(string FieldName, object Value)> filters)
    {
        // Contains can be called on a property: page.Name.Contains("value")
        // or on a collection: page.Tags.Contains("value")

        if (methodExpr.Object is MemberExpression memberExpr)
        {
            string propertyName = memberExpr.Member.Name;

            // Extract the search value from the Contains() argument
            if (methodExpr.Arguments.Count == 1 && methodExpr.Arguments[0] is ConstantExpression constExpr)
            {
                object? value = constExpr.Value;
                if (value == null)
                {
                    return; // Skip null values
                }

                // Map property to Bing filter with Contains semantic
                string? bingFilterOperator = MapPropertyToContainsFilter(propertyName);
                if (bingFilterOperator != null)
                {
                    // Use Bing's advanced search syntax: intitle:"value", inbody:"value", etc.
                    filters.Add((bingFilterOperator, value));
                }
                else
                {
                    throw new NotSupportedException(
                        $"Contains() on property '{propertyName}' is not supported by Bing API filters. " +
                        "Supported properties for Contains: Name (maps to intitle:), Snippet (maps to inbody:), Url (maps to url:).");
                }
            }
            else
            {
                throw new NotSupportedException(
                    "Contains() must have a single constant value argument. " +
                    "Complex expressions as arguments are not supported.");
            }
        }
        else
        {
            throw new NotSupportedException(
                "Contains() must be called on a property (e.g., page.Name.Contains(\"value\")). " +
                "Collection Contains patterns are not yet supported.");
        }
    }

    /// <summary>
    /// Determines if a MethodCallExpression is a MemoryExtensions.Contains call (C# 14 "first-class spans" feature).
    /// </summary>
    /// <param name="methodExpr">The method call expression to check.</param>
    /// <returns>True if this is a MemoryExtensions.Contains call with supported parameters; otherwise false.</returns>
    private static bool IsMemoryExtensionsContains(MethodCallExpression methodExpr)
    {
        // MemoryExtensions.Contains has 2-3 parameters:
        // - Contains<T>(ReadOnlySpan<T> span, T value)
        // - Contains<T>(ReadOnlySpan<T> span, T value, IEqualityComparer<T>? comparer)
        // We only support when comparer is null or omitted
        return methodExpr.Method.Name == nameof(MemoryExtensions.Contains) &&
               methodExpr.Arguments.Count >= 2 &&
               methodExpr.Arguments.Count <= 3 &&
               (methodExpr.Arguments.Count == 2 ||
                (methodExpr.Arguments.Count == 3 && methodExpr.Arguments[2] is ConstantExpression { Value: null }));
    }

    /// <summary>
    /// Maps BingWebPage property names to Bing API filter field names for equality operations.
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
            "ISFAMILYFRIENDLY" => "safeSearch", // Maps to safe search parameter

            // Direct API parameters (if we ever extend BingWebPage with metadata)
            "MKT" => "mkt",                    // Market/locale
            "FRESHNESS" => "freshness",        // Date freshness

            _ => null // Property not mappable to Bing filters
        };
    }

    /// <summary>
    /// Maps BingWebPage property names to Bing API advanced search operators for Contains operations.
    /// </summary>
    /// <param name="propertyName">The BingWebPage property name.</param>
    /// <returns>The corresponding Bing advanced search operator, or null if not mappable.</returns>
    private static string? MapPropertyToContainsFilter(string propertyName)
    {
        return propertyName.ToUpperInvariant() switch
        {
            // Map properties to Bing's contains-style operators
            "NAME" => "intitle",        // intitle:"search term" - title contains
            "SNIPPET" => "inbody",      // inbody:"search term" - body contains
            "URL" => "url",             // url:"search term" - URL contains
            "DISPLAYURL" => "site",     // site:domain.com - site contains

            _ => null // Property not mappable to Contains-style filters
        };
    }

    /// <summary>
    /// Execute a Bing search query and return the results.
    /// </summary>
    /// <param name="query">What to search for.</param>
    /// <param name="top">Number of results to return.</param>
    /// <param name="skip">Number of results to skip.</param>
    /// <param name="filters">Pre-extracted filter key-value pairs.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    private async Task<BingSearchResponse<BingWebPage>?> ExecuteSearchAsync(string query, int top, int skip, List<(string FieldName, object Value)> filters, CancellationToken cancellationToken = default)
    {
        using HttpResponseMessage response = await this.SendGetRequestAsync(query, top, skip, filters, cancellationToken).ConfigureAwait(false);

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
    /// <param name="top">Number of results to return.</param>
    /// <param name="skip">Number of results to skip.</param>
    /// <param name="filters">Pre-extracted filter key-value pairs.</param>
    /// <param name="cancellationToken">A cancellation token to cancel the request.</param>
    /// <returns>A <see cref="HttpResponseMessage"/> representing the response from the request.</returns>
    private async Task<HttpResponseMessage> SendGetRequestAsync(string query, int top, int skip, List<(string FieldName, object Value)> filters, CancellationToken cancellationToken = default)
    {
        if (top is <= 0 or > 50)
        {
            throw new ArgumentOutOfRangeException(nameof(top), top, "count value must be greater than 0 and have a maximum value of 50.");
        }

        Uri uri = new($"{this._uri}?q={this.BuildQuery(query, top, skip, filters)}");

        using var httpRequestMessage = new HttpRequestMessage(HttpMethod.Get, uri);

        if (!string.IsNullOrEmpty(this._apiKey))
        {
            httpRequestMessage.Headers.Add("Ocp-Apim-Subscription-Key", this._apiKey);
        }

        return await this._httpClient.SendWithSuccessCheckAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Return the search results as instances of <see cref="object"/>.
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
    /// Return the search results as strongly-typed <see cref="BingWebPage"/> instances.
    /// </summary>
    /// <param name="searchResponse">Response containing the web pages matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<BingWebPage> GetResultsAsBingWebPageAsync(BingSearchResponse<BingWebPage>? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
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

#pragma warning disable CS0618 // FilterClause is obsolete - backward compatibility shim for legacy ITextSearch
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
            }
        }
        return filters;
    }
#pragma warning restore CS0618

    /// <summary>
    /// Build a Bing API query string from pre-extracted filter key-value pairs.
    /// Both LINQ and legacy paths converge here after producing the same (FieldName, Value) list.
    /// </summary>
    /// <param name="query">The query.</param>
    /// <param name="top">Number of results to return.</param>
    /// <param name="skip">Number of results to skip.</param>
    /// <param name="filters">Pre-extracted filter key-value pairs.</param>
    private string BuildQuery(string query, int top, int skip, List<(string FieldName, object Value)> filters)
    {
        StringBuilder fullQuery = new();
        fullQuery.Append(Uri.EscapeDataString(query.Trim()));
        StringBuilder queryParams = new();
        HashSet<string> processedQueryParams = new(StringComparer.OrdinalIgnoreCase);

        foreach (var (fieldName, value) in filters)
        {
            // Check if value starts with '-' indicating negation (for inequality != operator)
            string? valueStr = value?.ToString();
            bool isNegated = valueStr?.StartsWith("-", StringComparison.Ordinal) == true;
            string actualValue = isNegated && valueStr != null ? valueStr.Substring(1) : valueStr ?? string.Empty;

            if (s_advancedSearchKeywords.Contains(fieldName, StringComparer.OrdinalIgnoreCase) && value is not null)
            {
                // For advanced search keywords, prepend '-' if negated to exclude results
                string prefix = isNegated ? "-" : "";
                fullQuery.Append($"+{prefix}{fieldName}%3A").Append(Uri.EscapeDataString(actualValue));
            }
            else if (s_queryParameters.Contains(fieldName, StringComparer.OrdinalIgnoreCase) && value is not null)
            {
                // Query parameters do not support negation (!=) - throw if attempted
                if (isNegated)
                {
                    throw new ArgumentException(
                        $"Negation (!= operator) is not supported for query parameter '{fieldName}'. " +
                        $"Negation only works with advanced search operators: {string.Join(", ", s_advancedSearchKeywords)}.",
                        nameof(filters));
                }

                string? queryParam = s_queryParameters.FirstOrDefault(s => s.Equals(fieldName, StringComparison.OrdinalIgnoreCase));
                queryParams.Append('&').Append(queryParam!).Append('=').Append(Uri.EscapeDataString(actualValue));
                processedQueryParams.Add(queryParam!);
            }
            else
            {
                throw new ArgumentException($"Unknown equality filter clause field name '{fieldName}', must be one of {string.Join(",", s_queryParameters)},{string.Join(",", s_advancedSearchKeywords)}", nameof(filters));
            }
        }

        // Apply default search parameters from constructor options (only for params not already set by filter)
        this.AppendDefaultSearchParameters(queryParams, processedQueryParams);

        fullQuery.Append($"&count={top}&offset={skip}{queryParams}");

        return fullQuery.ToString();
    }

    /// <summary>
    /// Appends default Bing search parameters from <see cref="BingTextSearchOptions"/> to the query.
    /// Parameters already set by filter clauses are not overridden.
    /// </summary>
    private void AppendDefaultSearchParameters(StringBuilder queryParams, HashSet<string> processedQueryParams)
    {
        AppendIfNotSet(queryParams, processedQueryParams, "mkt", this._options?.Market);
        AppendIfNotSet(queryParams, processedQueryParams, "freshness", this._options?.Freshness);
        AppendIfNotSet(queryParams, processedQueryParams, "safeSearch", this._options?.SafeSearch);
        AppendIfNotSet(queryParams, processedQueryParams, "cc", this._options?.CountryCode);
        AppendIfNotSet(queryParams, processedQueryParams, "setLang", this._options?.SetLanguage);
        AppendIfNotSet(queryParams, processedQueryParams, "responseFilter", this._options?.ResponseFilter);
        AppendIfNotSet(queryParams, processedQueryParams, "promote", this._options?.Promote);
        AppendIfNotSet(queryParams, processedQueryParams, "textFormat", this._options?.TextFormat);

        if (this._options?.AnswerCount is int answerCount && !processedQueryParams.Contains("answerCount"))
        {
            queryParams.Append("&answerCount=").Append(answerCount);
        }

        if (this._options?.TextDecorations is bool textDecorations && !processedQueryParams.Contains("textDecorations"))
        {
#pragma warning disable CA1308 // Bing API requires lowercase boolean values
            queryParams.Append("&textDecorations=").Append(textDecorations.ToString().ToLowerInvariant());
#pragma warning restore CA1308
        }
    }

    private static void AppendIfNotSet(StringBuilder queryParams, HashSet<string> processedQueryParams, string paramName, string? value)
    {
        if (value is not null && !processedQueryParams.Contains(paramName))
        {
            queryParams.Append('&').Append(paramName).Append('=').Append(Uri.EscapeDataString(value));
        }
    }

    #endregion
}
