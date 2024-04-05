// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Anthropic.Core;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.Anthropic;

/// <summary>
/// Represents a chat completion service using Google AI Claude API.
/// </summary>
public sealed class ClaudeChatCompletionService : IChatCompletionService
{
    private readonly Dictionary<string, object?> _attributesInternal = new();
    private readonly ClaudeChatCompletionClient _chatCompletionClient;

    /// <summary>
    /// Initializes a new instance of the <see cref="ClaudeChatCompletionService"/> class.
    /// </summary>
    /// <param name="modelId">The Claude model for the chat completion service.</param>
    /// <param name="apiKey">The API key for authentication.</param>
    /// <param name="httpClient">Optional HTTP client to be used for communication with the Claude API.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public ClaudeChatCompletionService(
        string modelId,
        string apiKey,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        this._chatCompletionClient = new ClaudeChatCompletionClient(
#pragma warning disable CA2000
            httpClient: HttpClientProvider.GetHttpClient(httpClient),
#pragma warning restore CA2000
            modelId: modelId,
            apiKey: apiKey,
            logger: loggerFactory?.CreateLogger(typeof(ClaudeChatCompletionService)));
        this._attributesInternal.Add(AIServiceExtensions.ModelIdKey, modelId);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ClaudeChatCompletionService"/> class.
    /// </summary>
    /// <param name="modelId">The Claude model for the chat completion service.</param>
    /// <param name="endpoint">Endpoint for the chat completion model</param>
    /// <param name="requestHandler">A custom request handler to be used for sending HTTP requests</param>
    /// <param name="httpClient">Optional HTTP client to be used for communication with the Claude API.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public ClaudeChatCompletionService(
        string modelId,
        Uri endpoint,
        Func<HttpRequestMessage, Task>? requestHandler,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNull(endpoint);

        this._chatCompletionClient = new ClaudeChatCompletionClient(
#pragma warning disable CA2000
            httpClient: HttpClientProvider.GetHttpClient(httpClient),
#pragma warning restore CA2000
            modelId: modelId,
            endpoint: endpoint,
            requestHandler: requestHandler,
            logger: loggerFactory?.CreateLogger(typeof(ClaudeChatCompletionService)));
        this._attributesInternal.Add(AIServiceExtensions.ModelIdKey, modelId);
    }

    /// <inheritdoc />
    public IReadOnlyDictionary<string, object?> Attributes => this._attributesInternal;

    /// <inheritdoc />
    public Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        return this._chatCompletionClient.GenerateChatMessageAsync(chatHistory, executionSettings, kernel, cancellationToken);
    }

    /// <inheritdoc />
    public IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        return this._chatCompletionClient.StreamGenerateChatMessageAsync(chatHistory, executionSettings, kernel, cancellationToken);
    }
}
