// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Plugins.Web.Bing;

/// <summary>
/// Bing API connector.
/// </summary>
public sealed class BingConnector : IWebSearchEngineConnector
{
    private readonly ILogger _logger;
    private readonly HttpClient _httpClient;
    private readonly string? _apiKey;
    private readonly string? _uri;
    private const string DefaultUri = "https://api.bing.microsoft.com/v7.0/search?q";

    /// <summary>
    /// Initializes a new instance of the <see cref="BingConnector"/> class.
    /// </summary>
    /// <param name="apiKey">The API key to authenticate the connector.</param>
    /// <param name="uri"></param>
    /// <param name="logger">An optional logger to log connector-related information.</param>
    [SuppressMessage("Performance", "CA1054:Change the type of parameter 'uri'...",
        Justification = "A constant Uri cannot be defined, as required by this class")]
    public BingConnector(string apiKey, string uri = DefaultUri, ILogger<BingConnector>? logger = null) :
        this(apiKey, new HttpClient(NonDisposableHttpClientHandler.Instance, false), uri, logger)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="BingConnector"/> class.
    /// </summary>
    /// <param name="apiKey">The API key to authenticate the connector.</param>
    /// <param name="httpClient">The HTTP client to use for making requests.</param>
    /// <param name="uri"></param>
    /// <param name="logger">An optional logger to log connector-related information.</param>
    [SuppressMessage("Performance", "CA1054:Change the type of parameter 'uri'...",
        Justification = "A constant Uri cannot be defined, as required by this class")]
    public BingConnector(string apiKey, HttpClient httpClient, string uri = DefaultUri, ILogger<BingConnector>? logger = null)
    {
        Verify.NotNull(httpClient);

        this._apiKey = apiKey;
        this._logger = logger is not null ? logger : NullLogger.Instance;
        this._httpClient = httpClient;
        this._uri = string.IsNullOrEmpty(uri) ? BingConnector.DefaultUri : uri;
    }

    /// <inheritdoc/>
    public async Task<IEnumerable<T>> SearchAsync<T>(string query, int count = 1, int offset = 0, CancellationToken cancellationToken = default)
    {
        if (count is <= 0 or >= 50)
        {
            throw new ArgumentOutOfRangeException(nameof(count), count, $"{nameof(count)} value must be greater than 0 and less than 50.");
        }

        Uri uri = new($"{this._uri}={Uri.EscapeDataString(query.Trim())}&count={count}&offset={offset}");

        this._logger.LogDebug("Sending request: {Uri}", uri);

        using HttpResponseMessage response = await this.SendGetRequestAsync(uri, cancellationToken).ConfigureAwait(false);

        this._logger.LogDebug("Response received: {StatusCode}", response.StatusCode);

        string json = await response.Content.ReadAsStringWithExceptionMappingAsync().ConfigureAwait(false);

        // Sensitive data, logging as trace, disabled by default
        this._logger.LogTrace("Response content received: {Data}", json);

        WebSearchResponse? data = JsonSerializer.Deserialize<WebSearchResponse>(json);

        List<T>? returnValues = new();
        if (data?.WebPages?.Value != null)
        {
            if (typeof(T) == typeof(string))
            {
                WebPage[]? results = data?.WebPages?.Value;
                returnValues = results?.Select(x => x.Snippet).ToList() as List<T>;
            }
            else if (typeof(T) == typeof(WebPage))
            {
                List<WebPage>? webPages = new();
#pragma warning disable 8602 // Disable null check warning for data?.WebPages?.Value which is not null here.
                foreach (var webPage in data?.WebPages?.Value)
#pragma warning restore 8602
                {
                    webPages.Add(webPage);
                }
                returnValues = webPages.Take(count).ToList() as List<T>;
            }
            else
            {
                throw new NotSupportedException($"Type {typeof(T)} is not supported.");
            }
        }
        return returnValues != null && returnValues.Count == 0 ? returnValues : returnValues.Take(count);
    }

    /// <summary>
    /// Sends a GET request to the specified URI.
    /// </summary>
    /// <param name="uri">The URI to send the request to.</param>
    /// <param name="cancellationToken">A cancellation token to cancel the request.</param>
    /// <returns>A <see cref="HttpResponseMessage"/> representing the response from the request.</returns>
    private async Task<HttpResponseMessage> SendGetRequestAsync(Uri uri, CancellationToken cancellationToken = default)
    {
        using var httpRequestMessage = new HttpRequestMessage(HttpMethod.Get, uri);

        if (!string.IsNullOrEmpty(this._apiKey))
        {
            httpRequestMessage.Headers.Add("Ocp-Apim-Subscription-Key", this._apiKey);
        }

        return await this._httpClient.SendWithSuccessCheckAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);
    }
}
