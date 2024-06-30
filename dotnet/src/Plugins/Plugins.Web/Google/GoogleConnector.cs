// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Google.Apis.CustomSearchAPI.v1;
using Google.Apis.Services;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.SemanticKernel.Plugins.Web.Google;

/// <summary>
/// Google search connector.
/// Provides methods to search using Google Custom Search API.
/// </summary>
public sealed class GoogleConnector : IWebSearchEngineConnector, IDisposable
{
    private readonly ILogger _logger;
    private readonly CustomSearchAPIService _search;
    private readonly string? _searchEngineId;

    /// <summary>
    /// Initializes a new instance of the <see cref="GoogleConnector"/> class.
    /// </summary>
    /// <param name="apiKey">Google Custom Search API (looks like "ABcdEfG1...")</param>
    /// <param name="searchEngineId">Google Search Engine ID (looks like "a12b345...")</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public GoogleConnector(
        string apiKey,
        string searchEngineId,
        ILoggerFactory? loggerFactory = null) : this(new BaseClientService.Initializer { ApiKey = apiKey }, searchEngineId, loggerFactory)
    {
        Verify.NotNullOrWhiteSpace(apiKey);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="GoogleConnector"/> class.
    /// </summary>
    /// <param name="initializer">The connector initializer</param>
    /// <param name="searchEngineId">Google Search Engine ID (looks like "a12b345...")</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public GoogleConnector(
        BaseClientService.Initializer initializer,
        string searchEngineId,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(initializer);
        Verify.NotNullOrWhiteSpace(searchEngineId);

        this._search = new CustomSearchAPIService(initializer);
        this._searchEngineId = searchEngineId;
        this._logger = loggerFactory?.CreateLogger(typeof(GoogleConnector)) ?? NullLogger.Instance;
    }

    /// <inheritdoc/>
    public async Task<IEnumerable<T>> SearchAsync<T>(
        string query,
        int count,
        int offset,
        CancellationToken cancellationToken)
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

        var results = await search.ExecuteAsync(cancellationToken).ConfigureAwait(false);

        List<T>? returnValues = null;
        if (results.Items is not null)
        {
            if (typeof(T) == typeof(string))
            {
                returnValues = results.Items.Select(item => item.Snippet).ToList() as List<T>;
            }
            else if (typeof(T) == typeof(WebPage))
            {
                List<WebPage> webPages = [];
                foreach (var item in results.Items)
                {
                    WebPage webPage = new()
                    {
                        Name = item.Title,
                        Snippet = item.Snippet,
                        Url = item.Link
                    };
                    webPages.Add(webPage);
                }
                returnValues = webPages.Take(count).ToList() as List<T>;
            }
            else
            {
                throw new NotSupportedException($"Type {typeof(T)} is not supported.");
            }
        }

        return
            returnValues is null ? [] :
            returnValues.Count <= count ? returnValues :
            returnValues.Take(count);
    }

    /// <summary>
    /// Disposes the <see cref="GoogleConnector"/> instance.
    /// </summary>
    public void Dispose()
    {
        this._search.Dispose();
    }
}
