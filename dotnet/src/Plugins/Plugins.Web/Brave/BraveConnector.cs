// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Plugins.Web.Brave;

/// <summary>
/// Brave API connector.
/// </summary>
public sealed class BraveConnector : IWebSearchEngineConnector
{
    private readonly ILogger _logger;
    private readonly HttpClient _httpClient;
    private readonly string? _apiKey;
    private readonly Uri? _uri = null;
    private const string DefaultUri = "https://api.search.brave.com/res/v1/web/search?q";

    /// <summary>
    /// Initializes a new instance of the <see cref="BraveConnector"/> class.
    /// </summary>
    /// <param name="apiKey">The API key to authenticate the connector.</param>
    /// <param name="uri">The URI of the Bing Search instance. Defaults to "https://api.bing.microsoft.com/v7.0/search?q".</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public BraveConnector(string apiKey, Uri? uri = null, ILoggerFactory? loggerFactory = null) :
        this(apiKey, HttpClientProvider.GetHttpClient(), uri, loggerFactory)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="BraveConnector"/> class.
    /// </summary>
    /// <param name="apiKey">The API key to authenticate the connector.</param>
    /// <param name="httpClient">The HTTP client to use for making requests.</param>
    /// <param name="uri">The URI of the Bing Search instance. Defaults to "https://api.bing.microsoft.com/v7.0/search?q".</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public BraveConnector(string apiKey, HttpClient httpClient, Uri? uri = null, ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(httpClient);

        this._apiKey = apiKey;
        this._logger = loggerFactory?.CreateLogger(typeof(BraveConnector)) ?? NullLogger.Instance;
        this._httpClient = httpClient;
        this._httpClient.DefaultRequestHeaders.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
        this._httpClient.DefaultRequestHeaders.Add(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(typeof(BraveConnector)));
        this._uri = uri ?? new Uri(DefaultUri);
    }

    /// <inheritdoc/>
    public async Task<IEnumerable<T>> SearchAsync<T>(string query, int count = 1, int offset = 0, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(query);

        if (count is <= 0 or >= 21)
        {
            throw new ArgumentOutOfRangeException(nameof(count), count, $"{nameof(count)} value must be greater than 0 and less than 21.");
        }

        if (offset is < 0 or > 10)
        {
            throw new ArgumentOutOfRangeException(nameof(offset), offset, $"{nameof(count)} value must be equal or greater than 0 and less than 10.");
        }

        Uri uri = new($"{this._uri}={Uri.EscapeDataString(query.Trim())}&count={count}&offset={offset}");

        this._logger.LogDebug("Sending request: {Uri}", uri);

        using HttpResponseMessage response = await this.SendGetRequestAsync(uri, cancellationToken).ConfigureAwait(false);

        this._logger.LogDebug("Response received: {StatusCode}", response.StatusCode);

        string json = await response.Content.ReadAsStringWithExceptionMappingAsync(cancellationToken).ConfigureAwait(false);

        // Sensitive data, logging as trace, disabled by default
        this._logger.LogTrace("Response content received: {Data}", json);

        var data = JsonSerializer.Deserialize<BraveSearchResponse<BraveWebResult>>(json);

        List<T>? returnValues = null;
        if (data?.Web?.Results is not null)
        {
            if (typeof(T) == typeof(string))
            {
                var results = data?.Web?.Results;
                returnValues = results?.Select(x => x.Description).ToList() as List<T>;
            }
            else if (typeof(T) == typeof(BraveWebResult))
            {
                var results = data?.Web?.Results!;
                returnValues = results.Take(count).ToList() as List<T>;
            }
            else if (typeof(T) == typeof(WebPage))
            {
                List<WebPage>? webPages = data.Web?.Results
                    .Select(x => new WebPage() { Name = x.Title, Snippet = x.Description, Url = x.Url }).ToList();

                returnValues = webPages!.Take(count).ToList() as List<T>;
            }
            else
            {
                throw new NotSupportedException($"Type {typeof(T)} is not supported.");
            }
        }

        if (data?.Videos?.Results is not null)
        {
            if (typeof(T) == typeof(string))
            {
                var results = data?.Videos?.Results;
                returnValues = results?.Select(x => x.Description).ToList() as List<T>;
            }
            else if (typeof(T) == typeof(BraveWebResult))
            {
                var results = data?.Videos?.Results!;
                returnValues = results.Take(count).ToList() as List<T>;
            }
            else if (typeof(T) == typeof(WebPage))
            {
                List<WebPage>? webPages = data.Videos?.Results
                    .Select(x => new WebPage() { Name = x.Title, Snippet = x.Description, Url = x.Url }).ToList();

                returnValues = webPages!.Take(count).ToList() as List<T>;
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
            httpRequestMessage.Headers.Add("X-Subscription-Token", this._apiKey);
        }

        return await this._httpClient.SendWithSuccessCheckAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);
    }
}
