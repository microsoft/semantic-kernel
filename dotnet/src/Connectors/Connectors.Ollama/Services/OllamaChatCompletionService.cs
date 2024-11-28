// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Ollama.Core;

namespace Microsoft.SemanticKernel.Connectors.Ollama;

/// <summary>
/// Represents a chat completion service using Ollama Original API.
/// </summary>
[Obsolete("Dedicated OllamaService is deprecated. Use OllamaApiClient.AsChatCompletionService() instead.")]
public sealed class OllamaChatCompletionService : ServiceBase, IChatCompletionService
{
    /// <summary>
    /// Initializes a new instance of the <see cref="OllamaChatCompletionService"/> class.
    /// </summary>
    /// <param name="modelId">The hosted model.</param>
    /// <param name="endpoint">The endpoint including the port where Ollama server is hosted</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public OllamaChatCompletionService(
        string modelId,
        Uri endpoint,
        ILoggerFactory? loggerFactory = null)
        : base(modelId, endpoint, null, loggerFactory)
    {
        Verify.NotNull(endpoint);

        this._chatCompletionService = this._client.AsChatCompletionService();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OllamaChatCompletionService"/> class.
    /// </summary>
    /// <param name="modelId">The hosted model.</param>
    /// <param name="httpClient">HTTP client to be used for communication with the Ollama API.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public OllamaChatCompletionService(
        string modelId,
        HttpClient httpClient,
        ILoggerFactory? loggerFactory = null)
        : base(modelId, null, httpClient, loggerFactory)
    {
        Verify.NotNull(httpClient);
        Verify.NotNull(httpClient.BaseAddress);

        this._chatCompletionService = this._client.AsChatCompletionService();
    }

    /// <inheritdoc />
    public IReadOnlyDictionary<string, object?> Attributes => this._chatCompletionService.Attributes;

    /// <inheritdoc />
    public Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        => this._chatCompletionService.GetChatMessageContentsAsync(chatHistory, executionSettings, kernel, cancellationToken);

    /// <inheritdoc />
    public IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        => this._chatCompletionService.GetStreamingChatMessageContentsAsync(chatHistory, executionSettings, kernel, cancellationToken);

    #region Private

    private readonly IChatCompletionService _chatCompletionService;

    #endregion
}
