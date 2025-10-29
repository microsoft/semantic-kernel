// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Google.Apis.CustomSearchAPI.v1;
using Google.Apis.Services;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel.Plugins.Web.Google;

/// <summary>
/// A Google Text Search implementation that can be used to perform searches using the Google Web Search API.
/// </summary>
#pragma warning disable CS0618 // ITextSearch is obsolete - this class provides backward compatibility
public sealed class GoogleTextSearch : ITextSearch, ITextSearch<GoogleWebPage>, IDisposable
#pragma warning restore CS0618
{
    /// <summary>
    /// Initializes a new instance of the <see cref="GoogleTextSearch"/> class.
    /// </summary>
    /// <param name="searchEngineId">Google Search Engine ID (looks like "a12b345...")</param>
    /// <param name="apiKey">Google Custom Search API (looks like "ABcdEfG1...")</param>
    /// <param name="options">Options used when creating this instance of <see cref="GoogleTextSearch"/>.</param>
    public GoogleTextSearch(
        string searchEngineId,
        string apiKey,
        GoogleTextSearchOptions? options = null) : this(new BaseClientService.Initializer { ApiKey = apiKey }, searchEngineId, options)
    {
        Verify.NotNullOrWhiteSpace(apiKey);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="GoogleTextSearch"/> class.
    /// </summary>
    /// <param name="initializer">The connector initializer</param>
    /// <param name="searchEngineId">Google Search Engine ID (looks like "a12b345...")</param>
    /// <param name="options">Options used when creating this instance of <see cref="GoogleTextSearch"/>.</param>
    public GoogleTextSearch(
        BaseClientService.Initializer initializer,
        string searchEngineId,
        GoogleTextSearchOptions? options = null)
    {
        Verify.NotNull(initializer);
        Verify.NotNullOrWhiteSpace(searchEngineId);

        this._search = new CustomSearchAPIService(initializer);
        this._searchEngineId = searchEngineId;
        this._logger = options?.LoggerFactory?.CreateLogger(typeof(GoogleTextSearch)) ?? NullLogger.Instance;
        this._stringMapper = options?.StringMapper ?? s_defaultStringMapper;
        this._resultMapper = options?.ResultMapper ?? s_defaultResultMapper;
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<object>> GetSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        searchOptions ??= new TextSearchOptions();
        var searchResponse = await this.ExecuteSearchAsync(query, searchOptions, cancellationToken).ConfigureAwait(false);

        long? totalCount = searchOptions.IncludeTotalCount ? long.Parse(searchResponse.SearchInformation.TotalResults) : null;

        return new KernelSearchResults<object>(this.GetResultsAsResultAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<TextSearchResult>> GetTextSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        searchOptions ??= new TextSearchOptions();
        var searchResponse = await this.ExecuteSearchAsync(query, searchOptions, cancellationToken).ConfigureAwait(false);

        long? totalCount = searchOptions.IncludeTotalCount ? long.Parse(searchResponse.SearchInformation.TotalResults) : null;

        return new KernelSearchResults<TextSearchResult>(this.GetResultsAsTextSearchResultAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<string>> SearchAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        searchOptions ??= new TextSearchOptions();
        var searchResponse = await this.ExecuteSearchAsync(query, searchOptions, cancellationToken).ConfigureAwait(false);

        long? totalCount = searchOptions.IncludeTotalCount ? long.Parse(searchResponse.SearchInformation.TotalResults) : null;

        return new KernelSearchResults<string>(this.GetResultsAsStringAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    #region ITextSearch<GoogleWebPage> Implementation

    /// <inheritdoc/>
    public async Task<KernelSearchResults<object>> GetSearchResultsAsync(string query, TextSearchOptions<GoogleWebPage>? searchOptions = null, CancellationToken cancellationToken = default)
    {
        var legacyOptions = ConvertToLegacyOptions(searchOptions);
        var searchResponse = await this.ExecuteSearchAsync(query, legacyOptions, cancellationToken).ConfigureAwait(false);

        long? totalCount = searchOptions?.IncludeTotalCount == true ? long.Parse(searchResponse.SearchInformation.TotalResults) : null;

        return new KernelSearchResults<object>(this.GetResultsAsGoogleWebPageAsync(searchResponse, cancellationToken).Cast<object>(), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<TextSearchResult>> GetTextSearchResultsAsync(string query, TextSearchOptions<GoogleWebPage>? searchOptions = null, CancellationToken cancellationToken = default)
    {
        var legacyOptions = ConvertToLegacyOptions(searchOptions);
        var searchResponse = await this.ExecuteSearchAsync(query, legacyOptions, cancellationToken).ConfigureAwait(false);

        long? totalCount = searchOptions?.IncludeTotalCount == true ? long.Parse(searchResponse.SearchInformation.TotalResults) : null;

        return new KernelSearchResults<TextSearchResult>(this.GetResultsAsTextSearchResultAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<string>> SearchAsync(string query, TextSearchOptions<GoogleWebPage>? searchOptions = null, CancellationToken cancellationToken = default)
    {
        var legacyOptions = ConvertToLegacyOptions(searchOptions);
        var searchResponse = await this.ExecuteSearchAsync(query, legacyOptions, cancellationToken).ConfigureAwait(false);

        long? totalCount = searchOptions?.IncludeTotalCount == true ? long.Parse(searchResponse.SearchInformation.TotalResults) : null;

        return new KernelSearchResults<string>(this.GetResultsAsStringAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <summary>
    /// Converts generic TextSearchOptions with LINQ filtering to legacy TextSearchOptions.
    /// Attempts to translate simple LINQ expressions to Google API filters where possible.
    /// </summary>
    /// <param name="genericOptions">The generic search options with LINQ filtering.</param>
    /// <returns>Legacy TextSearchOptions with equivalent filtering.</returns>
    private static TextSearchOptions ConvertToLegacyOptions(TextSearchOptions<GoogleWebPage>? genericOptions)
    {
        if (genericOptions == null)
        {
            return new TextSearchOptions();
        }

        return new TextSearchOptions
        {
            Top = genericOptions.Top,
            Skip = genericOptions.Skip,
            IncludeTotalCount = genericOptions.IncludeTotalCount,
            Filter = genericOptions.Filter != null ? ConvertLinqExpressionToGoogleFilter(genericOptions.Filter) : null
        };
    }

    /// <summary>
    /// Converts a LINQ expression to a TextSearchFilter compatible with Google Custom Search API.
    /// Supports property equality expressions, string Contains operations, NOT operations (inequality and negation),
    /// and compound AND expressions that map to Google's filter capabilities.
    /// </summary>
    /// <param name="linqExpression">The LINQ expression to convert.</param>
    /// <returns>A TextSearchFilter with equivalent filtering.</returns>
    /// <exception cref="NotSupportedException">Thrown when the expression cannot be converted to Google filters.</exception>
    private static TextSearchFilter ConvertLinqExpressionToGoogleFilter<TRecord>(Expression<Func<TRecord, bool>> linqExpression)
    {
        // Handle compound AND expressions: expr1 && expr2
        if (linqExpression.Body is BinaryExpression andExpr && andExpr.NodeType == ExpressionType.AndAlso)
        {
            var filter = new TextSearchFilter();
            CollectAndCombineFilters(andExpr, filter);
            return filter;
        }

        // Handle simple expressions using the shared processing logic
        var textSearchFilter = new TextSearchFilter();
        if (TryProcessSingleExpression(linqExpression.Body, textSearchFilter))
        {
            return textSearchFilter;
        }

        // Generate helpful error message with supported patterns
        var supportedProperties = s_queryParameters.Select(p =>
            MapGoogleFilterToProperty(p)).Where(p => p != null).Distinct();

        throw new NotSupportedException(
            $"LINQ expression '{linqExpression}' cannot be converted to Google API filters. " +
            $"Supported patterns: {string.Join(", ", s_supportedPatterns)}. " +
            $"Supported properties: {string.Join(", ", supportedProperties)}.");
    }

    /// <summary>
    /// Recursively collects and combines filters from compound AND expressions.
    /// </summary>
    /// <param name="expression">The expression to process.</param>
    /// <param name="filter">The filter to accumulate results into.</param>
    private static void CollectAndCombineFilters(Expression expression, TextSearchFilter filter)
    {
        if (expression is BinaryExpression binaryExpr && binaryExpr.NodeType == ExpressionType.AndAlso)
        {
            // Recursively process both sides of the AND
            CollectAndCombineFilters(binaryExpr.Left, filter);
            CollectAndCombineFilters(binaryExpr.Right, filter);
        }
        else
        {
            // Process individual expression using shared logic
            TryProcessSingleExpression(expression, filter);
        }
    }

    /// <summary>
    /// Shared logic to process a single LINQ expression and add appropriate filters.
    /// Consolidates duplicate code between ConvertLinqExpressionToGoogleFilter and CollectAndCombineFilters.
    /// </summary>
    /// <param name="expression">The expression to process.</param>
    /// <param name="filter">The filter to add results to.</param>
    /// <returns>True if the expression was successfully processed, false otherwise.</returns>
    private static bool TryProcessSingleExpression(Expression expression, TextSearchFilter filter)
    {
        // Handle equality: record.PropertyName == "value"
        if (expression is BinaryExpression equalExpr && equalExpr.NodeType == ExpressionType.Equal)
        {
            return TryProcessEqualityExpression(equalExpr, filter);
        }

        // Handle inequality (NOT): record.PropertyName != "value"
        if (expression is BinaryExpression notEqualExpr && notEqualExpr.NodeType == ExpressionType.NotEqual)
        {
            return TryProcessInequalityExpression(notEqualExpr, filter);
        }

        // Handle Contains method calls
        if (expression is MethodCallExpression methodCall && methodCall.Method.Name == "Contains")
        {
            // String.Contains (instance method) - supported for substring search
            if (methodCall.Method.DeclaringType == typeof(string))
            {
                return TryProcessContainsExpression(methodCall, filter);
            }

            // Collection Contains (static methods) - NOT supported due to Google API limitations
            // This handles both Enumerable.Contains (C# 13-) and MemoryExtensions.Contains (C# 14+)
            // User's C# language version determines which method is resolved, but both are unsupported
            if (methodCall.Object == null) // Static method
            {
                // Enumerable.Contains or MemoryExtensions.Contains
                if (methodCall.Method.DeclaringType == typeof(Enumerable) ||
                    (methodCall.Method.DeclaringType == typeof(MemoryExtensions) && IsMemoryExtensionsContains(methodCall)))
                {
                    throw new NotSupportedException(
                        "Collection Contains filters (e.g., array.Contains(page.Property)) are not supported by Google Custom Search API. " +
                        "Google's search operators do not support OR logic across multiple values. " +
                        "Consider either: (1) performing multiple separate searches for each value, or " +
                        "(2) retrieving broader results and filtering on the client side.");
                }
            }
        }

        // Handle NOT expressions: !record.PropertyName.Contains("value")
        if (expression is UnaryExpression unaryExpr && unaryExpr.NodeType == ExpressionType.Not)
        {
            return TryProcessNotExpression(unaryExpr, filter);
        }

        return false;
    }

    /// <summary>
    /// Checks if a method call expression is MemoryExtensions.Contains.
    /// This handles C# 14's "first-class spans" feature where collection.Contains(item) resolves to
    /// MemoryExtensions.Contains instead of Enumerable.Contains.
    /// </summary>
    private static bool IsMemoryExtensionsContains(MethodCallExpression methodExpr)
    {
        // MemoryExtensions.Contains has 2-3 parameters (source, value, optional comparer)
        // We only support the case without a comparer (or with null comparer)
        return methodExpr.Method.Name == nameof(MemoryExtensions.Contains) &&
               methodExpr.Arguments.Count >= 2 &&
               methodExpr.Arguments.Count <= 3 &&
               (methodExpr.Arguments.Count == 2 ||
                (methodExpr.Arguments.Count == 3 && methodExpr.Arguments[2] is ConstantExpression { Value: null }));
    }

    /// <summary>
    /// Processes equality expressions: record.PropertyName == "value"
    /// </summary>
    private static bool TryProcessEqualityExpression(BinaryExpression equalExpr, TextSearchFilter filter)
    {
        if (equalExpr.Left is MemberExpression memberExpr && equalExpr.Right is ConstantExpression constExpr)
        {
            string propertyName = memberExpr.Member.Name;
            object? value = constExpr.Value;
            string? googleFilterName = MapPropertyToGoogleFilter(propertyName);
            if (googleFilterName != null && value != null)
            {
                filter.Equality(googleFilterName, value);
                return true;
            }
        }
        return false;
    }

    /// <summary>
    /// Processes inequality expressions: record.PropertyName != "value"
    /// </summary>
    private static bool TryProcessInequalityExpression(BinaryExpression notEqualExpr, TextSearchFilter filter)
    {
        if (notEqualExpr.Left is MemberExpression memberExpr && notEqualExpr.Right is ConstantExpression constExpr)
        {
            string propertyName = memberExpr.Member.Name;
            object? value = constExpr.Value;
            // Map to excludeTerms for text fields
            if (propertyName.ToUpperInvariant() is "TITLE" or "SNIPPET" && value != null)
            {
                filter.Equality("excludeTerms", value);
                return true;
            }
        }
        return false;
    }

    /// <summary>
    /// Processes Contains expressions: record.PropertyName.Contains("value")
    /// </summary>
    private static bool TryProcessContainsExpression(MethodCallExpression methodCall, TextSearchFilter filter)
    {
        if (methodCall.Object is MemberExpression memberExpr &&
            methodCall.Arguments.Count == 1 &&
            methodCall.Arguments[0] is ConstantExpression constExpr)
        {
            string propertyName = memberExpr.Member.Name;
            object? value = constExpr.Value;
            string? googleFilterName = MapPropertyToGoogleFilter(propertyName);
            if (googleFilterName != null && value != null)
            {
                // For Contains operations on text fields, use exactTerms or orTerms
                if (googleFilterName == "exactTerms")
                {
                    filter.Equality("orTerms", value); // More flexible than exactTerms
                }
                else
                {
                    filter.Equality(googleFilterName, value);
                }
                return true;
            }
        }
        return false;
    }

    /// <summary>
    /// Processes NOT expressions: !record.PropertyName.Contains("value")
    /// </summary>
    private static bool TryProcessNotExpression(UnaryExpression unaryExpr, TextSearchFilter filter)
    {
        if (unaryExpr.Operand is MethodCallExpression notMethodCall &&
            notMethodCall.Method.Name == "Contains" &&
            notMethodCall.Method.DeclaringType == typeof(string))
        {
            if (notMethodCall.Object is MemberExpression memberExpr &&
                notMethodCall.Arguments.Count == 1 &&
                notMethodCall.Arguments[0] is ConstantExpression constExpr)
            {
                string propertyName = memberExpr.Member.Name;
                object? value = constExpr.Value;
                if (propertyName.ToUpperInvariant() is "TITLE" or "SNIPPET" && value != null)
                {
                    filter.Equality("excludeTerms", value);
                    return true;
                }
            }
        }
        return false;
    }

    /// <summary>
    /// Maps GoogleWebPage property names to Google Custom Search API filter field names.
    /// </summary>
    /// <param name="propertyName">The GoogleWebPage property name.</param>
    /// <returns>The corresponding Google API filter name, or null if not mappable.</returns>
    private static string? MapPropertyToGoogleFilter(string propertyName)
    {
        return propertyName.ToUpperInvariant() switch
        {
            // Map GoogleWebPage properties to Google API equivalents
            "LINK" => "siteSearch",           // Maps to site search
            "DISPLAYLINK" => "siteSearch",    // Maps to site search  
            "TITLE" => "exactTerms",          // Exact title match
            "SNIPPET" => "exactTerms",        // Exact content match

            // Direct API parameters mapped from GoogleWebPage metadata properties
            "FILEFORMAT" => "fileType",       // File type/extension filtering
            "MIME" => "filter",               // MIME type filtering

            // Locale/Language parameters (if we extend GoogleWebPage)
            "HL" => "hl",                     // Interface language
            "GL" => "gl",                     // Geolocation
            "CR" => "cr",                     // Country restrict
            "LR" => "lr",                     // Language restrict

            _ => null // Property not mappable to Google filters
        };
    }

    /// <summary>
    /// Maps Google Custom Search API filter field names back to example GoogleWebPage property names.
    /// Used for generating helpful error messages.
    /// </summary>
    /// <param name="googleFilterName">The Google API filter name.</param>
    /// <returns>An example property name, or null if not mappable.</returns>
    private static string? MapGoogleFilterToProperty(string googleFilterName)
    {
        return googleFilterName switch
        {
            "siteSearch" => "DisplayLink",
            "exactTerms" => "Title",
            "orTerms" => "Title",
            "excludeTerms" => "Title",
            "fileType" => "FileFormat",
            "filter" => "Mime",
            "hl" => "HL",
            "gl" => "GL",
            "cr" => "CR",
            "lr" => "LR",
            _ => null
        };
    }

    #endregion

    /// <inheritdoc/>
    public void Dispose()
    {
        this._search.Dispose();
    }

    private readonly ILogger _logger;
    private readonly CustomSearchAPIService _search;
    private readonly string? _searchEngineId;
    private readonly ITextSearchStringMapper _stringMapper;
    private readonly ITextSearchResultMapper _resultMapper;

    private static readonly ITextSearchStringMapper s_defaultStringMapper = new DefaultTextSearchStringMapper();
    private static readonly ITextSearchResultMapper s_defaultResultMapper = new DefaultTextSearchResultMapper();

    private const int MaxCount = 10;

    // See https://developers.google.com/custom-search/v1/reference/rest/v1/cse/list
    private static readonly string[] s_queryParameters = ["cr", "dateRestrict", "exactTerms", "excludeTerms", "fileType", "filter", "gl", "hl", "linkSite", "lr", "orTerms", "rights", "siteSearch"];

    // Performance optimization: Static error message arrays to avoid allocations in error paths
    private static readonly string[] s_supportedPatterns = [
        "page.Property == \"value\" (exact match)",
        "page.Property != \"value\" (exclude)",
        "page.Property.Contains(\"text\") (partial match)",
        "!page.Property.Contains(\"text\") (exclude partial)",
        "page.Prop1 == \"val1\" && page.Prop2.Contains(\"val2\") (compound AND)"
    ];

    private delegate void SetSearchProperty(CseResource.ListRequest search, string value);

    private static readonly Dictionary<string, SetSearchProperty> s_searchPropertySetters = new() {
        { "CR", (search, value) => search.Cr = value },
        { "DATERESTRICT", (search, value) => search.DateRestrict = value },
        { "EXACTTERMS", (search, value) => search.ExactTerms = value },
        { "EXCLUDETERMS", (search, value) => search.ExcludeTerms = value },
        { "FILETYPE", (search, value) => search.FileType = value },
        { "FILTER", (search, value) => search.Filter = value },
        { "GL", (search, value) => search.Gl = value },
        { "HL", (search, value) => search.Hl = value },
        { "LINKSITE", (search, value) => search.LinkSite = value },
        { "LR", (search, value) => search.Lr = value },
        { "ORTERMS", (search, value) => search.OrTerms = value },
        { "RIGHTS", (search, value) => search.Rights = value },
        { "SITESEARCH", (search, value) => { search.SiteSearch = value; search.SiteSearchFilter = CseResource.ListRequest.SiteSearchFilterEnum.I; } },
    };

    /// <summary>
    /// Execute a Google search
    /// </summary>
    /// <param name="query">The query string.</param>
    /// <param name="searchOptions">Search options.</param>
    /// <param name="cancellationToken">A cancellation token to cancel the request.</param>
    /// <exception cref="ArgumentOutOfRangeException"></exception>
    /// <exception cref="NotSupportedException"></exception>
    private async Task<global::Google.Apis.CustomSearchAPI.v1.Data.Search> ExecuteSearchAsync(string query, TextSearchOptions searchOptions, CancellationToken cancellationToken)
    {
        var count = searchOptions.Top;
        var offset = searchOptions.Skip;

        if (count <= 0 || count > MaxCount)
        {
            throw new ArgumentOutOfRangeException(nameof(searchOptions), count, $"{nameof(searchOptions)}.Count value must be must be greater than 0 and less than or equals 10.");
        }

        if (offset < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(searchOptions), offset, $"{nameof(searchOptions)}.Offset value must be must be greater than 0.");
        }

        var search = this._search.Cse.List();
        search.Cx = this._searchEngineId;
        search.Q = query;
        search.Num = count;
        search.Start = offset;

        this.AddFilters(search, searchOptions);

        return await search.ExecuteAsync(cancellationToken).ConfigureAwait(false);
    }

#pragma warning disable CS0618 // FilterClause is obsolete
    /// <summary>
    /// Add basic filters to the Google search metadata.
    /// </summary>
    /// <param name="search">Google search metadata</param>
    /// <param name="searchOptions">Text search options</param>
    private void AddFilters(CseResource.ListRequest search, TextSearchOptions searchOptions)
    {
        if (searchOptions.Filter is not null)
        {
            var filterClauses = searchOptions.Filter.FilterClauses;

            foreach (var filterClause in filterClauses)
            {
                if (filterClause is EqualToFilterClause equalityFilterClause)
                {
                    if (equalityFilterClause.Value is not string value)
                    {
                        continue;
                    }

                    if (s_searchPropertySetters.TryGetValue(equalityFilterClause.FieldName.ToUpperInvariant(), out var setter))
                    {
                        setter.Invoke(search, value);
                    }
                    else
                    {
                        throw new ArgumentException($"Unknown equality filter clause field name '{equalityFilterClause.FieldName}', must be one of {string.Join(",", s_queryParameters)}", nameof(searchOptions));
                    }
                }
            }
        }
    }
#pragma warning restore CS0618 // FilterClause is obsolete

    /// <summary>
    /// Return the search results as instances of <see cref="TextSearchResult"/>.
    /// </summary>
    /// <param name="searchResponse">Google search response</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<TextSearchResult> GetResultsAsTextSearchResultAsync(global::Google.Apis.CustomSearchAPI.v1.Data.Search searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse is null || searchResponse.Items is null)
        {
            yield break;
        }

        foreach (var item in searchResponse.Items)
        {
            yield return this._resultMapper.MapFromResultToTextSearchResult(item);
            await Task.Yield();
        }
    }

    /// <summary>
    /// Return the search results as instances of <see cref="string"/>.
    /// </summary>
    /// <param name="searchResponse">Google search response</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<string> GetResultsAsStringAsync(global::Google.Apis.CustomSearchAPI.v1.Data.Search searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse is null || searchResponse.Items is null)
        {
            yield break;
        }

        foreach (var item in searchResponse.Items)
        {
            yield return this._stringMapper.MapFromResultToString(item);
            await Task.Yield();
        }
    }

    /// <summary>
    /// Return the search results as instances of <see cref="GoogleWebPage"/>.
    /// </summary>
    /// <param name="searchResponse">Google search response</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<GoogleWebPage> GetResultsAsGoogleWebPageAsync(global::Google.Apis.CustomSearchAPI.v1.Data.Search searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse is null || searchResponse.Items is null)
        {
            yield break;
        }

        foreach (var item in searchResponse.Items)
        {
            yield return ConvertToGoogleWebPage(item);
            await Task.Yield();
        }
    }

    /// <summary>
    /// Return the search results as instances of <see cref="global::Google.Apis.CustomSearchAPI.v1.Data.Result"/>.
    /// </summary>
    /// <param name="searchResponse">Google search response</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<global::Google.Apis.CustomSearchAPI.v1.Data.Result> GetResultsAsResultAsync(global::Google.Apis.CustomSearchAPI.v1.Data.Search searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse is null || searchResponse.Items is null)
        {
            yield break;
        }

        foreach (var item in searchResponse.Items)
        {
            yield return item;
            await Task.Yield();
        }
    }

    /// <summary>
    /// Return the results metadata.
    /// </summary>
    /// <param name="searchResponse">Google search response</param>
    private static Dictionary<string, object?>? GetResultsMetadata(global::Google.Apis.CustomSearchAPI.v1.Data.Search searchResponse)
    {
        return new Dictionary<string, object?>()
        {
            { "ETag", searchResponse.ETag },
        };
    }

    /// <summary>
    /// Converts a Google CustomSearchAPI Result to a GoogleWebPage instance.
    /// </summary>
    /// <param name="googleResult">The Google search result to convert.</param>
    /// <returns>A GoogleWebPage with mapped properties.</returns>
    private static GoogleWebPage ConvertToGoogleWebPage(global::Google.Apis.CustomSearchAPI.v1.Data.Result googleResult)
    {
        return new GoogleWebPage
        {
            Title = googleResult.Title,
            Link = googleResult.Link,
            Snippet = googleResult.Snippet,
            DisplayLink = googleResult.DisplayLink,
            FormattedUrl = googleResult.FormattedUrl,
            HtmlFormattedUrl = googleResult.HtmlFormattedUrl,
            HtmlSnippet = googleResult.HtmlSnippet,
            HtmlTitle = googleResult.HtmlTitle,
            Mime = googleResult.Mime,
            FileFormat = googleResult.FileFormat,
            Labels = googleResult.Labels?.Select(l => l.Name).ToArray()
        };
    }

    /// <summary>
    /// Default implementation which maps from a <see cref="global::Google.Apis.CustomSearchAPI.v1.Data.Result"/> to a <see cref="string"/>
    /// </summary>
    private sealed class DefaultTextSearchStringMapper : ITextSearchStringMapper
    {
        /// <inheritdoc />
        public string MapFromResultToString(object result)
        {
            if (result is not global::Google.Apis.CustomSearchAPI.v1.Data.Result googleResult)
            {
                throw new ArgumentException("Result must be a Google Result", nameof(result));
            }

            return googleResult.Snippet ?? string.Empty;
        }
    }

    /// <summary>
    /// Default implementation which maps from a <see cref="global::Google.Apis.CustomSearchAPI.v1.Data.Result"/> to a <see cref="TextSearchResult"/>
    /// </summary>
    private sealed class DefaultTextSearchResultMapper : ITextSearchResultMapper
    {
        /// <inheritdoc />
        public TextSearchResult MapFromResultToTextSearchResult(object result)
        {
            if (result is not global::Google.Apis.CustomSearchAPI.v1.Data.Result googleResult)
            {
                throw new ArgumentException("Result must be a Google Result", nameof(result));
            }

            return new TextSearchResult(googleResult.Snippet) { Name = googleResult.Title, Link = googleResult.Link };
        }
    }
}
