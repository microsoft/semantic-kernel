// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Azure;
using Azure.AI.OpenAI;
using Azure.Core.Pipeline;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI.ImageGeneration;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ImageGeneration;

/// <summary>
/// Azure OpenAI Image generation
/// <see herf="https://learn.microsoft.com/en-us/azure/cognitive-services/openai/reference#image-generation" />
/// </summary>
[Experimental("SKEXP0012")]
public sealed class AzureOpenAIImageGeneration : IImageGeneration
{
    private readonly OpenAIClient _client;
    private readonly ILogger _logger;

    /// <summary>
    /// Create a new instance of Azure OpenAI image generation service
    /// </summary>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The ILoggerFactory used to create a logger for logging. If null, no logging will be performed.</param>
    /// <param name="maxRetryCount"> Maximum number of attempts to retrieve the image generation operation result.</param>
    /// <param name="apiVersion">Azure OpenAI Endpoint ApiVersion</param>
    public AzureOpenAIImageGeneration(
        string? endpoint,
        string modelId,
        string apiKey,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null,
        int? maxRetryCount = null,
        string? apiVersion = null)
    {
        Verify.NotNullOrWhiteSpace(apiKey);

        if (!string.IsNullOrEmpty(modelId))
        {
            throw new NotSupportedException($"Specifying a model ID, such as Dall-E-3, is not supported yet. Please provide an empty '{nameof(modelId)}' to use Dall-E-2.");
        }

        if (httpClient?.BaseAddress == null && string.IsNullOrEmpty(endpoint))
        {
            throw new ArgumentException($"The {nameof(httpClient)}.{nameof(HttpClient.BaseAddress)} and {nameof(endpoint)} are both null or empty. Please ensure at least one is provided.");
        }

        this._logger = loggerFactory?.CreateLogger(typeof(AzureOpenAIImageGeneration)) ?? NullLogger.Instance;

        endpoint = !string.IsNullOrEmpty(endpoint) ? endpoint! : httpClient!.BaseAddress!.AbsoluteUri;

        this._client = new(new Uri(endpoint),
            new AzureKeyCredential(apiKey),
            GetClientOptions(httpClient, maxRetryCount, apiVersion));
    }

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes { get; } = new Dictionary<string, object?>();

    /// <inheritdoc/>
    public async Task<string> GenerateImageAsync(
        string description,
        int width,
        int height,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(description);
        if (width != height)
        {
            throw new ArgumentOutOfRangeException("width,height", $"{width}x{height}",
                "OpenAI can generate only square images");
        }

        var size = ImageSize.Size256x256;
        switch (width)
        {
            case 256:
                size = ImageSize.Size256x256;
                break;
            case 512:
                size = ImageSize.Size512x512;
                break;
            case 1024:
                size = ImageSize.Size1024x1024;
                break;
            default:
                throw new ArgumentOutOfRangeException(nameof(width),
                    "OpenAI can generate only square images of size 256x256, 512x512, or 1024x1024");
        }

        Response<ImageGenerations> imageGenerations;
        try
        {
            imageGenerations = await this._client.GetImageGenerationsAsync(
                new ImageGenerationOptions
                {
                    Prompt = description,
                    Size = size,
                }, cancellationToken).ConfigureAwait(false);
        }
        catch (RequestFailedException e) when (e.Status == 404)
        {
            this._logger.LogError("Image generation failed with status code 404. This error can occur also when attempting to use Dall-E-3 which is still not supported");
            throw;
        }

        if (!imageGenerations.HasValue)
        {
            throw new KernelException("The response does not contain an image result");
        }

        if (imageGenerations.Value.Data.Count == 0)
        {
            throw new KernelException("The response does not contain any image");
        }

        return imageGenerations.Value.Data[0].Url.AbsoluteUri;
    }

    private static OpenAIClientOptions GetClientOptions(HttpClient? httpClient, int? maxRetryCount, string? apiVersion)
    {
        OpenAIClientOptions.ServiceVersion version;
        switch (apiVersion)
        {
            case "2022-12-01":
                version = OpenAIClientOptions.ServiceVersion.V2022_12_01;
                break;
            case "2023-05-15":
                version = OpenAIClientOptions.ServiceVersion.V2023_05_15;
                break;
            case "2023-06-01-preview":
                version = OpenAIClientOptions.ServiceVersion.V2023_06_01_Preview;
                break;
            case "2023-07-01-preview":
                version = OpenAIClientOptions.ServiceVersion.V2023_07_01_Preview;
                break;
            case "2023-08-01-preview":
                version = OpenAIClientOptions.ServiceVersion.V2023_08_01_Preview;
                break;
            case "2023-09-01-preview":
                version = OpenAIClientOptions.ServiceVersion.V2023_09_01_Preview;
                break;
            default:
                version = OpenAIClientOptions.ServiceVersion.V2023_09_01_Preview;
                break;
        }

        maxRetryCount ??= 5;
        var options = new OpenAIClientOptions(version)
        {
            RetryPolicy = new RetryPolicy(maxRetries: Math.Max(0, maxRetryCount.Value)),
            Diagnostics = { ApplicationId = HttpHeaderValues.UserAgent }
        };

        if (httpClient != null)
        {
            options.Transport = new HttpClientTransport(httpClient);
        }

        return options;
    }
}
