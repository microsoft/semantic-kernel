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
/// A Google Search service that creates and recalls memories associated with text.
/// </summary>
public sealed class GoogleTextSearchService : ITextSearchService<TextSearchResult>, ITextSearchService<global::Google.Apis.CustomSearchAPI.v1.Data.Result>, IDisposable
{
    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._attributes;

    /// <summary>
    /// Initializes a new instance of the <see cref="GoogleTextSearchService"/> class.
    /// </summary>
    /// <param name="searchEngineId">Google Search Engine ID (looks like "a12b345...")</param>
    /// <param name="apiKey">Google Custom Search API (looks like "ABcdEfG1...")</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public GoogleTextSearchService(
        string searchEngineId,
        string apiKey,
        ILoggerFactory? loggerFactory = null) : this(new BaseClientService.Initializer { ApiKey = apiKey }, searchEngineId, loggerFactory)
    {
        Verify.NotNullOrWhiteSpace(apiKey);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="GoogleTextSearchService"/> class.
    /// </summary>
    /// <param name="initializer">The connector initializer</param>
    /// <param name="searchEngineId">Google Search Engine ID (looks like "a12b345...")</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public GoogleTextSearchService(
        BaseClientService.Initializer initializer,
        string searchEngineId,
        ILoggerFactory? loggerFactory)
    {
        Verify.NotNull(initializer);
        Verify.NotNullOrWhiteSpace(searchEngineId);

        this._search = new CustomSearchAPIService(initializer);
        this._searchEngineId = searchEngineId;
        this._logger = loggerFactory?.CreateLogger(typeof(GoogleConnector)) ?? NullLogger.Instance;

        this._attributes = new Dictionary<string, object?>
        {
        };
    }

    /// <inheritdoc/>
    async Task<KernelSearchResults<TextSearchResult>> ITextSearchService<TextSearchResult>.SearchAsync(string query, SearchExecutionSettings? searchSettings, Kernel? kernel, CancellationToken cancellationToken)
    {
        var searchResponse = await this.ExecuteSearchAsync(query, searchSettings, cancellationToken).ConfigureAwait(false);

        return new KernelSearchResults<TextSearchResult>(searchResponse, this.GetResultsAsync<TextSearchResult>(searchResponse, cancellationToken), 1, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    async Task<KernelSearchResults<global::Google.Apis.CustomSearchAPI.v1.Data.Result>> ITextSearchService<global::Google.Apis.CustomSearchAPI.v1.Data.Result>.SearchAsync(string query, SearchExecutionSettings? searchSettings, Kernel? kernel, CancellationToken cancellationToken)
    {
        var searchResponse = await this.ExecuteSearchAsync(query, searchSettings, cancellationToken).ConfigureAwait(false);

        return new KernelSearchResults<global::Google.Apis.CustomSearchAPI.v1.Data.Result>(searchResponse, this.GetResultsAsync<global::Google.Apis.CustomSearchAPI.v1.Data.Result>(searchResponse, cancellationToken), 1, GetResultsMetadata(searchResponse));
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
    private readonly IReadOnlyDictionary<string, object?> _attributes;

    /// <summary>
    /// Execute a Google search
    /// </summary>
    /// <param name="query">The query string.</param>
    /// <param name="searchSettings">Option search execution settings</param>
    /// <param name="cancellationToken">A cancellation token to cancel the request.</param>
    /// <exception cref="ArgumentOutOfRangeException"></exception>
    /// <exception cref="NotSupportedException"></exception>
    private async Task<global::Google.Apis.CustomSearchAPI.v1.Data.Search> ExecuteSearchAsync(string query, SearchExecutionSettings? searchSettings, CancellationToken cancellationToken)
    {
        searchSettings ??= new SearchExecutionSettings();
        var count = searchSettings.Count;
        var offset = searchSettings.Offset;

        if (count is <= 0 or > MaxCount)
        {
            throw new ArgumentOutOfRangeException(nameof(searchSettings), count, $"{nameof(searchSettings)}.Count value must be must be greater than 0 and less than or equals 10.");
        }

        if (offset < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(searchSettings), offset, $"{nameof(searchSettings)}.Offset value must be must be greater than 0.");
        }

        var search = this._search.Cse.List();
        search.Cx = this._searchEngineId;
        search.Q = query;
        search.Num = count;
        search.Start = offset;

        return await search.ExecuteAsync(cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Return the search results.
    /// </summary>
    /// <param name="searchResponse">Google search response</param>
    /// <param name="cancellationToken">Cancellation token</param>
    private async IAsyncEnumerable<T> GetResultsAsync<T>(global::Google.Apis.CustomSearchAPI.v1.Data.Search searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse is null || searchResponse.Items is null)
        {
            yield break;
        }

        foreach (var item in searchResponse.Items)
        {
            if (item is T itemT)
            {
                yield return itemT;
            }
            else if (typeof(T) == typeof(TextSearchResult))
            {
                yield return (T)(object)new TextSearchResult(item.Title, item.Snippet, item.Link, item);
            }
            else
            {
                throw new NotSupportedException($"Type {typeof(T)} is not supported.");
            }
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
        };
    }

    #endregion
}
