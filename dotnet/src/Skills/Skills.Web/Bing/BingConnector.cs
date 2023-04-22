// Copyright (c) Microsoft. All rights reserved.

using System;
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
public class BingConnector : IWebSearchEngineConnector, IDisposable
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
    public async Task<string> SearchAsync(string query, CancellationToken cancellationToken = default)
    {
        Uri uri = new($"https://api.bing.microsoft.com/v7.0/search?q={Uri.EscapeDataString(query)}&count=1");

        this._logger.LogDebug("Sending request: {0}", uri);
        HttpResponseMessage response = await this._httpClient.GetAsync(uri, cancellationToken);
        response.EnsureSuccessStatusCode();
        this._logger.LogDebug("Response received: {0}", response.StatusCode);

        string json = await response.Content.ReadAsStringAsync();
        this._logger.LogTrace("Response content received: {0}", json);

        BingSearchResponse? data = JsonSerializer.Deserialize<BingSearchResponse>(json);
        WebPage? firstResult = data?.WebPages?.Value?.FirstOrDefault();

        this._logger.LogDebug("Result: {0}, {1}, {2}",
            firstResult?.Name,
            firstResult?.Url,
            firstResult?.Snippet);

        return firstResult?.Snippet ?? string.Empty;
    }

    protected virtual void Dispose(bool disposing)
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
