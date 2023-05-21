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

namespace Microsoft.SemanticKernel.Skills.Web.Bing;

/// <summary>
/// Bing API connector.
/// </summary>
public sealed class BingConnector : IWebSearchEngineConnector, IDisposable
{
    private readonly ILogger _logger;
    private readonly HttpClientHandler _httpClientHandler;
    private readonly HttpClient _httpClient;

    public BingConnector(string apiKey, ILogger<BingConnector>? logger = null)
    {
        this._logger = logger ?? NullLogger<BingConnector>.Instance;
        this._httpClientHandler = new() { CheckCertificateRevocationList = true };
        this._httpClient = new HttpClient(this._httpClientHandler);
        this._httpClient.DefaultRequestHeaders.Add("Ocp-Apim-Subscription-Key", apiKey);
    }

    /// <inheritdoc/>
    public async Task<IEnumerable<string>> SearchAsync(string query, List<string> relatedSites, int count = 1, int offset = 0, CancellationToken cancellationToken = default)
    {
        if (count <= 0) { throw new ArgumentOutOfRangeException(nameof(count)); }

        if (count >= 50) { throw new ArgumentOutOfRangeException(nameof(count), $"{nameof(count)} value must be less than 50."); }

        if (offset < 0) { throw new ArgumentOutOfRangeException(nameof(offset)); }

        UriBuilder uriBuilder = new("https://api.bing.microsoft.com/v7.0/search");

        uriBuilder.Query = $"q={Uri.EscapeDataString(query)}";

        if (relatedSites?.Count > 1) uriBuilder.Query += Uri.EscapeDataString($" site:{String.Join(" OR site:", relatedSites)}");
        else if (relatedSites?.Count == 1) uriBuilder.Query += Uri.EscapeDataString($" site:{relatedSites[0]}");

        uriBuilder.Query += $"&count={count}&offset={offset}";

        Uri uri = uriBuilder.Uri;

        this._logger.LogDebug("Sending request: {0}", uri);
        HttpResponseMessage response = await this._httpClient.GetAsync(uri, cancellationToken).ConfigureAwait(false);
        response.EnsureSuccessStatusCode();
        this._logger.LogDebug("Response received: {0}", response.StatusCode);

        string json = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
        this._logger.LogTrace("Response content received: {0}", json);

        BingSearchResponse? data = JsonSerializer.Deserialize<BingSearchResponse>(json);
        WebPage[]? results = data?.WebPages?.Value;

        return results == null ? Enumerable.Empty<string>() : results.Select(x => x.Snippet);
    }

    private void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._httpClient.Dispose();
            this._httpClientHandler.Dispose();
        }
    }

    public void Dispose()
    {
        // Do not change this code. Put cleanup code in 'Dispose(bool disposing)' method
        this.Dispose(disposing: true);
        GC.SuppressFinalize(this);
    }

    public Task<IEnumerable<string>> SearchAsync(string query, int count = 1, int offset = 0, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    public Task<IEnumerable<string>> SearchAsync(string query, string relatedSites, int count = 1, int offset = 0, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    [SuppressMessage("Performance", "CA1812:Internal class that is apparently never instantiated",
        Justification = "Class is instantiated through deserialization.")]
    private sealed class BingSearchResponse
    {
        [JsonPropertyName("webPages")]
        public WebPages? WebPages { get; set; }
    }

    [SuppressMessage("Performance", "CA1812:Internal class that is apparently never instantiated",
        Justification = "Class is instantiated through deserialization.")]
    private sealed class WebPages
    {
        [JsonPropertyName("value")]
        public WebPage[]? Value { get; set; }
    }

    [SuppressMessage("Performance", "CA1812:Internal class that is apparently never instantiated",
        Justification = "Class is instantiated through deserialization.")]
    private sealed class WebPage
    {
        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("url")]
        public string Url { get; set; } = string.Empty;

        [JsonPropertyName("snippet")]
        public string Snippet { get; set; } = string.Empty;
    }
}
