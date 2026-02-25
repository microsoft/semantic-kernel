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
        var filters = ExtractFiltersFromLegacy(searchOptions.Filter);
        BraveSearchResponse<BraveWebResult>? searchResponse = await this.ExecuteSearchAsync(query, searchOptions.Top, searchOptions.Skip, filters, cancellationToken).ConfigureAwait(false);

        long? totalCount = searchOptions.IncludeTotalCount ? searchResponse?.Web?.Results.Count : null;

        return new KernelSearchResults<string>(this.GetResultsAsStringAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<TextSearchResult>> GetTextSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = new CancellationToken())
    {
        searchOptions ??= new TextSearchOptions();
        var filters = ExtractFiltersFromLegacy(searchOptions.Filter);
        BraveSearchResponse<BraveWebResult>? searchResponse = await this.ExecuteSearchAsync(query, searchOptions.Top, searchOptions.Skip, filters, cancellationToken).ConfigureAwait(false);

        long? totalCount = searchOptions.IncludeTotalCount ? searchResponse?.Web?.Results.Count : null;

        return new KernelSearchResults<TextSearchResult>(this.GetResultsAsTextSearchResultAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<object>> GetSearchResultsAsync(string query, TextSearchOptions? searchOptions = null,
        CancellationToken cancellationToken = new CancellationToken())
    {
        searchOptions ??= new TextSearchOptions();
        var filters = ExtractFiltersFromLegacy(searchOptions.Filter);
        BraveSearchResponse<BraveWebResult>? searchResponse = await this.ExecuteSearchAsync(query, searchOptions.Top, searchOptions.Skip, filters, cancellationToken).ConfigureAwait(false);

        long? totalCount = searchOptions.IncludeTotalCount ? searchResponse?.Web?.Results.Count : null;

        return new KernelSearchResults<object>(this.GetResultsAsObjectAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    #region Generic ITextSearch<BraveWebPage> Implementation

    /// <inheritdoc/>
    async Task<KernelSearchResults<string>> ITextSearch<BraveWebPage>.SearchAsync(string query, TextSearchOptions<BraveWebPage>? searchOptions, CancellationToken cancellationToken)
    {
        var (modifiedQuery, top, skip, includeTotalCount, filters) = ExtractSearchParameters(query, searchOptions);
        BraveSearchResponse<BraveWebResult>? searchResponse = await this.ExecuteSearchAsync(modifiedQuery, top, skip, filters, cancellationToken).ConfigureAwait(false);

        long? totalCount = includeTotalCount ? searchResponse?.Web?.Results.Count : null;

        return new KernelSearchResults<string>(this.GetResultsAsStringAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    async Task<KernelSearchResults<TextSearchResult>> ITextSearch<BraveWebPage>.GetTextSearchResultsAsync(string query, TextSearchOptions<BraveWebPage>? searchOptions, CancellationToken cancellationToken)
    {
        var (modifiedQuery, top, skip, includeTotalCount, filters) = ExtractSearchParameters(query, searchOptions);
        BraveSearchResponse<BraveWebResult>? searchResponse = await this.ExecuteSearchAsync(modifiedQuery, top, skip, filters, cancellationToken).ConfigureAwait(false);

        long? totalCount = includeTotalCount ? searchResponse?.Web?.Results.Count : null;

        return new KernelSearchResults<TextSearchResult>(this.GetResultsAsTextSearchResultAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    async Task<KernelSearchResults<BraveWebPage>> ITextSearch<BraveWebPage>.GetSearchResultsAsync(string query, TextSearchOptions<BraveWebPage>? searchOptions, CancellationToken cancellationToken)
    {
        var (modifiedQuery, top, skip, includeTotalCount, filters) = ExtractSearchParameters(query, searchOptions);
        BraveSearchResponse<BraveWebResult>? searchResponse = await this.ExecuteSearchAsync(modifiedQuery, top, skip, filters, cancellationToken).ConfigureAwait(false);

        long? totalCount = includeTotalCount ? searchResponse?.Web?.Results.Count : null;

        return new KernelSearchResults<BraveWebPage>(this.GetResultsAsBraveWebPageAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    #endregion

    #region LINQ-to-Brave Conversion Logic

    /// <summary>
    /// Extracts search parameters from generic <see cref="TextSearchOptions{TRecord}"/>.
    /// This is the primary entry point for the LINQ-based filtering path.
    /// Brave supports query modification via Title.Contains() which appends terms to the query.
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
    /// Walks a LINQ expression tree and extracts Brave API filter key-value pairs and query terms directly.
    /// Supports equality expressions, Contains() method calls, and logical AND/OR operators.
    /// </summary>
    /// <param name="expression">The expression to analyze.</param>
    /// <param name="filters">The list to add filter key-value pairs to.</param>
    /// <param name="queryTerms">The list to add query modification terms to.</param>
    private static void ExtractFiltersFromExpression(Expression expression, List<(string FieldName, object Value)> filters, List<string> queryTerms)
    {
        switch (expression)
        {
            case BinaryExpression binaryExpr:
                if (binaryExpr.NodeType is ExpressionType.AndAlso or ExpressionType.OrElse)
                {
                    // Handle AND/OR expressions by recursively analyzing both sides
                    ExtractFiltersFromExpression(binaryExpr.Left, filters, queryTerms);
                    ExtractFiltersFromExpression(binaryExpr.Right, filters, queryTerms);
                }
                else if (binaryExpr.NodeType == ExpressionType.Equal)
                {
                    ProcessEqualityClause(binaryExpr, filters);
                }
                else if (binaryExpr.NodeType == ExpressionType.NotEqual)
                {
                    ProcessInequalityClause(binaryExpr);
                }
                else
                {
                    throw new NotSupportedException($"Binary expression type '{binaryExpr.NodeType}' is not supported. Supported operators: AndAlso (&&), OrElse (||), Equal (==), NotEqual (!=).");
                }
                break;

            case UnaryExpression unaryExpr when unaryExpr.NodeType == ExpressionType.Not:
                ProcessNotExpression(unaryExpr);
                break;

            case MethodCallExpression methodCall:
                ProcessMethodCallClause(methodCall, filters, queryTerms);
                break;

            default:
                throw new NotSupportedException($"Expression type '{expression.NodeType}' is not supported in Brave search filters.");
        }
    }

    /// <summary>
    /// Processes an equality expression and maps the property to a Brave API filter directly.
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
            var mappedFieldName = MapPropertyToBraveFilter(propertyName);
            if (mappedFieldName != null)
            {
                filters.Add((mappedFieldName, value));
            }
            else
            {
                throw new NotSupportedException(
                    $"Property '{propertyName}' cannot be mapped to Brave API filters. " +
                    $"Supported properties: {string.Join(", ", s_queryParameters)}. " +
                    "Example: page => page.Country == \"US\" && page.SafeSearch == \"moderate\"");
            }
        }
        else
        {
            throw new NotSupportedException("Unable to extract property name and value from equality expression.");
        }
    }

    /// <summary>
    /// Processes an inequality expression — not supported by Brave API.
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
    /// Processes a NOT (negation) expression — not supported by Brave API.
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
                // Instance method: property.Contains(value) - e.g., page.ResultFilter.Contains("web")
                var propertyName = member.Member.Name;
                var value = ExtractValue(methodCall.Arguments[0]);

                if (value != null)
                {
                    if (propertyName.Equals("ResultFilter", StringComparison.OrdinalIgnoreCase))
                    {
                        var mappedFieldName = MapPropertyToBraveFilter(propertyName);
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
                        throw new NotSupportedException($"Contains method is only supported for ResultFilter and Title properties, not '{propertyName}'.");
                    }
                }
            }
            else if (methodCall.Object == null && methodCall.Arguments.Count == 2)
            {
                // Static method: array.Contains(property) - NOT supported
                string errorMessage = "Collection Contains filters (e.g., array.Contains(page.Property)) are not supported by Brave Search API. " +
                    "Brave's API does not support OR logic across multiple values. ";

                if (IsMemoryExtensionsContains(methodCall))
                {
                    errorMessage += "Note: This occurs when using C# 14+ language features with span-based Contains methods (MemoryExtensions.Contains). ";
                }
                else
                {
                    errorMessage += "Note: This occurs with standard LINQ extension methods (Enumerable.Contains). ";
                }

                errorMessage += "Consider either: (1) performing multiple separate searches for each value, or " +
                    "(2) retrieving broader results and filtering on the client side.";

                throw new NotSupportedException(errorMessage);
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

    /// <summary>
    /// Extracts a value from an expression node (constant or member access).
    /// Used by filter extraction to evaluate expression values for AOT compatibility.
    /// </summary>
    /// <param name="expression">The expression to extract a value from.</param>
    /// <returns>The extracted value.</returns>
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
    /// Execute a Brave search query and return the results.
    /// </summary>
    /// <param name="query">What to search for.</param>
    /// <param name="top">Number of results to return.</param>
    /// <param name="skip">Number of results to skip.</param>
    /// <param name="filters">Pre-extracted filter key-value pairs.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    private async Task<BraveSearchResponse<BraveWebResult>?> ExecuteSearchAsync(string query, int top, int skip, List<(string FieldName, object Value)> filters, CancellationToken cancellationToken = default)
    {
        using HttpResponseMessage response = await this.SendGetRequestAsync(query, top, skip, filters, cancellationToken).ConfigureAwait(false);

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
    /// <param name="top">Number of results to return.</param>
    /// <param name="skip">Number of results to skip.</param>
    /// <param name="filters">Pre-extracted filter key-value pairs.</param>
    /// <param name="cancellationToken">A cancellation token to cancel the request.</param>
    /// <returns>A <see cref="HttpResponseMessage"/> representing the response from the request.</returns>
    private async Task<HttpResponseMessage> SendGetRequestAsync(string query, int top, int skip, List<(string FieldName, object Value)> filters, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(query);

        if (top is <= 0 or >= 21)
        {
            throw new ArgumentOutOfRangeException(nameof(top), top, $"{nameof(top)} value must be greater than 0 and less than 21.");
        }

        if (skip is < 0 or > 10)
        {
            throw new ArgumentOutOfRangeException(nameof(skip), skip, $"{nameof(skip)} value must be equal or greater than 0 and less than 10.");
        }

        Uri uri = new($"{this._uri}?q={BuildQuery(query, top, skip, filters)}");

        using var httpRequestMessage = new HttpRequestMessage(HttpMethod.Get, uri);

        if (!string.IsNullOrEmpty(this._apiKey))
        {
            httpRequestMessage.Headers.Add("X-Subscription-Token", this._apiKey);
        }

        return await this._httpClient.SendWithSuccessCheckAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Return the search results as instances of <see cref="object"/>.
    /// </summary>
    /// <param name="searchResponse">Response containing the web pages matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<object> GetResultsAsObjectAsync(BraveSearchResponse<BraveWebResult>? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse?.Web?.Results is null)
        {
            yield break;
        }

        foreach (var result in searchResponse.Web.Results)
        {
            yield return result;

            await Task.Yield();
        }
    }

    /// <summary>
    /// Return the search results as instances of <see cref="BraveWebPage"/>.
    /// </summary>
    /// <param name="searchResponse">Response containing the web pages matching the query.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<BraveWebPage> GetResultsAsBraveWebPageAsync(BraveSearchResponse<BraveWebResult>? searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
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
    /// Build a Brave API query string from pre-extracted filter key-value pairs.
    /// Both LINQ and legacy paths converge here after producing the same (FieldName, Value) list.
    /// </summary>
    /// <param name="query">The query.</param>
    /// <param name="top">Number of results to return.</param>
    /// <param name="skip">Number of results to skip.</param>
    /// <param name="filters">Pre-extracted filter key-value pairs.</param>
    private static string BuildQuery(string query, int top, int skip, List<(string FieldName, object Value)> filters)
    {
        StringBuilder fullQuery = new();
        fullQuery.Append(Uri.EscapeDataString(query.Trim()));
        StringBuilder queryParams = new();

        foreach (var (fieldName, value) in filters)
        {
            if (s_queryParameters.Contains(fieldName, StringComparer.OrdinalIgnoreCase) && value is not null)
            {
                string queryParam = s_queryParameters.FirstOrDefault(s => s.Equals(fieldName, StringComparison.OrdinalIgnoreCase))!;

                CheckQueryValidation(queryParam, value);

                queryParams.Append('&').Append(queryParam!).Append('=').Append(Uri.EscapeDataString(value.ToString()!));
            }
            else
            {
                throw new ArgumentException($"Unknown equality filter clause field name '{fieldName}', must be one of {string.Join(",", s_queryParameters)}", "searchOptions");
            }
        }

        fullQuery.Append($"&count={top}&offset={skip}{queryParams}");

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
