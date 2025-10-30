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

namespace Microsoft.SemanticKernel.Plugins.Web.Brave;

/// <summary>
/// A Brave Text Search implementation that can be used to perform searches using the Brave Web Search API.
/// </summary>
#pragma warning disable CS0618 // ITextSearch is obsolete - this class provides backward compatibility
public sealed class BraveTextSearch : ITextSearch, ITextSearch<BraveWebPage>
#pragma warning restore CS0618
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

    #region Generic ITextSearch<BraveWebPage> Implementation

    /// <inheritdoc/>
    async Task<KernelSearchResults<string>> ITextSearch<BraveWebPage>.SearchAsync(string query, TextSearchOptions<BraveWebPage>? searchOptions, CancellationToken cancellationToken)
    {
        var legacyOptions = this.ConvertToLegacyOptions(searchOptions);
        BraveSearchResponse<BraveWebResult>? searchResponse = await this.ExecuteSearchAsync(query, legacyOptions, cancellationToken).ConfigureAwait(false);

        long? totalCount = legacyOptions.IncludeTotalCount ? searchResponse?.Web?.Results.Count : null;

        return new KernelSearchResults<string>(this.GetResultsAsStringAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    async Task<KernelSearchResults<TextSearchResult>> ITextSearch<BraveWebPage>.GetTextSearchResultsAsync(string query, TextSearchOptions<BraveWebPage>? searchOptions, CancellationToken cancellationToken)
    {
        var legacyOptions = this.ConvertToLegacyOptions(searchOptions);
        BraveSearchResponse<BraveWebResult>? searchResponse = await this.ExecuteSearchAsync(query, legacyOptions, cancellationToken).ConfigureAwait(false);

        long? totalCount = legacyOptions.IncludeTotalCount ? searchResponse?.Web?.Results.Count : null;

        return new KernelSearchResults<TextSearchResult>(this.GetResultsAsTextSearchResultAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    async Task<KernelSearchResults<object>> ITextSearch<BraveWebPage>.GetSearchResultsAsync(string query, TextSearchOptions<BraveWebPage>? searchOptions, CancellationToken cancellationToken)
    {
        var legacyOptions = this.ConvertToLegacyOptions(searchOptions);
        BraveSearchResponse<BraveWebResult>? searchResponse = await this.ExecuteSearchAsync(query, legacyOptions, cancellationToken).ConfigureAwait(false);

        long? totalCount = legacyOptions.IncludeTotalCount ? searchResponse?.Web?.Results.Count : null;

        return new KernelSearchResults<object>(this.GetResultsAsBraveWebPageAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    #endregion

    #region LINQ-to-Brave Conversion Logic

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
                var convertedFilter = ConvertLinqExpressionToBraveFilter(options.Filter);
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
                this._logger.LogWarning("LINQ expression not fully supported by Brave API, performing search without some filters: {Message}", ex.Message);
                // Continue with basic search - graceful degradation
            }
        }

        return legacyOptions;
    }

    /// <summary>
    /// Converts a LINQ expression to Brave-compatible TextSearchFilter.
    /// </summary>
    /// <param name="linqExpression">The LINQ expression to convert.</param>
    /// <returns>A TextSearchFilter with Brave-compatible filter clauses.</returns>
    private static TextSearchFilter ConvertLinqExpressionToBraveFilter<TRecord>(Expression<Func<TRecord, bool>> linqExpression)
    {
        var filter = new TextSearchFilter();
        var filterClauses = new List<FilterClause>();

        // Analyze the LINQ expression and convert to filter clauses
        AnalyzeExpression(linqExpression.Body, filterClauses);

        // Validate and add clauses that are supported by Brave
        foreach (var clause in filterClauses)
        {
            if (clause is EqualToFilterClause equalityClause)
            {
                var mappedFieldName = MapPropertyToBraveFilter(equalityClause.FieldName);
                if (mappedFieldName != null)
                {
                    filter.Equality(mappedFieldName, equalityClause.Value);
                }
                else
                {
                    throw new NotSupportedException(
                        $"Property '{equalityClause.FieldName}' cannot be mapped to Brave API filters. " +
                        $"Supported properties: {string.Join(", ", s_queryParameters)}. " +
                        "Example: page => page.Country == \"US\" && page.SafeSearch == \"moderate\"");
                }
            }
        }

        return filter;
    }

    /// <summary>
    /// Maps BraveWebPage property names to Brave API filter parameter names.
    /// </summary>
    /// <param name="propertyName">The property name from BraveWebPage.</param>
    /// <returns>The corresponding Brave API parameter name, or null if not mappable.</returns>
    private static string? MapPropertyToBraveFilter(string propertyName) =>
        propertyName.ToUpperInvariant() switch
        {
            "COUNTRY" => BraveParamCountry,
            "SEARCHLANG" => BraveParamSearchLang,
            "UILANG" => BraveParamUiLang,
            "SAFESEARCH" => BraveParamSafeSearch,
            "TEXTDECORATIONS" => BraveParamTextDecorations,
            "SPELLCHECK" => BraveParamSpellCheck,
            "RESULTFILTER" => BraveParamResultFilter,
            "UNITS" => BraveParamUnits,
            "EXTRASNIPPETS" => BraveParamExtraSnippets,
            _ => null // Property not mappable to Brave filters
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
                    // Note: OR results in multiple filter values for the same property
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
                throw new NotSupportedException($"Expression type '{expression.NodeType}' is not supported in Brave search filters.");
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
            // For now, we don't add it to filter clauses as Brave API doesn't support direct negation
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
        // We support simple cases like !(page.SafeSearch == "off")
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
            // Handle C# 14 MemoryExtensions.Contains compatibility issue
            // In C# 14+, array.Contains(property) may resolve to MemoryExtensions.Contains instead of Enumerable.Contains
            if (methodCall.Object == null && IsMemoryExtensionsContains(methodCall))
            {
                throw new NotSupportedException(
                    "Collection Contains filters (e.g., array.Contains(page.Property)) using MemoryExtensions.Contains (C# 14+) are not supported by Brave Search API. " +
                    "Brave's API does not support OR logic across multiple values. " +
                    "Consider either: (1) performing multiple separate searches for each value, or " +
                    "(2) retrieving broader results and filtering on the client side. " +
                    "Note: This occurs when using C# 14+ language features with span-based Contains methods.");
            }

            // Check if this is property.Contains(value) or array.Contains(property)
            if (methodCall.Object is MemberExpression member)
            {
                // This is property.Contains(value) - e.g., page.ResultFilter.Contains("web")
                var propertyName = member.Member.Name;
                var value = ExtractValue(methodCall.Arguments[0]);

                if (value != null)
                {
                    // For Contains, we'll map it to equality for certain properties
                    if (propertyName.Equals("ResultFilter", StringComparison.OrdinalIgnoreCase))
                    {
                        filterClauses.Add(new EqualToFilterClause(propertyName, value));
                    }
                    else
                    {
                        throw new NotSupportedException($"Contains method is only supported for ResultFilter property, not '{propertyName}'.");
                    }
                }
            }
            else if (methodCall.Object == null && methodCall.Arguments.Count == 2)
            {
                // This is array.Contains(property) - e.g., new[] { "US", "GB" }.Contains(page.Country)
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
            throw new NotSupportedException($"Method '{methodCall.Method.Name}' is not supported in Brave search filters. Only 'Contains' is supported.");
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
    private readonly ITextSearchStringMapper _stringMapper;
    private readonly ITextSearchResultMapper _resultMapper;

    private static readonly ITextSearchStringMapper s_defaultStringMapper = new DefaultTextSearchStringMapper();
    private static readonly ITextSearchResultMapper s_defaultResultMapper = new DefaultTextSearchResultMapper();

    // Constants for Brave API parameter names
    private const string BraveParamCountry = "country";
    private const string BraveParamSearchLang = "search_lang";
    private const string BraveParamUiLang = "ui_lang";
    private const string BraveParamSafeSearch = "safesearch";
    private const string BraveParamTextDecorations = "text_decorations";
    private const string BraveParamSpellCheck = "spellcheck";
    private const string BraveParamResultFilter = "result_filter";
    private const string BraveParamUnits = "units";
    private const string BraveParamExtraSnippets = "extra_snippets";

    // See https://api-dashboard.search.brave.com/app/documentation/web-search/query#WebSearchAPIQueryParameters
    private static readonly string[] s_queryParameters = [BraveParamCountry, BraveParamSearchLang, BraveParamUiLang, BraveParamSafeSearch, BraveParamTextDecorations, BraveParamSpellCheck, BraveParamResultFilter, BraveParamUnits, BraveParamExtraSnippets];

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
    /// Return the search results as instances of <see cref="BraveWebPage"/>.
    /// </summary>
    /// <param name="searchResponse">Response containing the web pages matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<object> GetResultsAsBraveWebPageAsync(BraveSearchResponse<BraveWebResult>? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse is null) { yield break; }

        if (searchResponse.Web?.Results is { Count: > 0 } webResults)
        {
            foreach (var webPage in webResults)
            {
                yield return BraveWebPage.FromWebResult(webPage);
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

    /// <summary>
    /// Determines if a method call expression is a MemoryExtensions.Contains call (C# 14+ compatibility).
    /// In C# 14+, array.Contains(property) may resolve to MemoryExtensions.Contains instead of Enumerable.Contains.
    /// </summary>
    /// <param name="methodCall">The method call expression to check.</param>
    /// <returns>True if this is a MemoryExtensions.Contains call, false otherwise.</returns>
    private static bool IsMemoryExtensionsContains(MethodCallExpression methodCall)
    {
        // Check if this is a static method call (Object is null)
        if (methodCall.Object != null)
        {
            return false;
        }

        // Check if it's MemoryExtensions.Contains
        if (methodCall.Method.DeclaringType?.Name != "MemoryExtensions")
        {
            return false;
        }

        // MemoryExtensions.Contains has 2-3 parameters: (ReadOnlySpan<T>, T) or (ReadOnlySpan<T>, T, IEqualityComparer<T>)
        if (methodCall.Arguments.Count < 2 || methodCall.Arguments.Count > 3)
        {
            return false;
        }

        // For our text search scenarios, we don't support span comparers
        if (methodCall.Arguments.Count == 3)
        {
            throw new NotSupportedException(
                "MemoryExtensions.Contains with custom IEqualityComparer is not supported. " +
                "Use simple array.Contains(property) expressions without custom comparers.");
        }

        return true;
    }
    #endregion
}
