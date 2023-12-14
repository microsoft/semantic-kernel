// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Azure OpenAI and OpenAI Specialized streaming chat message content.
/// </summary>
/// <remarks>
/// Represents a chat message content chunk that was streamed from the remote model.
/// </remarks>
public sealed class OpenAIStreamingChatMessageContent : StreamingChatMessageContent
{
    /// <summary>
    /// The reason why the completion finished.
    /// </summary>
    public CompletionsFinishReason? FinishReason { get; set; }

    /// <summary>
    /// Create a new instance of the <see cref="OpenAIStreamingChatMessageContent"/> class.
    /// </summary>
    /// <param name="chatUpdate">Internal Azure SDK Message update representation</param>
    /// <param name="choiceIndex">Index of the choice</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="metadata">Additional metadata</param>
    internal OpenAIStreamingChatMessageContent(
        StreamingChatCompletionsUpdate chatUpdate,
        int choiceIndex,
        string modelId,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(
            chatUpdate.Role.HasValue ? new AuthorRole(chatUpdate.Role.Value.ToString()) : null,
            chatUpdate.ContentUpdate,
            chatUpdate,
            choiceIndex,
            modelId,
            Encoding.UTF8,
            metadata)
    {
        this.ToolCallUpdate = chatUpdate.ToolCallUpdate;
        this.FinishReason = chatUpdate?.FinishReason;
    }

    /// <summary>
    /// Create a new instance of the <see cref="OpenAIStreamingChatMessageContent"/> class.
    /// </summary>
    /// <param name="authorRole">Author role of the message</param>
    /// <param name="content">Content of the message</param>
    /// <param name="tootToolCallUpdate">Tool call update</param>
    /// <param name="completionsFinishReason">Completion finish reason</param>
    /// <param name="choiceIndex">Index of the choice</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="metadata">Additional metadata</param>
    internal OpenAIStreamingChatMessageContent(
        AuthorRole? authorRole,
        string? content,
        ChatCompletionsToolCall? tootToolCallUpdate = null,
        CompletionsFinishReason? completionsFinishReason = null,
        int choiceIndex = 0,
        string? modelId = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(
            authorRole,
            content,
            null,
            choiceIndex,
            modelId,
            Encoding.UTF8,
            metadata)
    {
        this.ToolCallUpdate = tootToolCallUpdate;
        this.FinishReason = completionsFinishReason;
    }

    /// <summary>Gets any update information in the message about a tool call.</summary>
    public ChatCompletionsToolCall? ToolCallUpdate { get; }

    /// <inheritdoc/>
    public override byte[] ToByteArray() => this.Encoding.GetBytes(this.ToString());

    /// <inheritdoc/>
    public override string ToString() => this.Content ?? string.Empty;
}
