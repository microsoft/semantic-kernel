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
public sealed class GoogleTextSearchService : ITextSearchService, IDisposable
{
    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._attributes;

    /// <summary>
    /// Initializes a new instance of the <see cref="GoogleTextSearchService"/> class.
    /// </summary>
    /// <param name="apiKey">Google Custom Search API (looks like "ABcdEfG1...")</param>
    /// <param name="searchEngineId">Google Search Engine ID (looks like "a12b345...")</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public GoogleTextSearchService(
        string apiKey,
        string searchEngineId,
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
        ILoggerFactory? loggerFactory = null)
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
    public async Task<KernelSearchResults<T>> SearchAsync<T>(string query, SearchExecutionSettings? searchSettings = null, CancellationToken cancellationToken = default) where T : class
    {
        searchSettings ??= new SearchExecutionSettings();
        var count = searchSettings.Count;
        var offset = searchSettings.Offset;
        var searchResponse = await this.ExecuteSearchAsync(query, count, offset, cancellationToken).ConfigureAwait(false);

        return new KernelSearchResults<T>(searchResponse, this.GetResultsAsync<T>(searchResponse, cancellationToken), 1, GetResultsMetadata(searchResponse));
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        this._search.Dispose();
    }

    #region private

    private readonly ILogger _logger;
    private readonly CustomSearchAPIService _search;
    private readonly string? _searchEngineId;
    private readonly IReadOnlyDictionary<string, object?> _attributes;

    /// <summary>
    /// Execute a Google search
    /// </summary>
    /// <param name="query">The query string.</param>
    /// <param name="count">The number of results to return.</param>
    /// <param name="offset">The index of the first result to return.</param>
    /// <param name="cancellationToken">A cancellation token to cancel the request.</param>
    /// <exception cref="ArgumentOutOfRangeException"></exception>
    /// <exception cref="NotSupportedException"></exception>
    private async Task<global::Google.Apis.CustomSearchAPI.v1.Data.Search> ExecuteSearchAsync(string query, int count, int offset, CancellationToken cancellationToken)
    {
        if (count is <= 0 or > 10)
        {
            throw new ArgumentOutOfRangeException(nameof(count), count, $"{nameof(count)} value must be must be greater than 0 and less than or equals 10.");
        }

        if (offset < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(offset));
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
    private async IAsyncEnumerable<KernelSearchResult<T>> GetResultsAsync<T>(global::Google.Apis.CustomSearchAPI.v1.Data.Search searchResponse, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (searchResponse is null || searchResponse.Items is null)
        {
            yield break;
        }

        foreach (var item in searchResponse.Items)
        {
            if (item is T itemT)
            {
                yield return new GoogleKernelSearchResult<T>(itemT, searchResponse);
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
