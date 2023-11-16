// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.ImageGeneration;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.CustomClient;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ImageGeneration;

/// <summary>
/// Azure OpenAI Image generation
/// <see herf="https://learn.microsoft.com/en-us/azure/cognitive-services/openai/reference#image-generation" />
/// </summary>
public class AzureOpenAIImageGeneration : OpenAIClientBase, IImageGeneration
{
    /// <summary>
    /// Image Generation Model DALL-E 2
    /// </summary>
    private const string DALLE2 = "dall-e-2";

    /// <summary>
    /// Image Generation Model DALL-E 3
    /// </summary>
    private const string DALLE3 = "dall-e-3";

    /// <summary>
    /// Azure OpenAI DALL-E-3 Deployment
    /// </summary>
    private readonly string? _deploymentName;

    /// <summary>
    /// Azure OpenAI API key
    /// </summary>
    private readonly string _apiKey;

    /// <summary>
    /// Maximum number of attempts to retrieve the image generation operation result.
    /// </summary>
    private readonly int _maxRetryCount;

    /// <summary>
    /// Azure OpenAI Image Generation Model
    /// </summary>
    private readonly string _model;

    /// <summary>
    /// Azure OpenAI DALL-E 3 Image Generation Options
    /// </summary>
    private readonly DALLE3GenerationOptions? _imageGenerationOptions;

    /// <summary>
    /// Create a new instance of Azure OpenAI DALL-E 2 image generation service
    /// </summary>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The ILoggerFactory used to create a logger for logging. If null, no logging will be performed.</param>
    /// <param name="maxRetryCount"> Maximum number of attempts to retrieve the image generation operation result.</param>
    /// <param name="apiVersion">Azure OpenAI Endpoint ApiVersion</param>
    public AzureOpenAIImageGeneration(string endpoint, string apiKey, HttpClient? httpClient = null, ILoggerFactory? loggerFactory = null, int maxRetryCount = 5, string apiVersion = "2023-08-01-preview") : base(httpClient, loggerFactory)
    {
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(apiKey);
        Verify.StartsWith(endpoint, "https://", "The Azure OpenAI endpoint must start with 'https://'");

        this._apiKey = apiKey;
        this._maxRetryCount = maxRetryCount;
        this._model = DALLE2;
        this.AddAttribute(IAIServiceExtensions.EndpointKey, endpoint);
        this.AddAttribute(IAIServiceExtensions.ApiVersionKey, apiVersion);
    }

    /// <summary>
    /// Create a new instance of Azure OpenAI DALL-E 2 image generation service
    /// </summary>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="loggerFactory">The ILoggerFactory used to create a logger for logging. If null, no logging will be performed.</param>
    /// <param name="maxRetryCount"> Maximum number of attempts to retrieve the image generation operation result.</param>
    /// <param name="apiVersion">Azure OpenAI Endpoint ApiVersion</param>
    public AzureOpenAIImageGeneration(string apiKey, HttpClient httpClient, string? endpoint = null, ILoggerFactory? loggerFactory = null, int maxRetryCount = 5, string apiVersion = "2023-08-01-preview") : base(httpClient, loggerFactory)
    {
        Verify.NotNull(httpClient);
        Verify.NotNullOrWhiteSpace(apiKey);

        if (httpClient.BaseAddress == null && string.IsNullOrEmpty(endpoint))
        {
            throw new SKException("The HttpClient BaseAddress and endpoint are both null or empty. Please ensure at least one is provided.");
        }

        endpoint = !string.IsNullOrEmpty(endpoint) ? endpoint! : httpClient.BaseAddress!.AbsoluteUri;
        Verify.StartsWith(endpoint, "https://", "The Azure OpenAI endpoint must start with 'https://'");

        this._apiKey = apiKey;
        this._maxRetryCount = maxRetryCount;
        this._model = DALLE2;
        this.AddAttribute(IAIServiceExtensions.EndpointKey, endpoint);
        this.AddAttribute(IAIServiceExtensions.ApiVersionKey, apiVersion);
    }

    /// <summary>
    /// Create a new instance of Azure OpenAI DALL-E 3 image generation service
    /// </summary>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="options">DALL-E 3 image generation options</param>
    /// <param name="client">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <param name="apiVersion">Azure OpenAI Endpoint ApiVersion</param>
    public AzureOpenAIImageGeneration(string deploymentName,
        string endpoint,
        string apiKey,
        DALLE3GenerationOptions? options,
        HttpClient? client,
        ILoggerFactory? loggerFactory = null,
        string apiVersion = "2023-12-01-preview") : base(client, loggerFactory)
    {
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(apiKey);
        Verify.StartsWith(endpoint, "https://", "The Azure OpenAI endpoint must start with 'https://'");

        this._deploymentName = deploymentName;
        this._apiKey = apiKey;
        this._imageGenerationOptions = options;
        this._model = DALLE3;
        this.AddAttribute(IAIServiceExtensions.EndpointKey, endpoint);
        this.AddAttribute(IAIServiceExtensions.ApiVersionKey, apiVersion);
    }

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, string> Attributes => this.InternalAttributes;

    /// <inheritdoc/>
    public async Task<string> GenerateImageAsync(string description, int width, int height, CancellationToken cancellationToken = default)
    {
        if (this._model == DALLE2)
        {
            return await this.GenerateImageForDALLE2Async(description, width, height, cancellationToken).ConfigureAwait(false);
        }

        if (this._model == DALLE3)
        {
            return await this.GenerateImageForDALLE3Async(description, width, height, cancellationToken).ConfigureAwait(false);
        }

        throw new SKException($"Azure OpenAI Image Generation Model {this._model} not supported");
    }

