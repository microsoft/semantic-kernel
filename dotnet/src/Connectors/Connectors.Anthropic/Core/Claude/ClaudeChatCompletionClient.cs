// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.Anthropic.Core;

/// <summary>
/// Represents a client for interacting with the chat completion Claude models.
/// </summary>
internal sealed class ClaudeChatCompletionClient
{
    private readonly HttpClient _httpClient;
    private readonly ILogger _logger;
    private readonly string _modelId;
    private readonly Uri _endpoint;
    private readonly Func<HttpRequestMessage, Task>? _customRequestHandler;

    /// <summary>
    /// Represents a client for interacting with the chat completion Claude model.
    /// </summary>
    /// <param name="httpClient">HttpClient instance used to send HTTP requests</param>
    /// <param name="modelId">Id of the model supporting chat completion</param>
    /// <param name="apiKey">Api key</param>
    /// <param name="logger">Logger instance used for logging (optional)</param>
    public ClaudeChatCompletionClient(
        HttpClient httpClient,
        string modelId,
        string apiKey,
        ILogger? logger = null)
    {
        Verify.NotNull(httpClient);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        this._httpClient = httpClient;
        this._logger = logger ?? NullLogger.Instance;
        this._modelId = modelId;
        this._endpoint = new Uri("https://api.anthropic.com/v1/messages");
    }

    /// <summary>
    /// Represents a client for interacting with the chat completion Claude model.
    /// </summary>
    /// <param name="httpClient">HttpClient instance used to send HTTP requests</param>
    /// <param name="modelId">Id of the model supporting chat completion</param>
    /// <param name="endpoint">Endpoint for the chat completion model</param>
    /// <param name="requestHandler">A custom request handler to be used for sending HTTP requests</param>
    /// <param name="logger">Logger instance used for logging (optional)</param>
    public ClaudeChatCompletionClient(
        HttpClient httpClient,
        string modelId,
        Uri endpoint,
        Func<HttpRequestMessage, Task>? requestHandler,
        ILogger? logger = null)
    {
        Verify.NotNull(httpClient);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNull(endpoint);

        this._httpClient = httpClient;
        this._logger = logger ?? NullLogger.Instance;
        this._modelId = modelId;
        this._endpoint = endpoint;
        this._customRequestHandler = requestHandler;
    }

    /// <summary>
    /// Generates a chat message asynchronously.
    /// </summary>
    /// <param name="chatHistory">The chat history containing the conversation data.</param>
    /// <param name="executionSettings">Optional settings for prompt execution.</param>
    /// <param name="kernel">A kernel instance.</param>
    /// <param name="cancellationToken">A cancellation token to cancel the operation.</param>
    /// <returns>Returns a list of chat message contents.</returns>
    public async Task<IReadOnlyList<ChatMessageContent>> GenerateChatMessageAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        await Task.Yield();
        throw new NotImplementedException("Implement this method in next PR.");
    }

    /// <summary>
    /// Generates a stream of chat messages asynchronously.
    /// </summary>
    /// <param name="chatHistory">The chat history containing the conversation data.</param>
    /// <param name="executionSettings">Optional settings for prompt execution.</param>
    /// <param name="kernel">A kernel instance.</param>
    /// <param name="cancellationToken">A cancellation token to cancel the operation.</param>
    /// <returns>An asynchronous enumerable of <see cref="StreamingChatMessageContent"/> streaming chat contents.</returns>
    public async IAsyncEnumerable<StreamingChatMessageContent> StreamGenerateChatMessageAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await Task.Yield();
        throw new NotImplementedException("Implement this method in next PR.");
        yield break;
    }
}
