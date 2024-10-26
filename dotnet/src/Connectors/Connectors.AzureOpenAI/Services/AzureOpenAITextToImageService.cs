// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
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
        string? apiVersion = null)
    {
        Verify.NotNullOrWhiteSpace(apiKey);

        var connectorEndpoint = !string.IsNullOrWhiteSpace(endpoint) ? endpoint! : httpClient?.BaseAddress?.AbsoluteUri;
        if (connectorEndpoint is null)
        {
            throw new ArgumentException($"The {nameof(httpClient)}.{nameof(HttpClient.BaseAddress)} and {nameof(endpoint)} are both null or empty. Please ensure at least one is provided.");
        }

        var options = AzureClientCore.GetAzureOpenAIClientOptions(
            httpClient,
            AzureOpenAIClientOptions.ServiceVersion.V2024_05_01_Preview); // DALL-E 3 is supported in the latest API releases - https://learn.microsoft.com/en-us/azure/ai-services/openai/reference#image-generation

        var azureOpenAIClient = new AzureOpenAIClient(new Uri(connectorEndpoint), apiKey, options);

        var options = AzureClientCore.GetAzureOpenAIClientOptions(httpClient); // DALL-E 3 is supported in the latest API releases - https://learn.microsoft.com/en-us/azure/ai-services/openai/reference#image-generation
        var options = AzureClientCore.GetAzureOpenAIClientOptions(httpClient, apiVersion); // DALL-E 3 is supported in the latest API releases - https://learn.microsoft.com/en-us/azure/ai-services/openai/reference#image-generation

        var azureOpenAIClient = new AzureOpenAIClient(new Uri(connectorEndpoint), new ApiKeyCredential(apiKey), options);

        var options = AzureClientCore.GetAzureOpenAIClientOptions(httpClient); // DALL-E 3 is supported in the latest API releases - https://learn.microsoft.com/en-us/azure/ai-services/openai/reference#image-generation

        var azureOpenAIClient = new AzureOpenAIClient(new Uri(connectorEndpoint), new ApiKeyCredential(apiKey), options);

        var options = AzureClientCore.GetAzureOpenAIClientOptions(httpClient); // DALL-E 3 is supported in the latest API releases - https://learn.microsoft.com/en-us/azure/ai-services/openai/reference#image-generation

        var azureOpenAIClient = new AzureOpenAIClient(new Uri(connectorEndpoint), new ApiKeyCredential(apiKey), options);

        var azureOpenAIClient = new AzureOpenAIClient(new Uri(connectorEndpoint), new ApiKeyCredential(apiKey), options);

        this._client = new(deploymentName, azureOpenAIClient, loggerFactory?.CreateLogger(this.GetType()));

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
        string? apiVersion = null)
    {
        Verify.NotNull(credential);

        var connectorEndpoint = !string.IsNullOrWhiteSpace(endpoint) ? endpoint! : httpClient?.BaseAddress?.AbsoluteUri;
        if (connectorEndpoint is null)
        {
            throw new ArgumentException($"The {nameof(httpClient)}.{nameof(HttpClient.BaseAddress)} and {nameof(endpoint)} are both null or empty. Please ensure at least one is provided.");
        }

        var options = AzureClientCore.GetAzureOpenAIClientOptions(
            httpClient,
            AzureOpenAIClientOptions.ServiceVersion.V2024_05_01_Preview); // DALL-E 3 is supported in the latest API releases - https://learn.microsoft.com/en-us/azure/ai-services/openai/reference#image-generation

        var connectorEndpoint = (!string.IsNullOrWhiteSpace(endpoint) ? endpoint! : httpClient?.BaseAddress?.AbsoluteUri)
            ?? throw new ArgumentException($"The {nameof(httpClient)}.{nameof(HttpClient.BaseAddress)} and {nameof(endpoint)} are both null or empty. Please ensure at least one is provided.");

        var options = AzureClientCore.GetAzureOpenAIClientOptions(httpClient); // DALL-E 3 is supported in the latest API releases - https://learn.microsoft.com/en-us/azure/ai-services/openai/reference#image-generation

        var options = AzureClientCore.GetAzureOpenAIClientOptions(httpClient, apiVersion); // DALL-E 3 is supported in the latest API releases - https://learn.microsoft.com/en-us/azure/ai-services/openai/reference#image-generation

        var azureOpenAIClient = new AzureOpenAIClient(new Uri(connectorEndpoint), credential, options);

        this._client = new(deploymentName, azureOpenAIClient, loggerFactory?.CreateLogger(this.GetType()));

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
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(azureOpenAIClient);

        this._client = new(deploymentName, azureOpenAIClient, loggerFactory?.CreateLogger(this.GetType()));

        if (modelId is not null)
        {
            this._client.AddAttribute(AIServiceExtensions.ModelIdKey, modelId);
        }
    }

    /// <inheritdoc/>
    public Task<string> GenerateImageAsync(string description, int width, int height, Kernel? kernel = null, CancellationToken cancellationToken = default)
        => this._client.GenerateImageAsync(this._client.DeploymentName, description, width, height, cancellationToken);
    public Task<string> GenerateImageAsync(string description, int width, int height, Kernel? kernel = null, CancellationToken cancellationToken = default)
        => this._client.GenerateImageAsync(this._client.DeploymentName, description, width, height, cancellationToken);
    public Task<IReadOnlyList<ImageContent>> GetImageContentsAsync(TextContent input, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        => this._client.GetImageContentsAsync(this._client.DeploymentName, input, executionSettings, kernel, cancellationToken);
    public Task<IReadOnlyList<ImageContent>> GetImageContentsAsync(TextContent input, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        => this._client.GetImageContentsAsync(this._client.DeploymentName, input, executionSettings, kernel, cancellationToken);
    public Task<IReadOnlyList<ImageContent>> GetImageContentsAsync(TextContent input, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        => this._client.GetImageContentsAsync(this._client.DeploymentName, input, executionSettings, kernel, cancellationToken);
}
