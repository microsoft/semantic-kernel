// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.ComponentModel;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.TextGeneration;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI;

/// <summary>
/// Represents a base class for chat completion service using GoogleVertex AI Gemini API.
/// </summary>
[EditorBrowsable(EditorBrowsableState.Never)]
public abstract class GeminiChatCompletionServiceBase : IChatCompletionService, ITextGenerationService
{
    private protected Dictionary<string, object?> AttributesInternal { get; } = new();
    private protected IGeminiTextGenerationClient TextGenerationClient { get; init; } = null!;
    private protected IGeminiChatCompletionClient ChatCompletionClient { get; init; } = null!;

    /// <inheritdoc />
    public IReadOnlyDictionary<string, object?> Attributes => this.AttributesInternal;

    /// <inheritdoc />
    public Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        return this.ChatCompletionClient.GenerateChatMessageAsync(chatHistory, executionSettings, cancellationToken);
    }

    /// <inheritdoc />
    public IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        return this.ChatCompletionClient.StreamGenerateChatMessageAsync(chatHistory, executionSettings, cancellationToken);
    }

    /// <inheritdoc />
    public Task<IReadOnlyList<TextContent>> GetTextContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        return this.TextGenerationClient.GenerateTextAsync(prompt, executionSettings, cancellationToken);
    }

    /// <inheritdoc />
    public IAsyncEnumerable<StreamingTextContent> GetStreamingTextContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        return this.TextGenerationClient.StreamGenerateTextAsync(prompt, executionSettings, cancellationToken);
    }
}
