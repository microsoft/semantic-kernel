// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Google.Apis.Customsearch.v1;
using Google.Apis.Services;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.SemanticKernel.Skills.Web.Google;

/// <summary>
/// Bing API connector.
/// </summary>
public class GoogleConnector : IWebSearchEngineConnector, IDisposable
{
    private readonly ILogger _logger;
    private readonly CustomsearchService _search;
    private readonly string _searchEngineId;

    public GoogleConnector(string apiKey, string searchEngineId, ILogger<GoogleConnector>? logger = null)
    {
        this._logger = logger ?? NullLogger<GoogleConnector>.Instance;
        this._search = new CustomsearchService(new BaseClientService.Initializer { ApiKey = apiKey });
        this._searchEngineId = searchEngineId;
    }

    /// <inheritdoc/>
    public async Task<string> SearchAsync(string query, CancellationToken cancellationToken = default)
    {
        var search = this._search.Cse.List();
        search.Cx = this._searchEngineId;
        search.Q = query;

        var results = await search.ExecuteAsync(cancellationToken);

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
