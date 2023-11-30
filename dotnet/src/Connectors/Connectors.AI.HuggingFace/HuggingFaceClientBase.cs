// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.AI.HuggingFace;

/// <summary>Base type for HuggingFace clients.</summary>
#pragma warning disable CA1001 // Types that own disposable fields should be disposable. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
public abstract class HuggingFaceClientBase
#pragma warning disable CA1001 // Types that own disposable fields should be disposable. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
{
    /// <summary>
    /// Default HuggingFace API to use.
    /// </summary>
    protected string? HuggingFaceApiEndpoint { get; set; } = "https://api-inference.huggingface.co/models";

    /// <summary>
    /// Attributes to be sent to the HuggingFace API.
    /// </summary>
    protected Dictionary<string, string> ClientAttributes { get; } = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="HuggingFaceClientBase"/> class.
    /// Using default <see cref="HttpClientHandler"/> implementation.
    /// </summary>
    /// <param name="endpoint">Endpoint for service API call.</param>
    /// <param name="model">Model to use for service API call.</param>
    protected HuggingFaceClientBase(Uri endpoint, string model)
    {
        Verify.NotNull(endpoint);
        Verify.NotNullOrWhiteSpace(model);

        this._endpoint = endpoint.AbsoluteUri;
        this._model = model;
        this._httpClient = HttpClientProvider.GetHttpClient();

        this.ClientAttributes.Add(IAIServiceExtensions.ModelIdKey, this._model);
        this.ClientAttributes.Add(IAIServiceExtensions.EndpointKey, this._endpoint);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="HuggingFaceClientBase"/> class.
    /// Using HuggingFace API for service call, see https://huggingface.co/docs/api-inference/index.
    /// </summary>
    /// <param name="model">The name of the model to use for text completion.</param>
    /// <param name="apiKey">The API key for accessing the Hugging Face service.</param>
    /// <param name="httpClient">The HTTP client to use for making API requests. If not specified, a default client will be used.</param>
    /// <param name="endpoint">The endpoint URL for the Hugging Face service.
    /// If not specified, the base address of the HTTP client is used. If the base address is not available, a default endpoint will be used.</param>
    protected HuggingFaceClientBase(string model, string? apiKey = null, HttpClient? httpClient = null, string? endpoint = null)
    {
        Verify.NotNullOrWhiteSpace(model);

        if (string.IsNullOrEmpty(endpoint) && (httpClient == null || httpClient.BaseAddress == null))
        {
            throw new KernelException("The HttpClient BaseAddress and endpoint are both null or empty. Please ensure at least one is provided.");
        }

        this._model = model;
        this._apiKey = apiKey;
        this._httpClient = HttpClientProvider.GetHttpClient(httpClient);
        this._endpoint = endpoint;

        this.ClientAttributes.Add(IAIServiceExtensions.ModelIdKey, this._model);
        this.ClientAttributes.Add(IAIServiceExtensions.EndpointKey, endpoint ?? httpClient!.BaseAddress!.ToString());
    }

    /// <summary>
    /// Send a HTTP POST request message.
    /// </summary>
    /// <param name="payload"></param>
    /// <param name="cancellationToken"></param>
    private protected async Task<HttpResponseMessage> SendPostRequestAsync(object? payload, CancellationToken cancellationToken = default)
    {
        using var httpRequestMessage = HttpRequest.CreatePostRequest(this.GetRequestUri(), payload);

        httpRequestMessage.Headers.Add("User-Agent", HttpHeaderValues.UserAgent);
        if (!string.IsNullOrEmpty(this._apiKey))
        {
            httpRequestMessage.Headers.Add("Authorization", $"Bearer {this._apiKey}");
        }

        return await this._httpClient.SendWithSuccessCheckAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Retrieves the request URI based on the provided endpoint and model information.
    /// </summary>
    /// <returns>
    /// A <see cref="Uri"/> object representing the request URI.
    /// </returns>
    private protected Uri GetRequestUri()
    {
        var baseUrl = this.HuggingFaceApiEndpoint;

        if (!string.IsNullOrEmpty(this._endpoint))
        {
            baseUrl = this._endpoint;
        }
        else if (this._httpClient.BaseAddress?.AbsoluteUri != null)
        {
            baseUrl = this._httpClient.BaseAddress!.AbsoluteUri;
        }
        else if (baseUrl is null)
        {
            throw new SKException("No endpoint or HTTP client base address has been provided");
        }

        return new Uri($"{baseUrl!.TrimEnd('/')}/{this._model}");
    }

    #region private

    private readonly string _model;
    private readonly string? _endpoint;
    private readonly HttpClient _httpClient;
    private readonly string? _apiKey;

    #endregion
}
