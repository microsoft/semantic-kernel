// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.AI.HuggingFace.TextCompletion;

/// <summary>
/// HuggingFace text completion service.
/// </summary>
public sealed class HuggingFaceTextCompletion : ITextCompletion, IDisposable
{
    private const string HttpUserAgent = "Microsoft-Semantic-Kernel";
    private const string HuggingFaceApiEndpoint = "https://api-inference.huggingface.co/models";

    private readonly string _model;
    private readonly string? _endpoint;
    private readonly HttpClient _httpClient;
    private readonly bool _disposeHttpClient = true;
    private readonly string? _apiKey;

    /// <summary>
    /// Initializes a new instance of the <see cref="HuggingFaceTextCompletion"/> class.
    /// </summary>
    /// <param name="endpoint">Endpoint for service API call.</param>
    /// <param name="model">Model to use for service API call.</param>
    /// <param name="httpClientHandler">Instance of <see cref="HttpClientHandler"/> to setup specific scenarios.</param>
    [Obsolete("This constructor is deprecated and will be removed in one of the next SK SDK versions. Please use one of the alternative constructors.")]
    public HuggingFaceTextCompletion(Uri endpoint, string model, HttpClientHandler httpClientHandler)
    {
        Verify.NotNull(endpoint);
        Verify.NotNullOrWhiteSpace(model);

        this._endpoint = endpoint.AbsoluteUri;
        this._model = model;

        this._httpClient = new(httpClientHandler);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="HuggingFaceTextCompletion"/> class.
    /// Using default <see cref="HttpClientHandler"/> implementation.
    /// </summary>
    /// <param name="endpoint">Endpoint for service API call.</param>
    /// <param name="model">Model to use for service API call.</param>
    public HuggingFaceTextCompletion(Uri endpoint, string model)
    {
        Verify.NotNull(endpoint);
        Verify.NotNullOrWhiteSpace(model);

        this._endpoint = endpoint.AbsoluteUri;
        this._model = model;

        this._httpClient = new HttpClient(NonDisposableHttpClientHandler.Instance, disposeHandler: false);
        this._disposeHttpClient = false; // Disposal is unnecessary as a non-disposable handler is used.
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="HuggingFaceTextCompletion"/> class.
    /// Using HuggingFace API for service call, see https://huggingface.co/docs/api-inference/index.
    /// </summary>
    /// <param name="apiKey">HuggingFace API key, see https://huggingface.co/docs/api-inference/quicktour#running-inference-with-api-requests.</param>
    /// <param name="model">Model to use for service API call.</param>
    /// <param name="httpClientHandler">Instance of <see cref="HttpClientHandler"/> to setup specific scenarios.</param>
    /// <param name="endpoint">Endpoint for service API call.</param>
    [Obsolete("This constructor is deprecated and will be removed in one of the next SK SDK versions. Please use one of the alternative constructors.")]
    public HuggingFaceTextCompletion(string apiKey, string model, HttpClientHandler httpClientHandler, string endpoint = HuggingFaceApiEndpoint)
        : this(new Uri(endpoint), model, httpClientHandler)
    {
        Verify.NotNullOrWhiteSpace(apiKey);
        this._apiKey = apiKey;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="HuggingFaceTextCompletion"/> class.
    /// Using HuggingFace API for service call, see https://huggingface.co/docs/api-inference/index.
    /// Using default <see cref="HttpClientHandler"/> implementation.
    /// </summary>
    /// <param name="apiKey">HuggingFace API key, see https://huggingface.co/docs/api-inference/quicktour#running-inference-with-api-requests.</param>
    /// <param name="model">Model to use for service API call.</param>
    /// <param name="endpoint">Endpoint for service API call.</param>
    [Obsolete("This constructor is deprecated and will be removed in one of the next SK SDK versions. Please use one of the alternative constructors.")]
    public HuggingFaceTextCompletion(string apiKey, string model, string endpoint = HuggingFaceApiEndpoint)
        : this(new Uri(endpoint), model)
    {
        Verify.NotNullOrWhiteSpace(apiKey);
        this._apiKey = apiKey;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="HuggingFaceTextCompletion"/> class.
    /// Using HuggingFace API for service call, see https://huggingface.co/docs/api-inference/index.
    /// </summary>
    /// <param name="model">The name of the model to use for text completion.</param>
    /// <param name="apiKey">The API key for accessing the Hugging Face service.</param>
    /// <param name="httpClient">The HTTP client to use for making API requests. If not specified, a default client will be used.</param>
    /// <param name="endpoint">The endpoint URL for the Hugging Face service.
    /// If not specified, the base address of the HTTP client is used. If the base address is not available, a default endpoint will be used.</param>
    public HuggingFaceTextCompletion(string model, string? apiKey = null, HttpClient? httpClient = null, string? endpoint = null)
    {
        Verify.NotNullOrWhiteSpace(model);

        this._model = model;
        this._apiKey = apiKey;
        this._httpClient = httpClient ?? new HttpClient(NonDisposableHttpClientHandler.Instance, disposeHandler: false);
        this._endpoint = endpoint;
        this._disposeHttpClient = false; // Disposal is unnecessary as we either use a non-disposable handler or utilize a custom HTTP client that we should not dispose.
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<ITextStreamingResult> GetStreamingCompletionsAsync(
        string text,
        CompleteRequestSettings requestSettings,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        foreach (var completion in await this.ExecuteGetCompletionsAsync(text, cancellationToken).ConfigureAwait(false))
        {
            yield return completion;
        }
    }

    /// <inheritdoc/>
    public async Task<IReadOnlyList<ITextResult>> GetCompletionsAsync(
        string text,
        CompleteRequestSettings requestSettings,
        CancellationToken cancellationToken = default)
    {
        return await this.ExecuteGetCompletionsAsync(text, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    [Obsolete("This method is deprecated and will be removed in one of the next SK SDK versions.")]
    public void Dispose()
    {
        if (this._disposeHttpClient)
        {
            this._httpClient.Dispose();
        }
    }

    #region private ================================================================================

    private async Task<IReadOnlyList<ITextStreamingResult>> ExecuteGetCompletionsAsync(string text, CancellationToken cancellationToken = default)
    {
        try
        {
            var completionRequest = new TextCompletionRequest
            {
                Input = text
            };

            using var httpRequestMessage = new HttpRequestMessage()
            {
                Method = HttpMethod.Post,
                RequestUri = this.GetRequestUri(),
                Content = new StringContent(JsonSerializer.Serialize(completionRequest)),
            };

            httpRequestMessage.Headers.Add("User-Agent", HttpUserAgent);
            if (!string.IsNullOrEmpty(this._apiKey))
            {
                httpRequestMessage.Headers.Add("Authorization", $"Bearer {this._apiKey}");
            }

            using var response = await this._httpClient.SendAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);
            response.EnsureSuccessStatusCode();

            var body = await response.Content.ReadAsStringAsync().ConfigureAwait(false);

            List<TextCompletionResponse>? completionResponse = JsonSerializer.Deserialize<List<TextCompletionResponse>>(body);

            if (completionResponse is null)
            {
                throw new AIException(AIException.ErrorCodes.InvalidResponseContent, "Unexpected response from model")
                {
                    Data = { { "ResponseData", body } },
                };
            }

            return completionResponse.ConvertAll(c => new TextCompletionStreamingResult(c));
        }
        catch (Exception e) when (e is not AIException && !e.IsCriticalException())
        {
            throw new AIException(
                AIException.ErrorCodes.UnknownError,
                $"Something went wrong: {e.Message}", e);
        }
    }

    /// <summary>
    /// Retrieves the request URI based on the provided endpoint and model information.
    /// </summary>
    /// <returns>
    /// A <see cref="Uri"/> object representing the request URI.
    /// </returns>
    private Uri GetRequestUri()
    {
        var baseUrl = HuggingFaceApiEndpoint;

        if (!string.IsNullOrEmpty(this._endpoint))
        {
            baseUrl = this._endpoint;
        }
        else if (this._httpClient.BaseAddress?.AbsoluteUri != null)
        {
            baseUrl = this._httpClient.BaseAddress!.AbsoluteUri;
        }

        return new Uri($"{baseUrl!.TrimEnd('/')}/{this._model}");
    }

    #endregion
}
