// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.Inference;
using Azure.Core;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AzureAIInference.Core;

namespace Microsoft.SemanticKernel.Connectors.AzureAIInference;

/// <summary>
/// Chat completion service for Azure AI Inference.
/// </summary>
[Obsolete("Dedicated AzureAIInferenceChatCompletionService is deprecated. Use OllamaApiClient.AsChatCompletionService() instead.")]
public sealed class AzureAIInferenceChatCompletionService : IChatCompletionService
{
    private readonly ChatClientCore _core;
    private readonly IChatCompletionService _chatService;

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureAIInferenceChatCompletionService"/> class.
    /// </summary>
    /// <param name="modelId">Target Model Id for endpoints supporting more than one model</param>
    /// <param name="apiKey">API Key</param>
    /// <param name="endpoint">Endpoint / Target URI</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureAIInferenceChatCompletionService(
            string modelId,
            string? apiKey = null,
            Uri? endpoint = null,
            HttpClient? httpClient = null,
            ILoggerFactory? loggerFactory = null)
    {
        var logger = loggerFactory?.CreateLogger(typeof(AzureAIInferenceChatCompletionService));
        this._core = new(
            modelId,
            apiKey,
            endpoint,
            httpClient,
            logger);

        var builder = new ChatClientBuilder()
            .UseFunctionInvocation(config =>
                config.MaximumIterationsPerRequest = MaxInflightAutoInvokes);

        if (logger is not null)
        {
            builder = builder.UseLogging(logger);
        }

        this._chatService = builder
            .Use(this._core.Client.AsChatClient(modelId))
            .AsChatCompletionService();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureAIInferenceChatCompletionService"/> class.
    /// </summary>
    /// <param name="modelId">Target Model Id for endpoints supporting more than one model</param>
    /// <param name="credential">Token credential, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="endpoint">Endpoint / Target URI</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureAIInferenceChatCompletionService(
            string? modelId,
            TokenCredential credential,
            Uri? endpoint = null,
            HttpClient? httpClient = null,
            ILoggerFactory? loggerFactory = null)
    {
        var logger = loggerFactory?.CreateLogger(typeof(AzureAIInferenceChatCompletionService));
        this._core = new(
            modelId,
            credential,
            endpoint,
            httpClient,
            logger);

        var builder = new ChatClientBuilder()
           .UseFunctionInvocation(config =>
               config.MaximumIterationsPerRequest = MaxInflightAutoInvokes);

        if (logger is not null)
        {
            builder = builder.UseLogging(logger);
        }

        this._chatService = builder
            .Use(this._core.Client.AsChatClient(modelId))
            .AsChatCompletionService();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureAIInferenceChatCompletionService"/> class providing your own ChatCompletionsClient instance.
    /// </summary>
    /// <param name="modelId">Target Model Id for endpoints supporting more than one model</param>
    /// <param name="chatClient">Breaking glass <see cref="ChatCompletionsClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureAIInferenceChatCompletionService(
        string? modelId,
        ChatCompletionsClient chatClient,
        ILoggerFactory? loggerFactory = null)
    {
        var logger = loggerFactory?.CreateLogger(typeof(AzureAIInferenceChatCompletionService));
        this._core = new(
            modelId,
            chatClient,
            logger);

        var builder = new ChatClientBuilder()
         .UseFunctionInvocation(config =>
             config.MaximumIterationsPerRequest = MaxInflightAutoInvokes);

        if (logger is not null)
        {
            builder = builder.UseLogging(logger);
        }

        this._chatService = builder
            .Use(this._core.Client.AsChatClient(modelId))
            .AsChatCompletionService();
    }

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._core.Attributes;

    /// <inheritdoc/>
    public Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        => this._chatService.GetChatMessageContentsAsync(chatHistory, executionSettings, kernel, cancellationToken);

    /// <inheritdoc/>
    public IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        => this._chatService.GetStreamingChatMessageContentsAsync(chatHistory, executionSettings, kernel, cancellationToken);

    #region Private

    private const int MaxInflightAutoInvokes = 128;

    #endregion
}
