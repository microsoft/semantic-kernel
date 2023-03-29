// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.HuggingFace.HttpSchema;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.AI.HuggingFace.Services;

/// <summary>
/// HuggingFace text completion service.
/// </summary>
public sealed class HuggingFaceTextCompletion : ITextCompletionClient, IDisposable
{
    private const string HttpUserAgent = "Microsoft Semantic Kernel";
    private const string HuggingFaceApiBaseUri = "https://api-inference.huggingface.co";
    private const string CompletionRemoteApiEndpoint = "/models";
    private const string CompletionLocalApiEndpoint = "/completions";

    private readonly string _completionEndpoint;
    private readonly string _model;
    private readonly HttpClient _httpClient;
    private readonly HttpClientHandler? _httpClientHandler;

    /// <summary>
    /// Initializes a new instance of the <see cref="HuggingFaceTextCompletion"/> class.
    /// </summary>
    /// <param name="baseUri">Base URI for service API call.</param>
    /// <param name="model">Model to use for service API call.</param>
    /// <param name="httpClientHandler">Instance of <see cref="HttpClientHandler"/> to setup specific scenarios.</param>
    public HuggingFaceTextCompletion(Uri baseUri, string model, HttpClientHandler httpClientHandler)
    {
        Verify.NotNull(baseUri, "Base URI cannot be null.");
        Verify.NotEmpty(model, "Model cannot be empty.");

        this._model = model;

        this._httpClient = new(httpClientHandler);

        this._httpClient.BaseAddress = baseUri;
        this._httpClient.DefaultRequestHeaders.Add("User-Agent", HttpUserAgent);

        this._completionEndpoint = CompletionLocalApiEndpoint;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="HuggingFaceTextCompletion"/> class.
    /// Using default <see cref="HttpClientHandler"/> implementation.
    /// </summary>
    /// <param name="baseUri">Base URI for service API call.</param>
    /// <param name="model">Model to use for service API call.</param>
    public HuggingFaceTextCompletion(Uri baseUri, string model)
    {
        Verify.NotNull(baseUri, "Base URI cannot be null.");
        Verify.NotEmpty(model, "Model cannot be empty.");

        this._model = model;

        this._httpClientHandler = new() { CheckCertificateRevocationList = true };
        this._httpClient = new(this._httpClientHandler);

        this._httpClient.BaseAddress = baseUri;
        this._httpClient.DefaultRequestHeaders.Add("User-Agent", HttpUserAgent);

        this._completionEndpoint = CompletionLocalApiEndpoint;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="HuggingFaceTextCompletion"/> class.
    /// Using HuggingFace API for service call, see https://huggingface.co/docs/api-inference/index.
    /// </summary>
    /// <param name="apiKey">HuggingFace API key, see https://huggingface.co/docs/api-inference/quicktour#running-inference-with-api-requests.</param>
    /// <param name="model">Model to use for service API call.</param>
    /// <param name="httpClientHandler">Instance of <see cref="HttpClientHandler"/> to setup specific scenarios.</param>
    public HuggingFaceTextCompletion(string apiKey, string model, HttpClientHandler httpClientHandler)
        : this(new Uri(HuggingFaceApiBaseUri), model, httpClientHandler)
    {
        Verify.NotEmpty(apiKey, "HuggingFace API key cannot be empty.");

        this._httpClient.DefaultRequestHeaders.Add("Authorization", $"Bearer {apiKey}");

        this._completionEndpoint = CompletionRemoteApiEndpoint;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="HuggingFaceTextCompletion"/> class.
    /// Using HuggingFace API for service call, see https://huggingface.co/docs/api-inference/index.
    /// Using default <see cref="HttpClientHandler"/> implementation.
    /// </summary>
    /// <param name="apiKey">HuggingFace API key, see https://huggingface.co/docs/api-inference/quicktour#running-inference-with-api-requests.</param>
    /// <param name="model">Model to use for service API call.</param>
    public HuggingFaceTextCompletion(string apiKey, string model)
        : this(new Uri(HuggingFaceApiBaseUri), model)
    {
        Verify.NotEmpty(apiKey, "HuggingFace API key cannot be empty.");

        this._httpClient.DefaultRequestHeaders.Add("Authorization", $"Bearer {apiKey}");

        this._completionEndpoint = CompletionRemoteApiEndpoint;
    }

    /// <inheritdoc/>
    public async Task<string> CompleteAsync(string text, CompleteRequestSettings requestSettings)
    {
        return await this.ExecuteCompleteRequestAsync(text);
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        this._httpClient.Dispose();
        this._httpClientHandler?.Dispose();
    }

    #region private ================================================================================

    /// <summary>
    /// Performs HTTP request to given base URI for text completion.
    /// </summary>
    /// <param name="text">Text to complete.</param>
    /// <returns>Completed text.</returns>
    /// <exception cref="AIException">Exception when backend didn't respond with completed text.</exception>
    private async Task<string> ExecuteCompleteRequestAsync(string text)
    {
        try
        {
            var completionRequest = new CompletionRequest
            {
                Input = text
            };

            using var httpRequestMessage = new HttpRequestMessage()
            {
                Method = HttpMethod.Post,
                RequestUri = new Uri($"{this._completionEndpoint}/{this._model}", UriKind.Relative),
                Content = new StringContent(JsonSerializer.Serialize(completionRequest))
            };

            var response = await this._httpClient.SendAsync(httpRequestMessage).ConfigureAwait(false);
            var body = await response.Content.ReadAsStringAsync().ConfigureAwait(false);

            var completionResponse = JsonSerializer.Deserialize<List<CompletionResponse>>(body);

            return completionResponse.First().Text!;
        }
        catch (Exception e) when (e is not AIException)
        {
            throw new AIException(
                AIException.ErrorCodes.UnknownError,
                $"Something went wrong: {e.Message}", e);
        }
    }

    #endregion
}
