// Copyright (c) Microsoft. All rights reserved.

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
#pragma warning disable CS0618 // ITextSearch is obsolete - this class provides backward compatibility
public sealed class TavilyTextSearch : ITextSearch, ITextSearch<TavilyWebPage>
#pragma warning restore CS0618
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
        TavilySearchResponse? searchResponse = await this.ExecuteSearchAsync(query, searchOptions, cancellationToken).ConfigureAwait(false);

        long? totalCount = null;

        return new KernelSearchResults<string>(this.GetResultsAsStringAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<TextSearchResult>> GetTextSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        searchOptions ??= new TextSearchOptions();
        TavilySearchResponse? searchResponse = await this.ExecuteSearchAsync(query, searchOptions, cancellationToken).ConfigureAwait(false);

        long? totalCount = null;

        return new KernelSearchResults<TextSearchResult>(this.GetResultsAsTextSearchResultAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<object>> GetSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        searchOptions ??= new TextSearchOptions();
        TavilySearchResponse? searchResponse = await this.ExecuteSearchAsync(query, searchOptions, cancellationToken).ConfigureAwait(false);

        long? totalCount = null;

        return new KernelSearchResults<object>(this.GetSearchResultsAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    #region Generic ITextSearch<TavilyWebPage> Implementation

    /// <inheritdoc/>
    async Task<KernelSearchResults<string>> ITextSearch<TavilyWebPage>.SearchAsync(string query, TextSearchOptions<TavilyWebPage>? searchOptions, CancellationToken cancellationToken)
    {
        var legacyOptions = this.ConvertToLegacyOptions(searchOptions);
        TavilySearchResponse? searchResponse = await this.ExecuteSearchAsync(query, legacyOptions, cancellationToken).ConfigureAwait(false);

        long? totalCount = null;

        return new KernelSearchResults<string>(this.GetResultsAsStringAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    async Task<KernelSearchResults<TextSearchResult>> ITextSearch<TavilyWebPage>.GetTextSearchResultsAsync(string query, TextSearchOptions<TavilyWebPage>? searchOptions, CancellationToken cancellationToken)
    {
        var legacyOptions = this.ConvertToLegacyOptions(searchOptions);
        TavilySearchResponse? searchResponse = await this.ExecuteSearchAsync(query, legacyOptions, cancellationToken).ConfigureAwait(false);

        long? totalCount = null;

        return new KernelSearchResults<TextSearchResult>(this.GetResultsAsTextSearchResultAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    async Task<KernelSearchResults<object>> ITextSearch<TavilyWebPage>.GetSearchResultsAsync(string query, TextSearchOptions<TavilyWebPage>? searchOptions, CancellationToken cancellationToken)
    {
        var legacyOptions = this.ConvertToLegacyOptions(searchOptions);
        TavilySearchResponse? searchResponse = await this.ExecuteSearchAsync(query, legacyOptions, cancellationToken).ConfigureAwait(false);

        long? totalCount = null;

        return new KernelSearchResults<object>(this.GetResultsAsWebPageAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    #endregion

    #region LINQ-to-Tavily Conversion Logic

    /// <summary>
    /// Converts generic TextSearchOptions with LINQ filtering to legacy TextSearchOptions.
    /// </summary>
    /// <param name="options">The generic search options with LINQ filter.</param>
    /// <returns>Legacy TextSearchOptions with converted filters.</returns>
    private TextSearchOptions ConvertToLegacyOptions<TRecord>(TextSearchOptions<TRecord>? options)
    {
        if (options == null)
        {
            return new TextSearchOptions();
        }

        var legacyOptions = new TextSearchOptions
        {
            Top = options.Top,
            Skip = options.Skip,
            IncludeTotalCount = options.IncludeTotalCount
        };

        // Convert LINQ expression to TextSearchFilter if present
        if (options.Filter != null)
        {
            try
            {
                var convertedFilter = ConvertLinqExpressionToTavilyFilter(options.Filter);
                legacyOptions = new TextSearchOptions
                {
                    Top = options.Top,
                    Skip = options.Skip,
                    IncludeTotalCount = options.IncludeTotalCount,
                    Filter = convertedFilter
                };
            }
            catch (NotSupportedException ex)
            {
                this._logger.LogWarning("LINQ expression not fully supported by Tavily API, performing search without some filters: {Message}", ex.Message);
                // Continue with basic search - graceful degradation
            }
        }

        return legacyOptions;
    }

    /// <summary>
    /// Converts a LINQ expression to Tavily-compatible TextSearchFilter.
    /// </summary>
    /// <param name="linqExpression">The LINQ expression to convert.</param>
    /// <returns>A TextSearchFilter with Tavily-compatible filter clauses.</returns>
    private static TextSearchFilter ConvertLinqExpressionToTavilyFilter<TRecord>(Expression<Func<TRecord, bool>> linqExpression)
    {
        var filter = new TextSearchFilter();
        var filterClauses = new List<FilterClause>();

        // Analyze the LINQ expression and convert to filter clauses
        AnalyzeExpression(linqExpression.Body, filterClauses);

        // Validate and add clauses that are supported by Tavily
        foreach (var clause in filterClauses)
        {
            if (clause is EqualToFilterClause equalityClause)
            {
                var mappedFieldName = MapPropertyToTavilyFilter(equalityClause.FieldName);
                if (mappedFieldName != null)
                {
                    filter.Equality(mappedFieldName, equalityClause.Value);
                }
                else
                {
                    throw new NotSupportedException(
                        $"Property '{equalityClause.FieldName}' cannot be mapped to Tavily API filters. " +
                        $"Supported properties: {string.Join(", ", s_validFieldNames)}. " +
                        "Example: page => page.Topic == \"general\" && page.TimeRange == \"week\"");
                }
            }
        }

        return filter;
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

    // TODO: Consider extracting LINQ expression analysis logic to a shared utility class
    // to reduce duplication across text search connectors (Brave, Tavily, etc.).
    // See code review for details.
    /// <summary>
    /// Analyzes a LINQ expression and extracts filter clauses.
    /// </summary>
    /// <param name="expression">The expression to analyze.</param>
    /// <param name="filterClauses">The list to add extracted filter clauses to.</param>
    private static void AnalyzeExpression(Expression expression, List<FilterClause> filterClauses)
    {
        switch (expression)
        {
            case BinaryExpression binaryExpr:
                if (binaryExpr.NodeType == ExpressionType.AndAlso)
                {
                    // Handle AND expressions by recursively analyzing both sides
                    AnalyzeExpression(binaryExpr.Left, filterClauses);
                    AnalyzeExpression(binaryExpr.Right, filterClauses);
                }
                else if (binaryExpr.NodeType == ExpressionType.OrElse)
                {
                    // Handle OR expressions by recursively analyzing both sides
                    // Note: OR results in multiple filter values for the same property (especially for domains)
                    AnalyzeExpression(binaryExpr.Left, filterClauses);
                    AnalyzeExpression(binaryExpr.Right, filterClauses);
                }
                else if (binaryExpr.NodeType == ExpressionType.Equal)
                {
                    // Handle equality expressions
                    ExtractEqualityClause(binaryExpr, filterClauses);
                }
                else if (binaryExpr.NodeType == ExpressionType.NotEqual)
                {
                    // Handle inequality expressions (property != value)
                    // This is supported as a negation pattern
                    ExtractInequalityClause(binaryExpr, filterClauses);
                }
                else
                {
                    throw new NotSupportedException($"Binary expression type '{binaryExpr.NodeType}' is not supported. Supported operators: AndAlso (&&), OrElse (||), Equal (==), NotEqual (!=).");
                }
                break;

            case UnaryExpression unaryExpr when unaryExpr.NodeType == ExpressionType.Not:
                // Handle NOT expressions (negation)
                AnalyzeNotExpression(unaryExpr, filterClauses);
                break;

            case MethodCallExpression methodCall:
                // Handle method calls like Contains, StartsWith, etc.
                ExtractMethodCallClause(methodCall, filterClauses);
                break;

            default:
                throw new NotSupportedException($"Expression type '{expression.NodeType}' is not supported in Tavily search filters.");
        }
    }

    /// <summary>
    /// Extracts an equality filter clause from a binary equality expression.
    /// </summary>
    /// <param name="binaryExpr">The binary equality expression.</param>
    /// <param name="filterClauses">The list to add the extracted clause to.</param>
    private static void ExtractEqualityClause(BinaryExpression binaryExpr, List<FilterClause> filterClauses)
    {
        string? propertyName = null;
        object? value = null;

        // Determine which side is the property and which is the value
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
            filterClauses.Add(new EqualToFilterClause(propertyName, value));
        }
        else
        {
            throw new NotSupportedException("Unable to extract property name and value from equality expression.");
        }
    }

    /// <summary>
    /// Extracts an inequality filter clause from a binary not-equal expression.
    /// </summary>
    /// <param name="binaryExpr">The binary not-equal expression.</param>
    /// <param name="filterClauses">The list to add the extracted clause to.</param>
    private static void ExtractInequalityClause(BinaryExpression binaryExpr, List<FilterClause> filterClauses)
    {
        // Note: Inequality is tracked but handled differently depending on the property
        // For now, we log a warning that inequality filtering may not work as expected
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
            // Add a marker for inequality - this will need special handling in conversion
            // For now, we don't add it to filter clauses as Tavily API doesn't support direct negation
            throw new NotSupportedException($"Inequality operator (!=) is not directly supported for property '{propertyName}'. Use NOT operator instead: !(page.{propertyName} == value).");
        }

        throw new NotSupportedException("Unable to extract property name and value from inequality expression.");
    }

    /// <summary>
    /// Analyzes a NOT (negation) expression.
    /// </summary>
    /// <param name="unaryExpr">The unary NOT expression.</param>
    /// <param name="filterClauses">The list to add extracted filter clauses to.</param>
    private static void AnalyzeNotExpression(UnaryExpression unaryExpr, List<FilterClause> filterClauses)
    {
        // NOT expressions are complex for web search APIs
        // We support simple cases like !(page.Topic == "general")
        if (unaryExpr.Operand is BinaryExpression binaryExpr && binaryExpr.NodeType == ExpressionType.Equal)
        {
            // This is !(property == value), which we can handle for some properties
            throw new NotSupportedException("NOT operator (!) with equality is not directly supported. Most web search APIs don't support negative filtering.");
        }

        throw new NotSupportedException("NOT operator (!) is only supported with simple equality expressions.");
    }

    /// <summary>
    /// Extracts a filter clause from a method call expression (e.g., Contains, StartsWith).
    /// </summary>
    /// <param name="methodCall">The method call expression.</param>
    /// <param name="filterClauses">The list to add the extracted clause to.</param>
    private static void ExtractMethodCallClause(MethodCallExpression methodCall, List<FilterClause> filterClauses)
    {
        if (methodCall.Method.Name == "Contains")
        {
            // Check if this is property.Contains(value) or array.Contains(property)
            if (methodCall.Object is MemberExpression member)
            {
                // This is property.Contains(value) - e.g., page.IncludeDomain.Contains("wikipedia.org")
                var propertyName = member.Member.Name;
                var value = ExtractValue(methodCall.Arguments[0]);

                if (value != null)
                {
                    // For Contains, we'll map it to equality for domains (Tavily supports domain filtering)
                    if (propertyName.EndsWith("Domain", StringComparison.OrdinalIgnoreCase))
                    {
                        filterClauses.Add(new EqualToFilterClause(propertyName, value));
                    }
                    else
                    {
                        throw new NotSupportedException($"Contains method is only supported for domain properties (IncludeDomain, ExcludeDomain), not '{propertyName}'.");
                    }
                }
            }
            else if (methodCall.Object == null && methodCall.Arguments.Count == 2)
            {
                // This is array.Contains(property) - e.g., new[] { "general", "news" }.Contains(page.Topic)
                // This is an extension method call where the first argument is the array
                var arrayExpr = methodCall.Arguments[0];
                var propertyExpr = methodCall.Arguments[1];

                if (propertyExpr is MemberExpression propertyMember)
                {
                    var propertyName = propertyMember.Member.Name;
                    var arrayValue = ExtractValue(arrayExpr);

                    if (arrayValue is System.Collections.IEnumerable enumerable)
                    {
                        // Convert to OR expressions - each value becomes an equality clause
                        foreach (var value in enumerable)
                        {
                            if (value != null)
                            {
                                filterClauses.Add(new EqualToFilterClause(propertyName, value));
                            }
                        }
                    }
                    else
                    {
                        throw new NotSupportedException($"Contains argument must be an array or collection, got: {arrayValue?.GetType().Name}");
                    }
                }
                else
                {
                    throw new NotSupportedException("Contains with inline collection requires a property reference as the second argument.");
                }
            }
            else
            {
                throw new NotSupportedException("Unsupported Contains expression format.");
            }
        }
        else
        {
            throw new NotSupportedException($"Method '{methodCall.Method.Name}' is not supported in Tavily search filters. Only 'Contains' is supported.");
        }
    }

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
            MemberExpression member when member.Expression is ConstantExpression constantExpr =>
                member.Member switch
                {
                    System.Reflection.FieldInfo field => field.GetValue(constantExpr.Value),
                    System.Reflection.PropertyInfo property => property.GetValue(constantExpr.Value),
                    _ => null
                },
            _ => Expression.Lambda(expression).Compile().DynamicInvoke()
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
    /// <param name="searchOptions">Search options.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    private async Task<TavilySearchResponse?> ExecuteSearchAsync(string query, TextSearchOptions searchOptions, CancellationToken cancellationToken)
    {
        using HttpResponseMessage response = await this.SendGetRequestAsync(query, searchOptions, cancellationToken).ConfigureAwait(false);

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
    /// <param name="searchOptions">The search options.</param>
    /// <param name="cancellationToken">A cancellation token to cancel the request.</param>
    /// <returns>A <see cref="HttpResponseMessage"/> representing the response from the request.</returns>
    private async Task<HttpResponseMessage> SendGetRequestAsync(string query, TextSearchOptions searchOptions, CancellationToken cancellationToken)
    {
        if (searchOptions.Top is <= 0 or > 50)
        {
            throw new ArgumentOutOfRangeException(nameof(searchOptions), searchOptions, $"{nameof(searchOptions)} count value must be greater than 0 and have a maximum value of 50.");
        }

        var requestContent = this.BuildRequestContent(query, searchOptions);

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
    private async IAsyncEnumerable<object> GetResultsAsWebPageAsync(TavilySearchResponse? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
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

#pragma warning disable CS0618 // FilterClause is obsolete
    /// <summary>
    /// Build a query string from the <see cref="TextSearchOptions"/>
    /// </summary>
    /// <param name="query">The query.</param>
    /// <param name="searchOptions">The search options.</param>
    private TavilySearchRequest BuildRequestContent(string query, TextSearchOptions searchOptions)
    {
        string? topic = null;
        string? timeRange = null;
        int? days = null;
        int? maxResults = searchOptions.Top - searchOptions.Skip;
        IList<string>? includeDomains = null;
        IList<string>? excludeDomains = null;

        if (searchOptions.Filter is not null)
        {
            var filterClauses = searchOptions.Filter.FilterClauses;

            foreach (var filterClause in filterClauses)
            {
                if (filterClause is EqualToFilterClause equalityFilterClause)
                {
                    if (equalityFilterClause.FieldName.Equals(Topic, StringComparison.OrdinalIgnoreCase) && equalityFilterClause.Value is not null)
                    {
                        topic = equalityFilterClause.Value.ToString()!;
                    }
                    else if (equalityFilterClause.FieldName.Equals(TimeRange, StringComparison.OrdinalIgnoreCase) && equalityFilterClause.Value is not null)
                    {
                        timeRange = equalityFilterClause.Value.ToString()!;
                    }
                    else if (equalityFilterClause.FieldName.Equals(Days, StringComparison.OrdinalIgnoreCase) && equalityFilterClause.Value is not null)
                    {
                        days = Convert.ToInt32(equalityFilterClause.Value);
                    }
                    else if (equalityFilterClause.FieldName.Equals(IncludeDomain, StringComparison.OrdinalIgnoreCase) && equalityFilterClause.Value is not null)
                    {
                        var includeDomain = equalityFilterClause.Value.ToString()!;
                        includeDomains ??= [];
                        includeDomains.Add(includeDomain);
                    }
                    else if (equalityFilterClause.FieldName.Equals(ExcludeDomain, StringComparison.OrdinalIgnoreCase) && equalityFilterClause.Value is not null)
                    {
                        var excludeDomain = equalityFilterClause.Value.ToString()!;
                        excludeDomains ??= [];
                        excludeDomains.Add(excludeDomain);
                    }
                    else
                    {
                        throw new ArgumentException($"Unknown equality filter clause field name '{equalityFilterClause.FieldName}', must be one of {string.Join(",", s_validFieldNames)}", nameof(searchOptions));
                    }
                }
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
#pragma warning restore CS0618 // FilterClause is obsolete

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