    #region DALL-E 3
    private async Task<string> GenerateImageForDALLE3Async(string description, int width, int height, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(description);

        ImageGenerationVerify.DALL3ImageSize(width, height);

        var requestBody = Microsoft.SemanticKernel.Text.Json.Serialize(new ImageGenerationRequest
        {
            Prompt = description,
            Size = $"{width}x{height}",
            Count = 1,
            Quality = this._imageGenerationOptions?.Quality,
            Style = this._imageGenerationOptions?.Style
        });

        var operation = this.GetUri($"openai/deployments/{this._deploymentName}/images/generations");
        var list = await this.ExecuteImageGenerationRequestAsync(operation, requestBody, x => x.Url, cancellationToken).ConfigureAwait(false);
        return list[0];
    }
    #endregion

    #region DALL-E 2
    private async Task<string> GenerateImageForDALLE2Async(string description, int width, int height, CancellationToken cancellationToken = default)
    {
        var operationId = await this.StartImageGenerationAsync(description, width, height, cancellationToken).ConfigureAwait(false);
        var result = await this.GetImageGenerationResultAsync(operationId, cancellationToken).ConfigureAwait(false);

        if (result.Result is null)
        {
            throw new SKException("Azure OpenAI Image Generation null response");
        }

        if (result.Result.Images.Count == 0)
        {
            throw new SKException("Azure OpenAI Image Generation result not found");
        }

        return result.Result.Images.First().Url;
    }

    /// <summary>
    /// Start an image generation task
    /// </summary>
    /// <param name="description">Image description</param>
    /// <param name="width">Image width in pixels</param>
    /// <param name="height">Image height in pixels</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns> The operationId that identifies the original image generation request. </returns>
    private async Task<string> StartImageGenerationAsync(string description, int width, int height, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(description);

        ImageGenerationVerify.DALLE2ImageSize(width, height);

        var requestBody = Microsoft.SemanticKernel.Text.Json.Serialize(new ImageGenerationRequest
        {
            Prompt = description,
            Size = $"{width}x{height}",
            Count = 1
        });

        var uri = this.GetUri("openai/images/generations:submit");

        var result = await this.ExecutePostRequestAsync<AzureOpenAIImageGenerationResponse>(uri, requestBody, cancellationToken).ConfigureAwait(false);

        if (result == null || string.IsNullOrWhiteSpace(result.Id))
        {
            throw new SKException("Response not contains result");
        }

        return result.Id;
    }

    /// <summary>
    /// Retrieve the results of an image generation operation.
    /// </summary>
    /// <param name="operationId">The operationId that identifies the original image generation request.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    private async Task<AzureOpenAIImageGenerationResponse> GetImageGenerationResultAsync(string operationId, CancellationToken cancellationToken = default)
    {
        var operationLocation = this.GetUri("openai/operations/images", operationId);

        var retryCount = 0;

        while (true)
        {
            if (this._maxRetryCount == retryCount)
            {
                throw new SKException("Reached maximum retry attempts");
            }

            using var response = await this.ExecuteRequestAsync(operationLocation, HttpMethod.Get, null, cancellationToken).ConfigureAwait(false);
            var responseJson = await response.Content.ReadAsStringWithExceptionMappingAsync().ConfigureAwait(false);
            var result = this.JsonDeserialize<AzureOpenAIImageGenerationResponse>(responseJson);

            if (result.Status.Equals(AzureOpenAIImageOperationStatus.Succeeded, StringComparison.OrdinalIgnoreCase))
            {
                return result;
            }
            else if (this.IsFailedOrCancelled(result.Status))
            {
                throw new SKException($"Azure OpenAI image generation {result.Status}");
            }

            if (response.Headers.TryGetValues("retry-after", out var afterValues) && long.TryParse(afterValues.FirstOrDefault(), out var after))
            {
                await Task.Delay(TimeSpan.FromSeconds(after), cancellationToken).ConfigureAwait(false);
            }

            // increase retry count
            retryCount++;
        }
    }
    #endregion

    private string GetUri(string operation, params string[] parameters)
    {
        var uri = new Azure.Core.RequestUriBuilder();
        uri.Reset(new Uri(this.GetAttribute(IAIServiceExtensions.EndpointKey)));
        uri.AppendPath(operation, false);
        foreach (var parameter in parameters)
        {
            uri.AppendPath("/" + parameter, false);
        }
        uri.AppendQuery("api-version", this.GetAttribute(IAIServiceExtensions.ApiVersionKey)!);
        return uri.ToString();
    }

    private bool IsFailedOrCancelled(string status)
    {
        return status.Equals(AzureOpenAIImageOperationStatus.Failed, StringComparison.OrdinalIgnoreCase)
            || status.Equals(AzureOpenAIImageOperationStatus.Cancelled, StringComparison.OrdinalIgnoreCase)
            || status.Equals(AzureOpenAIImageOperationStatus.Deleted, StringComparison.OrdinalIgnoreCase);
    }

    /// <summary>Adds headers to use for Azure OpenAI HTTP requests.</summary>
    private protected override void AddRequestHeaders(HttpRequestMessage request)
    {
        request.Headers.Add("api-key", this._apiKey);
    }
}
