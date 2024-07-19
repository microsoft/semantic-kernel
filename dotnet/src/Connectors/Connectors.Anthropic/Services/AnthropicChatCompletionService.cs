// Copyright (c) Microsoft. All rights reserved.

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
/// Represents a chat completion service using Anthropic API.
/// </summary>
public sealed class AnthropicChatCompletionService : IChatCompletionService
{
    private readonly Dictionary<string, object?> _attributesInternal = new();
    private readonly AnthropicClient _client;

    /// <summary>
    /// Initializes a new instance of the <see cref="AnthropicChatCompletionService"/> class.
    /// </summary>
    /// <param name="options">Options for the anthropic client</param>
    /// <param name="httpClient">Optional HTTP client to be used for communication with the Claude API.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public AnthropicChatCompletionService(
        ClientOptions options,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(options);
        Verify.NotNullOrWhiteSpace(options.ModelId);

        this._client = new AnthropicClient(
            httpClient: HttpClientProvider.GetHttpClient(httpClient),
            options: options,
            logger: loggerFactory?.CreateLogger(typeof(AnthropicChatCompletionService)));
        this._attributesInternal.Add(AIServiceExtensions.ModelIdKey, options.ModelId);
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
