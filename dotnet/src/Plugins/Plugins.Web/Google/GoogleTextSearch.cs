// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable CS0618 // Obsolete ITextSearch, TextSearchOptions, TextSearchFilter, FilterClause - backward compatibility

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
public sealed class GoogleTextSearch : ITextSearch, ITextSearch<GoogleWebPage>, IDisposable
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
        this._options = options;
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<object>> GetSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        searchOptions ??= new TextSearchOptions();
        var filters = ExtractFiltersFromLegacy(searchOptions.Filter);
        var searchResponse = await this.ExecuteSearchAsync(query, searchOptions.Top, searchOptions.Skip, filters, cancellationToken).ConfigureAwait(false);

        long? totalCount = searchOptions.IncludeTotalCount ? long.Parse(searchResponse.SearchInformation.TotalResults) : null;

        return new KernelSearchResults<object>(this.GetResultsAsResultAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<TextSearchResult>> GetTextSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        searchOptions ??= new TextSearchOptions();
        var filters = ExtractFiltersFromLegacy(searchOptions.Filter);
        var searchResponse = await this.ExecuteSearchAsync(query, searchOptions.Top, searchOptions.Skip, filters, cancellationToken).ConfigureAwait(false);

        long? totalCount = searchOptions.IncludeTotalCount ? long.Parse(searchResponse.SearchInformation.TotalResults) : null;

        return new KernelSearchResults<TextSearchResult>(this.GetResultsAsTextSearchResultAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<string>> SearchAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        searchOptions ??= new TextSearchOptions();
        var filters = ExtractFiltersFromLegacy(searchOptions.Filter);
        var searchResponse = await this.ExecuteSearchAsync(query, searchOptions.Top, searchOptions.Skip, filters, cancellationToken).ConfigureAwait(false);

        long? totalCount = searchOptions.IncludeTotalCount ? long.Parse(searchResponse.SearchInformation.TotalResults) : null;

        return new KernelSearchResults<string>(this.GetResultsAsStringAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    #region ITextSearch<GoogleWebPage> Implementation

    /// <inheritdoc/>
    public async Task<KernelSearchResults<GoogleWebPage>> GetSearchResultsAsync(string query, TextSearchOptions<GoogleWebPage>? searchOptions = null, CancellationToken cancellationToken = default)
    {
        var (top, skip, includeTotalCount, filters) = ExtractSearchParameters(searchOptions);
        var searchResponse = await this.ExecuteSearchAsync(query, top, skip, filters, cancellationToken).ConfigureAwait(false);

        long? totalCount = includeTotalCount ? long.Parse(searchResponse.SearchInformation.TotalResults) : null;

        return new KernelSearchResults<GoogleWebPage>(this.GetResultsAsGoogleWebPageAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<TextSearchResult>> GetTextSearchResultsAsync(string query, TextSearchOptions<GoogleWebPage>? searchOptions = null, CancellationToken cancellationToken = default)
    {
        var (top, skip, includeTotalCount, filters) = ExtractSearchParameters(searchOptions);
        var searchResponse = await this.ExecuteSearchAsync(query, top, skip, filters, cancellationToken).ConfigureAwait(false);

        long? totalCount = includeTotalCount ? long.Parse(searchResponse.SearchInformation.TotalResults) : null;

        return new KernelSearchResults<TextSearchResult>(this.GetResultsAsTextSearchResultAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<string>> SearchAsync(string query, TextSearchOptions<GoogleWebPage>? searchOptions = null, CancellationToken cancellationToken = default)
    {
        var (top, skip, includeTotalCount, filters) = ExtractSearchParameters(searchOptions);
        var searchResponse = await this.ExecuteSearchAsync(query, top, skip, filters, cancellationToken).ConfigureAwait(false);

        long? totalCount = includeTotalCount ? long.Parse(searchResponse.SearchInformation.TotalResults) : null;

        return new KernelSearchResults<string>(this.GetResultsAsStringAsync(searchResponse, cancellationToken), totalCount, GetResultsMetadata(searchResponse));
    }

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
    /// Walks a LINQ expression tree and extracts Google API filter key-value pairs directly.
    /// Supports property equality expressions, string Contains operations, NOT operations (inequality and negation),
    /// and compound AND expressions that map to Google's filter capabilities.
    /// </summary>
    /// <param name="linqExpression">The LINQ expression to walk.</param>
    /// <returns>A list of (FieldName, Value) pairs for Google API filters.</returns>
    /// <exception cref="NotSupportedException">Thrown when the expression cannot be converted to Google filters.</exception>
    private static List<(string FieldName, object Value)> ExtractFiltersFromExpression<TRecord>(Expression<Func<TRecord, bool>> linqExpression)
    {
        var filters = new List<(string FieldName, object Value)>();
        ProcessFilterNode(linqExpression.Body, filters);
        return filters;
    }

    /// <summary>
    /// Recursively processes a LINQ expression tree node and builds Google API filters.
    /// Handles AND combinations, equality, inequality, string Contains, and negation patterns.
    /// </summary>
    /// <param name="expression">The expression node to process.</param>
    /// <param name="filters">The filter list to accumulate results into.</param>
    /// <exception cref="NotSupportedException">Thrown when the expression cannot be converted to Google filters.</exception>
    private static void ProcessFilterNode(Expression expression, List<(string FieldName, object Value)> filters)
    {
        switch (expression)
        {
            case BinaryExpression { NodeType: ExpressionType.AndAlso } andExpr:
                ProcessFilterNode(andExpr.Left, filters);
                ProcessFilterNode(andExpr.Right, filters);
                break;

            case BinaryExpression { NodeType: ExpressionType.Equal, Left: MemberExpression member, Right: ConstantExpression constant }
                when constant.Value is not null:
            {
                var filterName = MapPropertyToGoogleFilter(member.Member.Name)
                    ?? throw new NotSupportedException(
                        $"Property '{member.Member.Name}' is not supported for Google API equality filters. " +
                        $"Supported patterns: {string.Join(", ", s_supportedPatterns)}.");
                filters.Add((filterName, constant.Value));
                break;
            }

            case BinaryExpression { NodeType: ExpressionType.NotEqual, Left: MemberExpression member, Right: ConstantExpression constant }
                when constant.Value is not null:
            {
                _ = MapPropertyToGoogleFilter(member.Member.Name)
                    ?? throw new NotSupportedException(
                        $"Property '{member.Member.Name}' is not supported for Google API inequality filters. " +
                        $"Supported patterns: {string.Join(", ", s_supportedPatterns)}.");
                filters.Add(("excludeTerms", constant.Value));
                break;
            }

            case MethodCallExpression { Method.Name: "Contains", Method.DeclaringType: Type dt, Object: MemberExpression member } methodCall
                when dt == typeof(string)
                    && methodCall.Arguments is [ConstantExpression { Value: not null } argExpr]:
            {
                var filterName = MapPropertyToGoogleFilter(member.Member.Name)
                    ?? throw new NotSupportedException(
                        $"Property '{member.Member.Name}' is not supported for Google API Contains filters. " +
                        $"Supported patterns: {string.Join(", ", s_supportedPatterns)}.");
                // For Contains operations on text fields, use orTerms (more flexible than exactTerms)
                filters.Add((filterName == "exactTerms" ? "orTerms" : filterName, argExpr.Value));
                break;
            }

            // Null-guard patterns (page.Property != null, page.Property == null) — silently skip
            case BinaryExpression { NodeType: ExpressionType.Equal or ExpressionType.NotEqual, Right: ConstantExpression { Value: null } }:
                break;

            case MethodCallExpression { Method.Name: "Contains", Object: null }:
                throw new NotSupportedException(
                    "Collection Contains filters (e.g., collection.Contains(page.Property)) are not supported by Google Custom Search API. " +
                    "Google API doesn't support OR logic across multiple values for a single field. " +
                    "Consider using multiple separate queries instead.");

            case UnaryExpression { NodeType: ExpressionType.Not } unaryExpr:
                ProcessNegatedFilterNode(unaryExpr.Operand, filters);
                break;

            default:
                throw new NotSupportedException(
                    $"Expression type '{expression.NodeType}' is not supported for Google API filters. " +
                    $"Supported patterns: {string.Join(", ", s_supportedPatterns)}.");
        }
    }

    /// <summary>
    /// Processes negated expressions (! operator), mapping them to Google's excludeTerms parameter.
    /// Handles both !(property == value) and !property.Contains(value) patterns.
    /// </summary>
    /// <param name="expression">The inner expression of the NOT operation.</param>
    /// <param name="filters">The filter list to accumulate results into.</param>
    /// <exception cref="NotSupportedException">Thrown when the negated expression cannot be converted to Google filters.</exception>
    private static void ProcessNegatedFilterNode(Expression expression, List<(string FieldName, object Value)> filters)
    {
        switch (expression)
        {
            case BinaryExpression { NodeType: ExpressionType.Equal, Left: MemberExpression member, Right: ConstantExpression constant }
                when constant.Value is not null:
            {
                _ = MapPropertyToGoogleFilter(member.Member.Name)
                    ?? throw new NotSupportedException(
                        $"Property '{member.Member.Name}' is not supported for Google API negated equality filters.");
                filters.Add(("excludeTerms", constant.Value));
                break;
            }

            case MethodCallExpression { Method.Name: "Contains", Method.DeclaringType: Type dt, Object: MemberExpression member } methodCall
                when dt == typeof(string)
                    && methodCall.Arguments is [ConstantExpression { Value: not null } argExpr]:
            {
                _ = MapPropertyToGoogleFilter(member.Member.Name)
                    ?? throw new NotSupportedException(
                        $"Property '{member.Member.Name}' is not supported for Google API negated Contains filters.");
                filters.Add(("excludeTerms", argExpr.Value));
                break;
            }

            default:
                throw new NotSupportedException(
                    $"Negated expression type '{expression.NodeType}' is not supported for Google API filters. " +
                    $"Supported patterns: {string.Join(", ", s_supportedPatterns)}.");
        }
    }

    /// <summary>
    /// Maps GoogleWebPage property names to Google Custom Search API filter field names.
    /// </summary>
    /// <param name="propertyName">The GoogleWebPage property name.</param>
    /// <returns>The corresponding Google API filter name, or null if not mappable.</returns>
    private static string? MapPropertyToGoogleFilter(string propertyName) =>
        propertyName.ToUpperInvariant() switch
        {
            // Map GoogleWebPage properties to Google API equivalents
            "LINK" => "siteSearch",           // Maps to site search
            "DISPLAYLINK" => "siteSearch",    // Maps to site search  
            "TITLE" => "exactTerms",          // Exact title match
            "SNIPPET" => "exactTerms",        // Exact content match

            // Direct API parameters mapped from GoogleWebPage metadata properties
            "FILEFORMAT" => "fileType",       // File type/extension filtering

            // Note: GoogleWebPage does expose a Mime property, but the Google Custom Search 'filter'
            //       API parameter does not accept MIME types; it only accepts 0 or 1 for duplicate
            //       content filtering. Therefore, no Mime-to-filter mapping is defined here.
            // Note: HL, GL, CR, LR properties don't exist on GoogleWebPage

            _ => null // Property not mappable to Google filters
        };

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
    private readonly GoogleTextSearchOptions? _options;

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
    /// <param name="top">Number of results to return.</param>
    /// <param name="skip">Number of results to skip.</param>
    /// <param name="filters">Pre-extracted filter key-value pairs.</param>
    /// <param name="cancellationToken">A cancellation token to cancel the request.</param>
    /// <exception cref="ArgumentOutOfRangeException"></exception>
    /// <exception cref="NotSupportedException"></exception>
    private async Task<global::Google.Apis.CustomSearchAPI.v1.Data.Search> ExecuteSearchAsync(string query, int top, int skip, List<(string FieldName, object Value)> filters, CancellationToken cancellationToken)
    {
        if (top <= 0 || top > MaxCount)
        {
            throw new ArgumentOutOfRangeException(nameof(top), top, $"{nameof(top)} value must be greater than 0 and less than or equals 10.");
        }

        if (skip < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(skip), skip, $"{nameof(skip)} value must be greater than or equal to 0.");
        }

        var search = this._search.Cse.List();
        search.Cx = this._searchEngineId;
        search.Q = query;
        search.Num = top;
        search.Start = skip;

        this.ApplyFilters(search, filters);

        return await search.ExecuteAsync(cancellationToken).ConfigureAwait(false);
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
                        $"Filter clause type '{clause.GetType().Name}' is not supported by Google Text Search. Only EqualToFilterClause is supported.");
                }
            }
        }
        return filters;
    }

    /// <summary>
    /// Apply pre-extracted filter key-value pairs to the Google search request.
    /// Both LINQ and legacy paths converge here after producing the same (FieldName, Value) list.
    /// </summary>
    /// <param name="search">Google search metadata</param>
    /// <param name="filters">Pre-extracted filter key-value pairs.</param>
    private void ApplyFilters(CseResource.ListRequest search, List<(string FieldName, object Value)> filters)
    {
        HashSet<string> processedParams = new(StringComparer.OrdinalIgnoreCase);

        foreach (var (fieldName, value) in filters)
        {
            if (value is not string stringValue)
            {
                continue;
            }

            if (s_searchPropertySetters.TryGetValue(fieldName.ToUpperInvariant(), out var setter))
            {
                setter.Invoke(search, stringValue);
                processedParams.Add(fieldName);
            }
            else
            {
                throw new ArgumentException($"Unknown equality filter clause field name '{fieldName}', must be one of {string.Join(",", s_queryParameters)}", nameof(filters));
            }
        }

        // Apply default search parameters from constructor options (only for params not already set by filter)
        this.ApplyDefaultSearchParameters(search, processedParams);
    }

    /// <summary>
    /// Applies default Google search parameters from <see cref="GoogleTextSearchOptions"/> to the search request.
    /// Parameters already set by filter clauses are not overridden.
    /// </summary>
    private void ApplyDefaultSearchParameters(CseResource.ListRequest search, HashSet<string> processedParams)
    {
        if (this._options is null)
        {
            return;
        }

        if (this._options.CountryRestrict is not null && !processedParams.Contains("cr"))
        {
            search.Cr = this._options.CountryRestrict;
        }

        if (this._options.DateRestrict is not null && !processedParams.Contains("dateRestrict"))
        {
            search.DateRestrict = this._options.DateRestrict;
        }

        if (this._options.GeoLocation is not null && !processedParams.Contains("gl"))
        {
            search.Gl = this._options.GeoLocation;
        }

        if (this._options.InterfaceLanguage is not null && !processedParams.Contains("hl"))
        {
            search.Hl = this._options.InterfaceLanguage;
        }

        if (this._options.LinkSite is not null && !processedParams.Contains("linkSite"))
        {
            search.LinkSite = this._options.LinkSite;
        }

        if (this._options.LanguageRestrict is not null && !processedParams.Contains("lr"))
        {
            search.Lr = this._options.LanguageRestrict;
        }

        if (this._options.Rights is not null && !processedParams.Contains("rights"))
        {
            search.Rights = this._options.Rights;
        }

        if (this._options.DuplicateContentFilter is not null && !processedParams.Contains("filter"))
        {
            search.Filter = this._options.DuplicateContentFilter;
        }
    }

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
