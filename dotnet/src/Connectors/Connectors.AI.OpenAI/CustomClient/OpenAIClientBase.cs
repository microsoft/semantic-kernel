// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ImageGeneration;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextEmbedding;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.CustomClient;

/// <summary>Base type for OpenAI clients.</summary>
public abstract class OpenAIClientBase
{
    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIClientBase"/> class.
    /// </summary>
    /// <param name="httpClient">The HttpClient used for making HTTP requests.</param>
    /// <param name="loggerFactory">The ILoggerFactory used to create a logger for logging. If null, no logging will be performed.</param>
    private protected OpenAIClientBase(HttpClient? httpClient, ILoggerFactory? loggerFactory = null)
    {
        this._httpClient = httpClient ?? new HttpClient(NonDisposableHttpClientHandler.Instance, disposeHandler: false);
        this._logger = loggerFactory is not null ? loggerFactory.CreateLogger(this.GetType()) : NullLogger.Instance;
    }

    /// <summary>Adds headers to use for OpenAI HTTP requests.</summary>
    private protected virtual void AddRequestHeaders(HttpRequestMessage request)
    {
        request.Headers.Add("User-Agent", Telemetry.HttpUserAgent);
    }

    /// <summary>
    /// Asynchronously sends a text embedding request for the text.
    /// </summary>
    /// <param name="url">URL for the text embedding request API</param>
    /// <param name="requestBody">Request payload</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>List of text embeddings</returns>
    private protected async Task<IList<ReadOnlyMemory<float>>> ExecuteTextEmbeddingRequestAsync(
        string url,
        string requestBody,
        CancellationToken cancellationToken = default)
    {
        var result = await this.ExecutePostRequestAsync<TextEmbeddingResponse>(url, requestBody, cancellationToken).ConfigureAwait(false);
        if (result.Embeddings is not { Count: >= 1 })
        {
            throw new SKException("Embeddings not found");
        }

        return result.Embeddings.Select(e => e.Values).ToList();
    }

    /// <summary>
    /// Run the HTTP request to generate a list of images
    /// </summary>
    /// <param name="url">URL for the image generation request API</param>
    /// <param name="requestBody">Request payload</param>
    /// <param name="extractResponseFunc">Function to invoke to extract the desired portion of the image generation response.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>List of image URLs</returns>
    private protected async Task<IList<string>> ExecuteImageGenerationRequestAsync(
        string url,
        string requestBody,
        Func<ImageGenerationResponse.Image, string> extractResponseFunc,
        CancellationToken cancellationToken = default)
    {
        var result = await this.ExecutePostRequestAsync<ImageGenerationResponse>(url, requestBody, cancellationToken).ConfigureAwait(false);
        return result.Images.Select(extractResponseFunc).ToList();
    }

    #region private ================================================================================

    /// <summary>
    /// Logger
    /// </summary>
    private readonly ILogger _logger;

    /// <summary>
    /// The HttpClient used for making HTTP requests.
    /// </summary>
    private readonly HttpClient _httpClient;

    private protected async Task<T> ExecutePostRequestAsync<T>(string url, string requestBody, CancellationToken cancellationToken = default)
    {
        using var content = new StringContent(requestBody, Encoding.UTF8, "application/json");
        using var response = await this.ExecuteRequestAsync(url, HttpMethod.Post, content, cancellationToken).ConfigureAwait(false);
        string responseJson = await response.Content.ReadAsStringWithExceptionMappingAsync().ConfigureAwait(false);
        T result = this.JsonDeserialize<T>(responseJson);
        return result;
    }

    private protected T JsonDeserialize<T>(string responseJson)
    {
        var result = Json.Deserialize<T>(responseJson);
        if (result is null)
        {
            throw new SKException("Response JSON parse error");
        }

        return result;
    }

    private protected async Task<HttpResponseMessage> ExecuteRequestAsync(string url, HttpMethod method, HttpContent? content, CancellationToken cancellationToken = default)
    {
        using var request = new HttpRequestMessage(method, url);

        this.AddRequestHeaders(request);

        if (content != null)
        {
            request.Content = content;
        }

        var response = await this._httpClient.SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);

        this._logger.LogDebug("HTTP response: {0} {1}", (int)response.StatusCode, response.StatusCode.ToString("G"));

        return response;
    }

    #endregion
}
