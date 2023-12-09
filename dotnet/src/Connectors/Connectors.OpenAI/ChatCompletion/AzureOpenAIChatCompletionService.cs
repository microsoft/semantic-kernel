// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.TextGeneration;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Azure OpenAI chat completion service.
/// </summary>
public sealed class AzureOpenAIChatCompletionService : IChatCompletionService, ITextGenerationService
{
    /// <summary>Core implementation shared by Azure OpenAI clients.</summary>
    private readonly AzureOpenAIClientCore _core;

    /// <summary>
    /// Create an instance of the <see cref="AzureOpenAIChatCompletionService"/> connector with API key auth.
    /// </summary>
    /// <param name="serviceConfig">Service configuration <see cref="OpenAIServiceConfig"/></param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureOpenAIChatCompletionService(
        OpenAIServiceConfig serviceConfig,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(serviceConfig.DeploymentName);
        Verify.NotNullOrWhiteSpace(serviceConfig.Endpoint);
        Verify.NotNullOrWhiteSpace(serviceConfig.ApiKey);

        this._core = new(serviceConfig.DeploymentName, serviceConfig.Endpoint, serviceConfig.ApiKey, httpClient, loggerFactory?.CreateLogger(typeof(AzureOpenAIChatCompletionService)));

        this._core.SetAttributes(serviceConfig);
    }

    /// <summary>
    /// Create an instance of the <see cref="AzureOpenAIChatCompletionService"/> connector with AAD auth.
    /// </summary>
    /// <param name="serviceConfig">Service configuration <see cref="OpenAIServiceConfig"/></param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureOpenAIChatCompletionService(
        OpenAIServiceConfig serviceConfig,
        TokenCredential credentials,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(serviceConfig.DeploymentName);
        Verify.NotNullOrWhiteSpace(serviceConfig.Endpoint);

        this._core = new(serviceConfig.DeploymentName, serviceConfig.Endpoint, credentials, httpClient, loggerFactory?.CreateLogger(typeof(AzureOpenAIChatCompletionService)));

        this._core.SetAttributes(serviceConfig);
    }

    /// <summary>
    /// Creates a new <see cref="AzureOpenAIChatCompletionService"/> client instance using the specified <see cref="OpenAIClient"/>.
    /// </summary>
    /// <param name="serviceConfig">Service configuration <see cref="OpenAIServiceConfig"/></param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/>.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureOpenAIChatCompletionService(
        OpenAIServiceConfig serviceConfig,
        OpenAIClient openAIClient,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(serviceConfig.DeploymentName);

        this._core = new(serviceConfig.DeploymentName, openAIClient, loggerFactory?.CreateLogger(typeof(AzureOpenAIChatCompletionService)));

        this._core.SetAttributes(serviceConfig);
    }

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._core.Attributes;

    /// <inheritdoc/>
    public Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        => this._core.GetChatMessageContentsAsync(chatHistory, executionSettings, kernel, cancellationToken);

    /// <inheritdoc/>
    public IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        => this._core.GetStreamingChatMessageContentsAsync(chatHistory, executionSettings, kernel, cancellationToken);

    /// <inheritdoc/>
    public Task<IReadOnlyList<TextContent>> GetTextContentsAsync(string prompt, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        => this._core.GetChatAsTextContentsAsync(prompt, executionSettings, kernel, cancellationToken);

    /// <inheritdoc/>
    public IAsyncEnumerable<StreamingTextContent> GetStreamingTextContentsAsync(string prompt, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        => this._core.GetChatAsTextStreamingContentsAsync(prompt, executionSettings, kernel, cancellationToken);
}
