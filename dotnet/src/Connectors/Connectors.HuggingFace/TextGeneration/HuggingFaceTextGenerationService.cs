// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TextGeneration;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace;

/// <summary>
/// HuggingFace text generation service.
/// </summary>
#pragma warning disable CA1001 // Types that own disposable fields should be disposable. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
public sealed class HuggingFaceTextGenerationService : ITextGenerationService
#pragma warning restore CA1001 // Types that own disposable fields should be disposable. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
{
    private const string HuggingFaceApiEndpoint = "https://api-inference.huggingface.co/models";

    private readonly string _model;
    private readonly string? _endpoint;
    private readonly HttpClient _httpClient;
    private readonly string? _apiKey;
    private readonly Dictionary<string, object?> _attributes = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="HuggingFaceTextGenerationService"/> class.
    /// Using default <see cref="HttpClientHandler"/> implementation.
    /// </summary>
    /// <param name="endpoint">Endpoint for service API call.</param>
    /// <param name="model">Model to use for service API call.</param>
    public HuggingFaceTextGenerationService(Uri endpoint, string model)
    {
        Verify.NotNull(endpoint);
        Verify.NotNullOrWhiteSpace(model);

        this._model = model;
        this._endpoint = endpoint.AbsoluteUri;
        this._attributes.Add(AIServiceExtensions.ModelIdKey, this._model);
        this._attributes.Add(AIServiceExtensions.EndpointKey, this._endpoint);

        this._httpClient = HttpClientProvider.GetHttpClient();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="HuggingFaceTextGenerationService"/> class.
    /// Using HuggingFace API for service call, see https://huggingface.co/docs/api-inference/index.
    /// </summary>
    /// <param name="model">The name of the model to use for text generation.</param>
    /// <param name="apiKey">The API key for accessing the Hugging Face service.</param>
    /// <param name="httpClient">The HTTP client to use for making API requests. If not specified, a default client will be used.</param>
    /// <param name="endpoint">The endpoint URL for the Hugging Face service.
    /// If not specified, the base address of the HTTP client is used. If the base address is not available, a default endpoint will be used.</param>
    public HuggingFaceTextGenerationService(string model, string? apiKey = null, HttpClient? httpClient = null, string? endpoint = null)
    {
        Verify.NotNullOrWhiteSpace(model);

        this._model = model;
        this._apiKey = apiKey;
        this._httpClient = HttpClientProvider.GetHttpClient(httpClient);
        this._endpoint = endpoint;
        this._attributes.Add(AIServiceExtensions.ModelIdKey, this._model);
        this._attributes.Add(AIServiceExtensions.EndpointKey, this._endpoint ?? HuggingFaceApiEndpoint);
    }

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._attributes;

    /// <inheritdoc/>
    public Task<IReadOnlyList<TextContent>> GetTextContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
        => this.InternalGetTextContentsAsync(prompt, cancellationToken);

    /// <inheritdoc/>
    public async IAsyncEnumerable<StreamingTextContent> GetStreamingTextContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        foreach (var textContent in await this.InternalGetTextContentsAsync(prompt, cancellationToken).ConfigureAwait(false))
        {
            yield return new StreamingTextContent(textContent.Text, 0, this.GetModelId(), textContent);
        }
    }

    #region private ================================================================================

    private async Task<IReadOnlyList<TextContent>> InternalGetTextContentsAsync(string text, CancellationToken cancellationToken = default)
    {
        var completionRequest = new TextGenerationRequest
        {
            Input = text
        };

        using var httpRequestMessage = HttpRequest.CreatePostRequest(this.GetRequestUri(), completionRequest);

        httpRequestMessage.Headers.Add("User-Agent", HttpHeaderValues.UserAgent);
        if (!string.IsNullOrEmpty(this._apiKey))
        {
            httpRequestMessage.Headers.Add("Authorization", $"Bearer {this._apiKey}");
        }

        using var response = await this._httpClient.SendWithSuccessCheckAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);

        var body = await response.Content.ReadAsStringWithExceptionMappingAsync().ConfigureAwait(false);

        List<TextGenerationResponse>? completionResponse = JsonSerializer.Deserialize<List<TextGenerationResponse>>(body);

        if (completionResponse is null)
        {
            throw new KernelException("Unexpected response from model")
            {
                Data = { { "ResponseData", body } },
            };
        }

        return completionResponse.ConvertAll(responseContent => new TextContent(responseContent.Text, this.GetModelId(), responseContent));
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
