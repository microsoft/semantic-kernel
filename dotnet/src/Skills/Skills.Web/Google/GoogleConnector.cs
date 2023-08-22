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
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Skills.Web.Google;

/// <summary>
/// Google search connector.
/// Provides methods to search using Google Custom Search API.
/// </summary>
/// <example>
/// <code>
/// var apiKey = "your_api_key";
/// var searchEngineId = "your_search_engine_id";
/// var googleConnector = new GoogleConnector(apiKey, searchEngineId);
/// var searchResults = await googleConnector.SearchAsync("example query", 10, 0, CancellationToken.None);
/// </code>
/// </example>
public sealed class GoogleConnector : IWebSearchEngineConnector, IDisposable
{
    private readonly ILogger _logger;
    private readonly CustomSearchAPIService _search;
    private readonly string? _searchEngineId;

    /// <summary>
    /// Initializes a new instance of the <see cref="GoogleConnector"/> class.
    /// </summary>
    /// <param name="apiKey">Google Custom Search API key (looks like "ABcdEfG1...").</param>
    /// <param name="searchEngineId">Google Search Engine ID (looks like "a12b345...").</param>
    /// <param name="logger">Optional logger.</param>
    public GoogleConnector(
        string apiKey,
        string searchEngineId,
        ILogger<GoogleConnector>? logger = null) : this(new BaseClientService.Initializer { ApiKey = apiKey }, searchEngineId, logger)
    {
        Verify.NotNullOrWhiteSpace(apiKey);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="GoogleConnector"/> class.
    /// </summary>
    /// <param name="initializer">The connector initializer.</param>
    /// <param name="searchEngineId">Google Search Engine ID (looks like "a12b345...").</param>
    /// <param name="logger">Optional logger.</param>
    public GoogleConnector(
        BaseClientService.Initializer initializer,
        string searchEngineId,
        ILogger<GoogleConnector>? logger = null)
    {
        Verify.NotNull(initializer);
        Verify.NotNullOrWhiteSpace(searchEngineId);

        this._search = new CustomSearchAPIService(initializer);
        this._searchEngineId = searchEngineId;
        this._logger = logger ?? NullLogger<GoogleConnector>.Instance;
    }

    /// <inheritdoc/>
    public async Task<IEnumerable<string>> SearchAsync(
        string query,
        int count,
        int offset,
        CancellationToken cancellationToken)
    {
        if (count <= 0) { throw new ArgumentOutOfRangeException(nameof(count)); }

        if (count > 10) { throw new ArgumentOutOfRangeException(nameof(count), $"{nameof(count)} value must be between 0 and 10, inclusive."); }

        if (offset < 0) { throw new ArgumentOutOfRangeException(nameof(offset)); }

        var search = this._search.Cse.List();
        search.Cx = this._searchEngineId;
        search.Q = query;
        search.Num = count;
        search.Start = offset;

        var results = await search.ExecuteAsync(cancellationToken).ConfigureAwait(false);

        return results.Items.Select(item => item.Snippet);
    }

    /// <summary>
    /// Releases the unmanaged resources used by the GoogleConnector and optionally releases the managed resources.
    /// </summary>
    /// <param name="disposing">true to release both managed and unmanaged resources; false to release only unmanaged resources.</param>
    private void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._search.Dispose();
        }
    }

    /// <summary>
    /// Performs application-defined tasks associated with freeing, releasing, or resetting unmanaged resources.
    /// </summary>
    public void Dispose()
    {
        this.Dispose(disposing: true);
        GC.SuppressFinalize(this);
    }
}
