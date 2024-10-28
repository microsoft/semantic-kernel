// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.TextCompletion;

/// <summary>
/// HuggingFace text completion service.
/// </summary>
public sealed class HuggingFaceTextCompletion : ITextCompletion, IDisposable
{
    private const string HttpUserAgent = "Microsoft-Semantic-Kernel";
    private const string HuggingFaceApiEndpoint = "https://api-inference.huggingface.co/models";

    private readonly string _model;
    private readonly Uri _endpoint;
    private readonly HttpClient _httpClient;
    private readonly HttpClientHandler? _httpClientHandler;

    /// <summary>
    /// Initializes a new instance of the <see cref="HuggingFaceTextCompletion"/> class.
    /// </summary>
    /// <param name="endpoint">Endpoint for service API call.</param>
    /// <param name="model">Model to use for service API call.</param>
    /// <param name="httpClientHandler">Instance of <see cref="HttpClientHandler"/> to setup specific scenarios.</param>
    public HuggingFaceTextCompletion(Uri endpoint, string model, HttpClientHandler httpClientHandler)
    {
        Verify.NotNull(endpoint);
        Verify.NotNullOrWhiteSpace(model);

        this._endpoint = endpoint;
        this._model = model;

        this._httpClient = new HttpClient(httpClientHandler);

        this._httpClient.DefaultRequestHeaders.Add("User-Agent", HttpUserAgent);
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

        this._endpoint = endpoint;
        this._model = model;

        this._httpClientHandler = new HttpClientHandler { CheckCertificateRevocationList = true };
        this._httpClient = new HttpClient(this._httpClientHandler);

        this._httpClient.DefaultRequestHeaders.Add("User-Agent", HttpUserAgent);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="HuggingFaceTextCompletion"/> class.
    /// Using HuggingFace API for service call, see https://huggingface.co/docs/api-inference/index.
    /// </summary>
    /// <param name="apiKey">HuggingFace API key, see https://huggingface.co/docs/api-inference/quicktour#running-inference-with-api-requests.</param>
    /// <param name="model">Model to use for service API call.</param>
    /// <param name="httpClientHandler">Instance of <see cref="HttpClientHandler"/> to setup specific scenarios.</param>
    /// <param name="endpoint">Endpoint for service API call.</param>
    public HuggingFaceTextCompletion(string apiKey, string model, HttpClientHandler httpClientHandler, string endpoint = HuggingFaceApiEndpoint)
        : this(new Uri(endpoint), model, httpClientHandler)
    {
        Verify.NotNullOrWhiteSpace(apiKey);

        this._httpClient.DefaultRequestHeaders.Add("Authorization", $"Bearer {apiKey}");
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="HuggingFaceTextCompletion"/> class.
    /// Using HuggingFace API for service call, see https://huggingface.co/docs/api-inference/index.
    /// Using default <see cref="HttpClientHandler"/> implementation.
    /// </summary>
    /// <param name="apiKey">HuggingFace API key, see https://huggingface.co/docs/api-inference/quicktour#running-inference-with-api-requests.</param>
    /// <param name="model">Model to use for service API call.</param>
    /// <param name="endpoint">Endpoint for service API call.</param>
    public HuggingFaceTextCompletion(string apiKey, string model, string endpoint = HuggingFaceApiEndpoint)
        : this(new Uri(endpoint), model)
    {
        Verify.NotNullOrWhiteSpace(apiKey);

        this._httpClient.DefaultRequestHeaders.Add("Authorization", $"Bearer {apiKey}");
    }

    /// <inheritdoc/>
    public async Task<string> CompleteAsync(string text, JsonObject requestSettings, CancellationToken cancellationToken = default)
    {
        return await this.ExecuteCompleteRequestAsync(text, cancellationToken).ConfigureAwait(false);
    }

    public IAsyncEnumerable<string> CompleteStreamAsync(
        string text,
        JsonObject requestSettings,
        CancellationToken cancellationToken = default)
    {
        return this.ExecuteCompleteRequestAsync(text, cancellationToken).ToAsyncEnumerable();
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        this._httpClient.Dispose();
        this._httpClientHandler?.Dispose();
    }

    #region private ================================================================================

    /// <summary>
    /// Performs HTTP request to given endpoint for text completion.
    /// </summary>
    /// <param name="text">Text to complete.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Completed text.</returns>
    /// <exception cref="AIException">Exception when backend didn't respond with completed text.</exception>
    private async Task<string> ExecuteCompleteRequestAsync(string text, CancellationToken cancellationToken = default)
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
                RequestUri = new Uri($"{this._endpoint}/{this._model}"),
                Content = new StringContent(JsonSerializer.Serialize(completionRequest))
            };

            var response = await this._httpClient.SendAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);
            var body = await response.Content.ReadAsStringAsync().ConfigureAwait(false);

            var completionResponse = JsonSerializer.Deserialize<List<TextCompletionResponse>>(body);

            return completionResponse.First().Text!;
        }
        catch (Exception e) when (e is not AIException && !e.IsCriticalException())
        {
            throw new AIException(
                AIException.ErrorCodes.UnknownError,
                $"Something went wrong: {e.Message}", e);
        }
    }

    #endregion
}
