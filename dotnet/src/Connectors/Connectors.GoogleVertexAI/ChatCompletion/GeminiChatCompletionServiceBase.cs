// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.ComponentModel;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI;

/// <summary>
/// Represents a base class for chat completion service using GoogleVertex AI Gemini API.
/// </summary>
[EditorBrowsable(EditorBrowsableState.Never)]
[Browsable(false)]
public abstract class GeminiChatCompletionServiceBase : IChatCompletionService
{
    private protected Dictionary<string, object?> AttributesInternal { get; } = new();
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
}
