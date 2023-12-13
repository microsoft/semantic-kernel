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
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.TextToImage;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Azure OpenAI Image generation
/// <see herf="https://learn.microsoft.com/en-us/azure/cognitive-services/openai/reference#image-generation" />
/// </summary>
[Experimental("SKEXP0012")]
public sealed class AzureOpenAITextToImageService : ITextToImageService
{
    private readonly OpenAIClient _client;
    private readonly ILogger _logger;
    private readonly string _deploymentName;
    /// <summary>
    /// Create a new instance of Azure OpenAI image generation service
    /// </summary>
    /// <param name="deploymentName">Deployment name identifier</param>
    /// <param name="endpoint">Azure OpenAI deployment URL</param>
    /// <param name="apiKey">Azure OpenAI API key</param>
    /// <param name="modelId">Model name identifier</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The ILoggerFactory used to create a logger for logging. If null, no logging will be performed.</param>
    /// <param name="apiVersion">Azure OpenAI Endpoint ApiVersion</param>
    public AzureOpenAITextToImageService(
        string deploymentName,
        string endpoint,
        string apiKey,
        string? modelId = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null,
        string? apiVersion = null)
    {
        Verify.NotNullOrWhiteSpace(apiKey);
        Verify.NotNullOrWhiteSpace(deploymentName);

        this._deploymentName = deploymentName;

        this._logger = loggerFactory?.CreateLogger(typeof(AzureOpenAITextToImageService)) ?? NullLogger.Instance;
        if (string.Equals(modelId, "dall-e-2", StringComparison.OrdinalIgnoreCase))
        {
            this._logger.LogWarning($"{nameof(AzureOpenAITextToImageService)} supports only Dall-E-3. .");
            throw new NotSupportedException("Dall-E-2 support was deprecated in Azure Open AI latest SDK. Please use a 'dall-e-3' deployment.");
        }

        var connectorEndpoint = !string.IsNullOrWhiteSpace(endpoint) ? endpoint! : httpClient?.BaseAddress?.AbsoluteUri;
        if (connectorEndpoint is null)
        {
            throw new ArgumentException($"The {nameof(httpClient)}.{nameof(HttpClient.BaseAddress)} and {nameof(endpoint)} are both null or empty. Please ensure at least one is provided.");
        }

        this._client = new(new Uri(connectorEndpoint),
            new AzureKeyCredential(apiKey),
            GetClientOptions(httpClient, apiVersion));
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
        const string SizeErr = "Dall-E 2 can generate only square images of size 256x256, 512x512, or 1024x1024";

        if (width != height)
        {
            throw new ArgumentOutOfRangeException("width,height", $"{width}x{height}", SizeErr);
        }

        var size = width switch
        {
            256 => ImageSize.Size256x256,
            512 => ImageSize.Size512x512,
            1024 => ImageSize.Size1024x1024,
            _ => throw new ArgumentOutOfRangeException(nameof(width), SizeErr)
        };

        Response<ImageGenerations> imageGenerations;
        try
        {
            imageGenerations = await this._client.GetImageGenerationsAsync(
                new ImageGenerationOptions
                {
                    DeploymentName = this._deploymentName,
                    Prompt = description,
                    Size = size,
                }, cancellationToken).ConfigureAwait(false);
        }
        catch (RequestFailedException e) when (e.Status == 404)
        {
            this._logger.LogError("Image generation failed with status code 404. This error can occur also when attempting to use Dall-E-3 which is still not supported");
            throw e.ToHttpOperationException();
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

    private static OpenAIClientOptions GetClientOptions(HttpClient? httpClient, string? apiVersion)
    {
        OpenAIClientOptions.ServiceVersion version = apiVersion switch
        {
            "2022-12-01" => OpenAIClientOptions.ServiceVersion.V2022_12_01,
            "2023-05-15" => OpenAIClientOptions.ServiceVersion.V2023_05_15,
            "2023-06-01-preview" => OpenAIClientOptions.ServiceVersion.V2023_06_01_Preview,
            "2023-07-01-preview" => OpenAIClientOptions.ServiceVersion.V2023_07_01_Preview,
            "2023-08-01-preview" => OpenAIClientOptions.ServiceVersion.V2023_08_01_Preview,
            "2023-12-01-preview" => OpenAIClientOptions.ServiceVersion.V2023_12_01_Preview,
            _ => OpenAIClientOptions.ServiceVersion.V2023_09_01_Preview
        };

        var options = new OpenAIClientOptions(version)
        {
            Diagnostics = { ApplicationId = HttpHeaderValues.UserAgent }
        };

        if (httpClient != null)
        {
            options.Transport = new HttpClientTransport(httpClient);
        }

        return options;
    }
}
