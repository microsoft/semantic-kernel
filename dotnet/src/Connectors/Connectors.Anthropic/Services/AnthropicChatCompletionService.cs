// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Anthropic;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Anthropic.Core;
using Microsoft.SemanticKernel.TextGeneration;

namespace Microsoft.SemanticKernel.Connectors.Anthropic.Services;

/// <summary>
/// Anthropic chat completion service.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class AnthropicChatCompletionService : IChatCompletionService, ITextGenerationService
{
    #region Private Fields

    /// <summary>Core implementation for Anthropic API.</summary>
    private readonly AnthropicClientCore _client;

    /// <summary>
    /// Default base URL for the Anthropic API.
    /// </summary>
    private static readonly Uri s_defaultBaseUrl = new("https://api.anthropic.com");

    #endregion

    #region Constructors

    /// <summary>
    /// Create an instance of the Anthropic chat completion connector.
    /// </summary>
    /// <param name="modelId">Model name (e.g., claude-sonnet-4-20250514).</param>
    /// <param name="apiKey">API Key for authentication.</param>
    /// <param name="baseUrl">Base URL for the API endpoint. Defaults to https://api.anthropic.com.</param>
    /// <param name="endpointId">Optional endpoint identifier for telemetry.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AnthropicChatCompletionService(
        string modelId,
        string apiKey,
        Uri? baseUrl = null,
        string? endpointId = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        this._client = new AnthropicClientCore(
            modelId,
            apiKey,
            baseUrl ?? s_defaultBaseUrl,
            endpointId,
            httpClient,
            loggerFactory?.CreateLogger(typeof(AnthropicChatCompletionService)));
    }

    /// <summary>
    /// Create an instance of the Anthropic chat completion connector using an existing AnthropicClient.
    /// </summary>
    /// <param name="modelId">Model name (e.g., claude-sonnet-4-20250514).</param>
    /// <param name="anthropicClient">Pre-configured <see cref="AnthropicClient"/>.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <remarks>
    /// Note: Instances created this way might not have the default diagnostics settings.
    /// It's up to the caller to configure the client appropriately.
    /// </remarks>
    public AnthropicChatCompletionService(
        string modelId,
        AnthropicClient anthropicClient,
        ILoggerFactory? loggerFactory = null)
    {
        this._client = new AnthropicClientCore(
            modelId,
            anthropicClient,
            loggerFactory?.CreateLogger(typeof(AnthropicChatCompletionService)));
    }

    #endregion

    #region IChatCompletionService Implementation

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._client.Attributes;

    /// <inheritdoc/>
    public Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
        => this._client.GetChatMessageContentsAsync(
            this._client.ModelId, chatHistory, executionSettings, kernel, cancellationToken);

    /// <inheritdoc/>
    public IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
        => this._client.GetStreamingChatMessageContentsAsync(
            this._client.ModelId, chatHistory, executionSettings, kernel, cancellationToken);

    #endregion

    #region ITextGenerationService Implementation

    /// <inheritdoc/>
    public Task<IReadOnlyList<TextContent>> GetTextContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
        => this._client.GetChatAsTextContentsAsync(
            this._client.ModelId, prompt, executionSettings, kernel, cancellationToken);

    /// <inheritdoc/>
    public IAsyncEnumerable<StreamingTextContent> GetStreamingTextContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
        => this._client.GetChatAsTextStreamingContentsAsync(
            this._client.ModelId, prompt, executionSettings, kernel, cancellationToken);

    #endregion
}
