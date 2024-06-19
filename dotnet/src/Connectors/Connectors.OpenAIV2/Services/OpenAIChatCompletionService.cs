// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Services;
using OpenAI;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// OpenAI chat completion service.
/// </summary>
public sealed class OpenAIChatCompletionService : IChatCompletionService
{
    private readonly OpenAIClientCore _core;

    /// <summary>
    /// Create an instance of the OpenAI chat completion connector
    /// </summary>
    /// <param name="config">Service configuration</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    public OpenAIChatCompletionService(
        OpenAIClientChatCompletionnConfig config,
        HttpClient? httpClient = null)
    {
        this._core = new(config, httpClient);

        this._core.AddAttribute(AIServiceExtensions.ModelIdKey, config.ModelId);
        this._core.AddAttribute(OpenAIClientCore.OrganizationKey, config.OrganizationId);
    }

    /// <summary>
    /// Create an instance of the OpenAI chat completion connector
    /// </summary>
    /// <param name="modelId">Model name</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public OpenAIChatCompletionService(
        string modelId,
        OpenAIClient openAIClient,
        ILoggerFactory? loggerFactory = null)
    {
        this._core = new(
            modelId,
            openAIClient,
            loggerFactory?.CreateLogger(typeof(OpenAIChatCompletionService)));

        this._core.AddAttribute(AIServiceExtensions.ModelIdKey, modelId);
    }

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._core.Attributes;

    /// <inheritdoc/>
    public async Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        => [await this._core.GetChatMessageContentsAsync(chatHistory, executionSettings, kernel, cancellationToken).ConfigureAwait(false)];

    /// <inheritdoc/>
    public IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        => this._core.GetStreamingChatMessageContentsAsync(chatHistory, executionSettings, kernel, cancellationToken);
}
