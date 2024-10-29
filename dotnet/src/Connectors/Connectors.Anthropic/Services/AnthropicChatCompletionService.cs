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

namespace Microsoft.SemanticKernel.Connectors.Anthropic;

/// <summary>
/// Represents a chat completion service using Anthropic API.
/// </summary>
public sealed class AnthropicChatCompletionService : IChatCompletionService
{
    private readonly AnthropicClient _client;

    /// <inheritdoc />
    public IReadOnlyDictionary<string, object?> Attributes => this._client.Attributes;

    /// <summary>
    /// Initializes a new instance of the <see cref="AnthropicChatCompletionService"/> class.
    /// </summary>
    /// <param name="modelId">Model identifier.</param>
    /// <param name="apiKey">API key.</param>
    /// <param name="options">Options for the anthropic client</param>
    /// <param name="httpClient">Optional HTTP client to be used for communication with the Claude API.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public AnthropicChatCompletionService(
        string modelId,
        string apiKey,
        AnthropicClientOptions? options = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        this._client = new AnthropicClient(
            modelId: modelId,
            apiKey: apiKey,
            options: options ?? new AnthropicClientOptions(),
            httpClient: HttpClientProvider.GetHttpClient(httpClient),
            logger: loggerFactory?.CreateLogger(typeof(AnthropicChatCompletionService)));
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AnthropicChatCompletionService"/> class.
    /// </summary>
    /// <param name="modelId">Model identifier.</param>
    /// <param name="bearerTokenProvider">Bearer token provider.</param>
    /// <param name="options">Options for the anthropic client</param>
    /// <param name="endpoint">Claude API endpoint.</param>
    /// <param name="httpClient">Optional HTTP client to be used for communication with the Claude API.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public AnthropicChatCompletionService(
        string modelId,
        Func<ValueTask<string>> bearerTokenProvider,
        ClientOptions options,
        Uri? endpoint = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        this._client = new AnthropicClient(
            modelId: modelId,
            bearerTokenProvider: bearerTokenProvider,
            options: options,
            endpoint: endpoint,
            httpClient: HttpClientProvider.GetHttpClient(httpClient),
            logger: loggerFactory?.CreateLogger(typeof(AnthropicChatCompletionService)));
    }

    /// <inheritdoc />
    public Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        return this._client.GenerateChatMessageAsync(chatHistory, executionSettings, kernel, cancellationToken);
    }

    /// <inheritdoc />
    public IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        return this._client.StreamGenerateChatMessageAsync(chatHistory, executionSettings, kernel, cancellationToken);
    }
}
