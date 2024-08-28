// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Google.Apis.CustomSearchAPI.v1;
using Google.Apis.Services;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Search;

namespace Microsoft.SemanticKernel.Plugins.Web.Google;

/// <summary>
/// A Google Text Search implementation that can be used to perform searches using the Google Web Search API.
/// </summary>
public sealed class GoogleTextSearch : ITextSearch, IDisposable
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
        this._mapToString = options?.MapToString ?? DefaultMapToString;
        this._mapToTextSearchResult = options?.MapToTextSearchResult ?? DefaultMapToTextSearchResult;
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

    /// <inheritdoc/>
    public void Dispose()
    {
        this._search.Dispose();
    }

    #region private

    private const int MaxCount = 10;

    private readonly ILogger _logger;
    private readonly CustomSearchAPIService _search;
    private readonly string? _searchEngineId;
    private readonly MapResultToString _mapToString;
    private readonly MapResultToTextSearchResult _mapToTextSearchResult;

    // See https://developers.google.com/custom-search/v1/reference/rest/v1/cse/list
    private static readonly string[] s_queryParameters = ["cr", "dateRestrict", "exactTerms", "excludeTerms", "filter", "gl", "hl", "linkSite", "lr", "orTerms", "rights", "siteSearch"];

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
        var count = searchOptions.Count;
        var offset = searchOptions.Offset;

        if (count is <= 0 or > MaxCount)
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

    /// <summary>
    /// Add basic filters to the Google search metadata.
    /// </summary>
    /// <param name="search">Google search metadata</param>
    /// <param name="searchOptions">Text search options</param>
    private void AddFilters(CseResource.ListRequest search, TextSearchOptions searchOptions)
    {
        if (searchOptions.BasicFilter is not null)
        {
            var filterClauses = searchOptions.BasicFilter.FilterClauses;

            foreach (var filterClause in filterClauses)
            {
                if (filterClause is EqualityFilterClause equalityFilterClause)
                {
                    if (equalityFilterClause.Value is not string value)
                    {
                        continue;
                    }

                    if (equalityFilterClause.FieldName.Equals("cr", StringComparison.OrdinalIgnoreCase))
                    {
                        search.Cr = value;
                    }
                    else if (equalityFilterClause.FieldName.Equals("dateRestrict", StringComparison.OrdinalIgnoreCase))
                    {
                        search.DateRestrict = value;
                    }
                    else if (equalityFilterClause.FieldName.Equals("exactTerms", StringComparison.OrdinalIgnoreCase))
                    {
                        search.ExactTerms = value;
                    }
                    else if (equalityFilterClause.FieldName.Equals("excludeTerms", StringComparison.OrdinalIgnoreCase))
                    {
                        search.ExcludeTerms = value;
                    }
                    else if (equalityFilterClause.FieldName.Equals("filter", StringComparison.OrdinalIgnoreCase))
                    {
                        search.Filter = value;
                    }
                    else if (equalityFilterClause.FieldName.Equals("gl", StringComparison.OrdinalIgnoreCase))
                    {
                        search.Gl = value;
                    }
                    else if (equalityFilterClause.FieldName.Equals("hl", StringComparison.OrdinalIgnoreCase))
                    {
                        search.Hl = value;
                    }
                    else if (equalityFilterClause.FieldName.Equals("linkSite", StringComparison.OrdinalIgnoreCase))
                    {
                        search.LinkSite = value;
                    }
                    else if (equalityFilterClause.FieldName.Equals("lr", StringComparison.OrdinalIgnoreCase))
                    {
                        search.Lr = value;
                    }
                    else if (equalityFilterClause.FieldName.Equals("orTerms", StringComparison.OrdinalIgnoreCase))
                    {
                        search.OrTerms = value;
                    }
                    else if (equalityFilterClause.FieldName.Equals("rights", StringComparison.OrdinalIgnoreCase))
                    {
                        search.Rights = value;
                    }
                    else if (equalityFilterClause.FieldName.Equals("siteSearch", StringComparison.OrdinalIgnoreCase))
                    {
                        search.SiteSearch = value;
                        search.SiteSearchFilter = CseResource.ListRequest.SiteSearchFilterEnum.I;
                    }
                    else
                    {
                        throw new ArgumentException($"Unknown equality filter clause field name, must be one of {string.Join(",", s_queryParameters)}", nameof(searchOptions));
                    }
                }
            }
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
            yield return this._mapToTextSearchResult(item);
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
            yield return this._mapToString(item);
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
    /// Default implementation which maps from a <see cref="global::Google.Apis.CustomSearchAPI.v1.Data.Result"/> to a <see cref="string"/>
    /// </summary>
    private static string DefaultMapToString(global::Google.Apis.CustomSearchAPI.v1.Data.Result result)
    {
        return result.Snippet ?? string.Empty;
    }

    /// <summary>
    /// Default implementation which maps from a <see cref="global::Google.Apis.CustomSearchAPI.v1.Data.Result"/> to a <see cref="TextSearchResult"/>
    /// </summary>
    private static TextSearchResult DefaultMapToTextSearchResult(global::Google.Apis.CustomSearchAPI.v1.Data.Result result)
    {
        return new TextSearchResult(result.Title, result.Snippet, result.Link);
    }

    #endregion
}
