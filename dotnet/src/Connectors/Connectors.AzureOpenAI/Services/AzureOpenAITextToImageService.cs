// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TextToImage;

namespace Microsoft.SemanticKernel.Connectors.AzureOpenAI;

/// <summary>
/// Azure OpenAI text to image service.
/// </summary>
[Experimental("SKEXP0010")]
public class AzureOpenAITextToImageService : ITextToImageService
{
    private readonly AzureClientCore _client;
    private readonly string? _modelId;

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._client.Attributes;

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureOpenAITextToImageService"/> class.
    /// </summary>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="modelId">Azure OpenAI model id, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <param name="apiVersion">Azure OpenAI service API version, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    public AzureOpenAITextToImageService(
        string deploymentName,
        string endpoint,
        string apiKey,
        string? modelId,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null,
        string? apiVersion = null
    )
    {
        Verify.NotNullOrWhiteSpace(apiKey);

        var connectorEndpoint = !string.IsNullOrWhiteSpace(endpoint)
            ? endpoint!
            : httpClient?.BaseAddress?.AbsoluteUri;
        if (connectorEndpoint is null)
        {
            throw new ArgumentException(
                $"The {nameof(httpClient)}.{nameof(HttpClient.BaseAddress)} and {nameof(endpoint)} are both null or empty. Please ensure at least one is provided."
            );
        }

        var options = AzureClientCore.GetAzureOpenAIClientOptions(httpClient, apiVersion); // DALL-E 3 is supported in the latest API releases - https://learn.microsoft.com/en-us/azure/ai-services/openai/reference#image-generation

        var azureOpenAIClient = new AzureOpenAIClient(
            new Uri(connectorEndpoint),
            new ApiKeyCredential(apiKey),
            options
        );

        this._client = new(
            deploymentName,
            azureOpenAIClient,
            loggerFactory?.CreateLogger(this.GetType())
        );

        this._modelId = modelId;
        if (modelId is not null)
        {
            this._client.AddAttribute(AIServiceExtensions.ModelIdKey, modelId);
        }
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureOpenAITextToImageService"/> class.
    /// </summary>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credential">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="modelId">Azure OpenAI model id, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <param name="apiVersion">Azure OpenAI service API version, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    public AzureOpenAITextToImageService(
        string deploymentName,
        string endpoint,
        TokenCredential credential,
        string? modelId,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null,
        string? apiVersion = null
    )
    {
        Verify.NotNull(credential);

        var connectorEndpoint =
            (
                !string.IsNullOrWhiteSpace(endpoint)
                    ? endpoint!
                    : httpClient?.BaseAddress?.AbsoluteUri
            )
            ?? throw new ArgumentException(
                $"The {nameof(httpClient)}.{nameof(HttpClient.BaseAddress)} and {nameof(endpoint)} are both null or empty. Please ensure at least one is provided."
            );

        var options = AzureClientCore.GetAzureOpenAIClientOptions(httpClient, apiVersion); // DALL-E 3 is supported in the latest API releases - https://learn.microsoft.com/en-us/azure/ai-services/openai/reference#image-generation

        var azureOpenAIClient = new AzureOpenAIClient(
            new Uri(connectorEndpoint),
            credential,
            options
        );

        this._client = new(
            deploymentName,
            azureOpenAIClient,
            loggerFactory?.CreateLogger(this.GetType())
        );

        this._modelId = modelId;
        if (modelId is not null)
        {
            this._client.AddAttribute(AIServiceExtensions.ModelIdKey, modelId);
        }
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureOpenAITextToImageService"/> class.
    /// </summary>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="azureOpenAIClient">Custom <see cref="AzureOpenAIClient"/>.</param>
    /// <param name="modelId">Azure OpenAI model id, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureOpenAITextToImageService(
        string deploymentName,
        AzureOpenAIClient azureOpenAIClient,
        string? modelId,
        ILoggerFactory? loggerFactory = null
    )
    {
        Verify.NotNull(azureOpenAIClient);

        this._client = new(
            deploymentName,
            azureOpenAIClient,
            loggerFactory?.CreateLogger(this.GetType())
        );

        this._modelId = modelId;
        if (modelId is not null)
        {
            this._client.AddAttribute(AIServiceExtensions.ModelIdKey, modelId);
        }
    }

    /// <inheritdoc/>
    public Task<IReadOnlyList<ImageContent>> GetImageContentsAsync(
        TextContent input,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default
    ) =>
        this._client.GetImageContentsAsync(
            this._modelId ?? this._client.DeploymentName, // Use ModelId if available, otherwise fallback to DeploymentName
            input,
            executionSettings,
            kernel,
            cancellationToken
        );

    /// <inheritdoc/>
    public Task<IReadOnlyList<ImageContent>> GenerateImagesAsync(
        TextContent input,
        int imageCount,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default
    ) =>
        this._client.GenerateImagesAsync(
            this._modelId ?? this._client.DeploymentName,
            input,
            imageCount,
            executionSettings,
            kernel,
            cancellationToken
        );

    /// <inheritdoc/>
    public Task<IReadOnlyList<ImageContent>> GenerateEditImageAsync(
        Stream image,
        string prompt,
        Stream? mask = null,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default
    )
    {
        // Determine file names based on stream type or use defaults
        var imageFileName = GetFileNameFromStream(image, "image.png");
        var maskFileName = mask is not null ? GetFileNameFromStream(mask, "mask.png") : null;

        return this._client.GenerateEditImageAsync(
            this._modelId ?? this._client.DeploymentName,
            image,
            imageFileName,
            prompt,
            mask,
            maskFileName,
            executionSettings,
            kernel,
            cancellationToken
        );
    }

    /// <summary>
    /// Generates an edited image based on file paths and a prompt.
    /// </summary>
    /// <param name="imageFilePath">Path to the image file to edit</param>
    /// <param name="prompt">Text prompt describing the desired edits</param>
    /// <param name="maskFilePath">Optional path to mask file indicating areas to edit</param>
    /// <param name="executionSettings">Execution settings for the image edit</param>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>Generated image contents</returns>
    public async Task<IReadOnlyList<ImageContent>> GenerateEditImageAsync(
        string imageFilePath,
        string prompt,
        string? maskFilePath = null,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default
    )
    {
        using var imageStream = File.OpenRead(imageFilePath);

        if (!string.IsNullOrEmpty(maskFilePath))
        {
            using var maskStream = File.OpenRead(maskFilePath);
            return await this.GenerateEditImageAsync(
                    imageStream,
                    prompt,
                    maskStream,
                    executionSettings,
                    kernel,
                    cancellationToken
                )
                .ConfigureAwait(false);
        }

        return await this.GenerateEditImageAsync(
                imageStream,
                prompt,
                null,
                executionSettings,
                kernel,
                cancellationToken
            )
            .ConfigureAwait(false);
    }

    private static string GetFileNameFromStream(Stream stream, string defaultName)
    {
        if (stream is FileStream fileStream)
        {
            return Path.GetFileName(fileStream.Name);
        }
        return defaultName;
    }
}
