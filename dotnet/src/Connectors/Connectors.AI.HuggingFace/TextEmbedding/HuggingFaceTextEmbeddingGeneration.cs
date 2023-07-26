// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.AI.HuggingFace.TextEmbedding;

/// <summary>
/// HuggingFace embedding generation service.
/// </summary>
#pragma warning disable CA1001 // Types that own disposable fields should be disposable. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
public sealed class HuggingFaceTextEmbeddingGeneration : ITextEmbeddingGeneration
#pragma warning restore CA1001 // Types that own disposable fields should be disposable. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
{
    private const string HttpUserAgent = "Microsoft-Semantic-Kernel";

    private readonly string _model;
    private readonly string? _endpoint;
    private readonly HttpClient _httpClient;

    /// <summary>
    /// Initializes a new instance of the <see cref="HuggingFaceTextEmbeddingGeneration"/> class.
    /// Using default <see cref="HttpClientHandler"/> implementation.
    /// </summary>
    /// <param name="endpoint">Endpoint for service API call.</param>
    /// <param name="model">Model to use for service API call.</param>
    public HuggingFaceTextEmbeddingGeneration(Uri endpoint, string model)
    {
        Verify.NotNull(endpoint);
        Verify.NotNullOrWhiteSpace(model);

        this._endpoint = endpoint.AbsoluteUri;
        this._model = model;

        this._httpClient = new HttpClient(NonDisposableHttpClientHandler.Instance, disposeHandler: false);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="HuggingFaceTextEmbeddingGeneration"/> class.
    /// </summary>
    /// <param name="model">Model to use for service API call.</param>
    /// <param name="endpoint">Endpoint for service API call.</param>
    public HuggingFaceTextEmbeddingGeneration(string model, string endpoint)
    {
        Verify.NotNullOrWhiteSpace(model);
        Verify.NotNullOrWhiteSpace(endpoint);

        this._model = model;
        this._endpoint = endpoint;

        this._httpClient = new HttpClient(NonDisposableHttpClientHandler.Instance, disposeHandler: false);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="HuggingFaceTextEmbeddingGeneration"/> class.
    /// </summary>
    /// <param name="model">Model to use for service API call.</param>
    /// <param name="httpClient">The HttpClient used for making HTTP requests.</param>
    /// <param name="endpoint">Endpoint for service API call. If not specified, the base address of the HTTP client is used.</param>
    public HuggingFaceTextEmbeddingGeneration(string model, HttpClient httpClient, string? endpoint = null)
    {
        Verify.NotNullOrWhiteSpace(model);
        Verify.NotNull(httpClient);

        this._model = model;
        this._endpoint = endpoint;
        this._httpClient = httpClient;

        if (httpClient.BaseAddress == null && string.IsNullOrEmpty(endpoint))
        {
            throw new ArgumentException("The HttpClient BaseAddress and endpoint are both null or empty. Please ensure at least one is provided.");
        }
    }

    /// <inheritdoc/>
    public async Task<IList<Embedding<float>>> GenerateEmbeddingsAsync(IList<string> data, CancellationToken cancellationToken = default)
    {
        return await this.ExecuteEmbeddingRequestAsync(data, cancellationToken).ConfigureAwait(false);
    }

    #region private ================================================================================

    /// <summary>
    /// Performs HTTP request to given endpoint for embedding generation.
    /// </summary>
    /// <param name="data">Data to embed.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>List of generated embeddings.</returns>
    /// <exception cref="HttpOperationException">Exception when backend didn't respond with generated embeddings.</exception>
    private async Task<IList<Embedding<float>>> ExecuteEmbeddingRequestAsync(IList<string> data, CancellationToken cancellationToken)
    {
        var embeddingRequest = new TextEmbeddingRequest
        {
            Input = data
        };

        using var httpRequestMessage = HttpRequest.CreatePostRequest(this.GetRequestUri(), embeddingRequest);

        httpRequestMessage.Headers.Add("User-Agent", HttpUserAgent);

        var response = await this._httpClient.SendAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);

        var responseContent = await response.Content.ReadAsStringAsync().ConfigureAwait(false);

        response.EnsureSuccess(responseContent);

        var embeddingResponse = JsonSerializer.Deserialize<TextEmbeddingResponse>(responseContent);

        return embeddingResponse?.Embeddings?.Select(l => new Embedding<float>(l.Embedding!, transferOwnership: true)).ToList()!;
    }

    /// <summary>
    /// Retrieves the request URI based on the provided endpoint and model information.
    /// </summary>
    /// <returns>
    /// A <see cref="Uri"/> object representing the request URI.
    /// </returns>
    private Uri GetRequestUri()
    {
        string? baseUrl = null;

        if (!string.IsNullOrEmpty(this._endpoint))
        {
            baseUrl = this._endpoint;
        }
        else if (this._httpClient.BaseAddress?.AbsoluteUri != null)
        {
            baseUrl = this._httpClient.BaseAddress!.AbsoluteUri;
        }
        else
        {
            throw new SKException("No endpoint or HTTP client base address has been provided");
        }

        return new Uri($"{baseUrl!.TrimEnd('/')}/{this._model}");
    }

    #endregion
}
