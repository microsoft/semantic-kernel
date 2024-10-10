// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>Base type for OpenAI text to image clients.</summary>
internal sealed class OpenAITextToImageClientCore
{
    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAITextToImageClientCore"/> class.
    /// </summary>
    /// <param name="httpClient">The HttpClient used for making HTTP requests.</param>
    /// <param name="logger">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    internal OpenAITextToImageClientCore(HttpClient? httpClient, ILogger? logger = null)
    {
        this._httpClient = HttpClientProvider.GetHttpClient(httpClient);
        this._logger = logger ?? NullLogger.Instance;
    }

    /// <summary>
    /// Storage for AI service attributes.
    /// </summary>
    internal Dictionary<string, object?> Attributes { get; } = [];

    /// <summary>
    /// Run the HTTP request to generate a list of images
    /// </summary>
    /// <param name="url">URL for the text to image request API</param>
    /// <param name="requestBody">Request payload</param>
    /// <param name="extractResponseFunc">Function to invoke to extract the desired portion of the text to image response.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>List of image URLs</returns>
    [Experimental("SKEXP0010")]
    internal async Task<IList<string>> ExecuteImageGenerationRequestAsync(
        string url,
        string requestBody,
        Func<TextToImageResponse.Image, string> extractResponseFunc,
        CancellationToken cancellationToken = default)
    {
        var result = await this.ExecutePostRequestAsync<TextToImageResponse>(url, requestBody, cancellationToken).ConfigureAwait(false);
        return result.Images.Select(extractResponseFunc).ToList();
    }

    /// <summary>
    /// Add attribute to the internal attribute dictionary if the value is not null or empty.
    /// </summary>
    /// <param name="key">Attribute key</param>
    /// <param name="value">Attribute value</param>
    internal void AddAttribute(string key, string? value)
    {
        if (!string.IsNullOrEmpty(value))
        {
            this.Attributes.Add(key, value);
        }
    }

    /// <summary>
    /// Logger
    /// </summary>
    private readonly ILogger _logger;

    /// <summary>
    /// The HttpClient used for making HTTP requests.
    /// </summary>
    private readonly HttpClient _httpClient;

    internal async Task<T> ExecutePostRequestAsync<T>(string url, string requestBody, CancellationToken cancellationToken = default)
    {
        using var content = new StringContent(requestBody, Encoding.UTF8, "application/json");
        using var response = await this.ExecuteRequestAsync(url, HttpMethod.Post, content, cancellationToken).ConfigureAwait(false);
        string responseJson = await response.Content.ReadAsStringWithExceptionMappingAsync().ConfigureAwait(false);
        T result = JsonSerializer.Deserialize<T>(responseJson, JsonOptionsCache.ReadPermissive) ?? throw new KernelException("Response JSON parse error");
        return result;
    }

    internal event EventHandler<HttpRequestMessage>? RequestCreated;

    internal async Task<HttpResponseMessage> ExecuteRequestAsync(string url, HttpMethod method, HttpContent? content, CancellationToken cancellationToken = default)
    {
        using var request = new HttpRequestMessage(method, url);

        if (content is not null)
        {
            request.Content = content;
        }

        request.Headers.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
        request.Headers.Add(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(typeof(OpenAITextToImageClientCore)));

        this.RequestCreated?.Invoke(this, request);

        var response = await this._httpClient.SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);

        if (this._logger.IsEnabled(LogLevel.Debug))
        {
            this._logger.LogDebug("HTTP response: {0} {1}", (int)response.StatusCode, response.StatusCode.ToString("G"));
        }

        return response;
    }
}
