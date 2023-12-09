// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TextGeneration;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Azure OpenAI text generation client.
/// </summary>
public sealed class AzureOpenAITextGenerationService : ITextGenerationService
{
    private readonly AzureOpenAIClientCore _core;

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._core.Attributes;

    /// <summary>
    /// Creates a new <see cref="AzureOpenAITextGenerationService"/> client instance using API Key auth
    /// </summary>
    /// <param name="serviceConfig">Service configuration <see cref="OpenAIServiceConfig"/></param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureOpenAITextGenerationService(
        OpenAIServiceConfig serviceConfig,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(serviceConfig.DeploymentName);
        Verify.NotNullOrWhiteSpace(serviceConfig.Endpoint);
        Verify.NotNullOrWhiteSpace(serviceConfig.ApiKey);

        this._core = new(serviceConfig.DeploymentName, serviceConfig.Endpoint, serviceConfig.ApiKey, httpClient, loggerFactory?.CreateLogger(typeof(AzureOpenAITextGenerationService)));
        this._core.AddAttribute(AIServiceExtensions.ModelIdKey, serviceConfig.ModelId);
    }

    /// <summary>
    /// Creates a new <see cref="AzureOpenAITextGenerationService"/> client instance supporting AAD auth
    /// </summary>
    /// <param name="serviceConfig">Service configuration <see cref="OpenAIServiceConfig"/></param>
    /// <param name="credential">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureOpenAITextGenerationService(
        OpenAIServiceConfig serviceConfig,
        TokenCredential credential,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(serviceConfig.DeploymentName);
        Verify.NotNullOrWhiteSpace(serviceConfig.Endpoint);

        this._core = new(serviceConfig.DeploymentName, serviceConfig.Endpoint, credential, httpClient, loggerFactory?.CreateLogger(typeof(AzureOpenAITextGenerationService)));

        this._core.AddAttribute(AIServiceExtensions.ModelIdKey, serviceConfig.ModelId);
    }

    /// <summary>
    /// Creates a new <see cref="AzureOpenAITextGenerationService"/> client instance using the specified OpenAIClient
    /// </summary>
    /// <param name="serviceConfig">Service configuration <see cref="OpenAIServiceConfig"/></param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/>.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureOpenAITextGenerationService(
        OpenAIServiceConfig serviceConfig,
        OpenAIClient openAIClient,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(serviceConfig.DeploymentName);

        this._core = new(serviceConfig.DeploymentName, openAIClient, loggerFactory?.CreateLogger(typeof(AzureOpenAITextGenerationService)));

        this._core.AddAttribute(AIServiceExtensions.ModelIdKey, serviceConfig.ModelId);
    }

    /// <inheritdoc/>
    public Task<IReadOnlyList<TextContent>> GetTextContentsAsync(string prompt, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
    {
        return this._core.GetTextResultsAsync(prompt, executionSettings, kernel, cancellationToken);
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<StreamingTextContent> GetStreamingTextContentsAsync(string prompt, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
    {
        return this._core.GetStreamingTextContentsAsync(prompt, executionSettings, kernel, cancellationToken);
    }
}
