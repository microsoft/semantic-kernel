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
[Obsolete("Dedicated AzureAIInferenceChatCompletionService is deprecated. Use Azure.AI.Inference.ChatCompletionsClient.AsChatClient().AsChatCompletionService() instead.")]
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
        this._core = new ChatClientCore(modelId, apiKey, endpoint, httpClient);

        var builder = this._core.Client
            .AsIChatClient(modelId)
            .AsBuilder()
            .UseFunctionInvocation(loggerFactory, f => f.MaximumIterationsPerRequest = MaxInflightAutoInvokes);

        if (loggerFactory is not null)
        {
            builder.UseLogging(loggerFactory);
        }

        this._chatService = builder.Build().AsChatCompletionService();
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
        this._core = new ChatClientCore(modelId, credential, endpoint, httpClient);

        var builder = this._core.Client
            .AsIChatClient(modelId)
            .AsBuilder()
            .UseFunctionInvocation(loggerFactory, f => f.MaximumIterationsPerRequest = MaxInflightAutoInvokes);

        if (loggerFactory is not null)
        {
            builder.UseLogging(loggerFactory);
        }

        this._chatService = builder.Build().AsChatCompletionService();
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
        Verify.NotNull(chatClient);

        this._core = new ChatClientCore(modelId, chatClient);

        var builder = chatClient
            .AsIChatClient(modelId)
            .AsBuilder()
            .UseFunctionInvocation(loggerFactory, f => f.MaximumIterationsPerRequest = MaxInflightAutoInvokes);

        if (loggerFactory is not null)
        {
            builder.UseLogging(loggerFactory);
        }

        this._chatService = builder.Build().AsChatCompletionService();
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
