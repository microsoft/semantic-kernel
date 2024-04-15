// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
using Microsoft.SemanticKernel.Search;

namespace Microsoft.SemanticKernel.Plugins.Web.Google;

/// <summary>
/// A Google Search service that creates and recalls memories associated with text.
/// </summary>
public sealed class GoogleTextSearchService : ITextSearchService
{
    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._attributes;

    /// <summary>
    /// Create an instance of the <see cref="GoogleTextSearchService"/> connector with API key authentication.
    /// </summary>
    /// <param name="endpoint">Required. The URI endpoint of the Google search service. The URI must use HTTPS.</param>
    /// <param name="apiKey">Required. The API key credential used to authenticate requests against the Search service.</param>
    /// <param name="httpClient">The HTTP client to use for making requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public GoogleTextSearchService(string endpoint, string apiKey, HttpClient? httpClient = null, ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(apiKey);

        this._uri = new Uri(endpoint ?? DefaultUri);
        this._apiKey = apiKey;
        this._logger = loggerFactory?.CreateLogger(typeof(BingTextSearchService)) ?? NullLogger.Instance;
        this._httpClient = httpClient ?? HttpClientProvider.GetHttpClient();
        this._httpClient.DefaultRequestHeaders.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
        this._httpClient.DefaultRequestHeaders.Add(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(typeof(BingTextSearchService)));

        this._attributes = new Dictionary<string, object?>
        {
        };
    }

    /// <inheritdoc/>
    public Task<KernelSearchResults<T>> SearchAsync<T>(string query, SearchExecutionSettings searchSettings, CancellationToken cancellationToken = default) where T : class
    {
        throw new NotImplementedException();
    }

    #region private

    private readonly ILogger _logger;
    private readonly HttpClient _httpClient;
    private readonly string? _apiKey;
    private readonly Uri? _uri = null;
    private readonly IReadOnlyDictionary<string, object?> _attributes;

    private const string DefaultUri = "https://api.bing.microsoft.com/v7.0/search?q";

    #endregion
}
