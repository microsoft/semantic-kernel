// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI;

/// <summary>
/// Represents a chat completion service using Google AI Gemini API.
/// </summary>
public sealed class GoogleAIGeminiChatCompletionService : IChatCompletionService
{
    private readonly Dictionary<string, object?> _attributesInternal = new();
    private readonly GeminiChatCompletionClient _chatCompletionClient;

    /// <summary>
    /// Initializes a new instance of the <see cref="GoogleAIGeminiChatCompletionService"/> class.
    /// </summary>
    /// <param name="model">The Gemini model for the chat completion service.</param>
    /// <param name="apiKey">The API key for authentication.</param>
    /// <param name="httpClient">Optional HTTP client to be used for communication with the Gemini API.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public GoogleAIGeminiChatCompletionService(
        string model,
        string apiKey,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(model);
        Verify.NotNullOrWhiteSpace(apiKey);

        this._chatCompletionClient = new GeminiChatCompletionClient(
#pragma warning disable CA2000
            httpClient: HttpClientProvider.GetHttpClient(httpClient),
#pragma warning restore CA2000
            modelId: model,
            httpRequestFactory: new GoogleAIHttpRequestFactory(),
            endpointProvider: new GoogleAIEndpointProvider(apiKey),
            logger: loggerFactory?.CreateLogger(typeof(GoogleAIGeminiChatCompletionService)));
        this._attributesInternal.Add(AIServiceExtensions.ModelIdKey, model);
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
        return this._chatCompletionClient.GenerateChatMessageAsync(chatHistory, kernel, executionSettings, cancellationToken);
    }

    /// <inheritdoc />
    public IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        return this._chatCompletionClient.StreamGenerateChatMessageAsync(chatHistory, kernel, executionSettings, cancellationToken);
    }
}
