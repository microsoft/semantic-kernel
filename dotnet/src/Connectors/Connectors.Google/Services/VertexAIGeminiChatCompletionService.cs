// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Google.Core;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.Google;

/// <summary>
/// Represents a chat completion service using Vertex AI Gemini API.
/// </summary>
public sealed class VertexAIGeminiChatCompletionService : IChatCompletionService
{
    private readonly Dictionary<string, object?> _attributesInternal = [];
    private readonly GeminiChatCompletionClient _chatCompletionClient;

    /// <summary>
    /// Initializes a new instance of the <see cref="VertexAIGeminiChatCompletionService"/> class.
    /// </summary>
    /// <param name="modelId">The Gemini model for the chat completion service.</param>
    /// <param name="bearerKey">The Bearer Key for authentication.</param>
    /// <param name="location">The region to process the request</param>
    /// <param name="projectId">Your project ID</param>
    /// <param name="apiVersion">Version of the Vertex API</param>
    /// <param name="isFineTunedModel">Whether this is a tuned model or not</param>
    /// <param name="httpClient">Optional HTTP client to be used for communication with the Gemini API.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public VertexAIGeminiChatCompletionService(
        string modelId,
        string bearerKey,
        string location,
        string projectId,
        VertexAIVersion apiVersion = VertexAIVersion.V1,
        bool isFineTunedModel = false,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
        : this(modelId, () => new ValueTask<string>(bearerKey), location, projectId, apiVersion, isFineTunedModel, httpClient, loggerFactory)
    {
        Verify.NotNullOrWhiteSpace(bearerKey);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="VertexAIGeminiChatCompletionService"/> class.
    /// </summary>
    /// <param name="modelId">The Gemini model for the chat completion service.</param>
    /// <param name="bearerTokenProvider">The Bearer Key provider for authentication.</param>
    /// <param name="location">The region to process the request</param>
    /// <param name="projectId">Your project ID</param>
    /// <param name="apiVersion">Version of the Vertex API</param>
    /// <param name="isFineTunedModel">Whether this is a tuned model or not</param>
    /// <param name="httpClient">Optional HTTP client to be used for communication with the Gemini API.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    /// <remarks>
    /// This <paramref name="bearerTokenProvider"/> will be called on every request,
    /// when providing the token consider using caching strategy and refresh token logic
    /// when it is expired or close to expiration.
    /// </remarks>
    public VertexAIGeminiChatCompletionService(
        string modelId,
        Func<ValueTask<string>> bearerTokenProvider,
        string location,
        string projectId,
        VertexAIVersion apiVersion = VertexAIVersion.V1,
        bool isFineTunedModel = false,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNull(bearerTokenProvider);
        Verify.NotNullOrWhiteSpace(location);
        Verify.NotNullOrWhiteSpace(projectId);

        this._chatCompletionClient = new GeminiChatCompletionClient(
#pragma warning disable CA2000
            httpClient: HttpClientProvider.GetHttpClient(httpClient),
#pragma warning restore CA2000
            modelId: modelId,
            bearerTokenProvider: bearerTokenProvider,
            location: location,
            projectId: projectId,
            apiVersion: apiVersion,
            isFineTunedModel: isFineTunedModel,
            logger: loggerFactory?.CreateLogger(typeof(VertexAIGeminiChatCompletionService)));
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
