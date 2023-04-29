// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Google.Apis.CustomSearchAPI.v1;
using Google.Apis.Services;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.SemanticKernel.Skills.Web.Google;

/// <summary>
/// Google search connector.
/// </summary>
public class GoogleConnector : IWebSearchEngineConnector, IDisposable
{
    private readonly ILogger _logger;
    private readonly CustomSearchAPIService _search;
    private readonly string? _searchEngineId;

    /// <summary>
    /// Google search connector
    /// </summary>
    /// <param name="apiKey">Google Custom Search API (looks like "ABcdEfG1...")</param>
    /// <param name="searchEngineId">Google Search Engine ID (looks like "a12b345...")</param>
    /// <param name="logger">Optional logger</param>
    public GoogleConnector(
        string apiKey,
        string searchEngineId,
        ILogger<GoogleConnector>? logger = null)
    {
        this._search = new CustomSearchAPIService(new BaseClientService.Initializer { ApiKey = apiKey });
        this._searchEngineId = searchEngineId;
        this._logger = logger ?? NullLogger<GoogleConnector>.Instance;
    }

    /// <inheritdoc/>
    public async Task<string> SearchAsync(string query, CancellationToken cancellationToken = default)
    {
        var search = this._search.Cse.List();
        search.Cx = this._searchEngineId;
        search.Q = query;

        var results = await search.ExecuteAsync(cancellationToken).ConfigureAwait(false);

        var first = results.Items?.FirstOrDefault();
        this._logger.LogDebug("Result: {Title}, {Link}, {Snippet}", first?.Title, first?.Link, first?.Snippet);

        return first?.Snippet ?? string.Empty;
    }

    protected virtual void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._search.Dispose();
        }
    }

    public void Dispose()
    {
        this.Dispose(disposing: true);
        GC.SuppressFinalize(this);
    }
}
