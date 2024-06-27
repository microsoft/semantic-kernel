// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Chat;

namespace Microsoft.SemanticKernel.Connectors.AzureOpenAI;

/// <summary>
/// Azure OpenAI specialized streaming chat message content.
/// </summary>
/// <remarks>
/// Represents a chat message content chunk that was streamed from the remote model.
/// </remarks>
public sealed class AzureOpenAIStreamingChatMessageContent : StreamingChatMessageContent
{
    /// <summary>
    /// The reason why the completion finished.
    /// </summary>
    public ChatFinishReason? FinishReason { get; set; }

    /// <summary>
    /// Create a new instance of the <see cref="AzureOpenAIStreamingChatMessageContent"/> class.
    /// </summary>
    /// <param name="chatUpdate">Internal Azure SDK Message update representation</param>
    /// <param name="choiceIndex">Index of the choice</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="metadata">Additional metadata</param>
    internal AzureOpenAIStreamingChatMessageContent(
        StreamingChatCompletionUpdate chatUpdate,
        int choiceIndex,
        string modelId,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(
            chatUpdate.Role.HasValue ? new AuthorRole(chatUpdate.Role.Value.ToString()) : null,
            null,
            chatUpdate,
            choiceIndex,
            modelId,
            Encoding.UTF8,
            metadata)
    {
        this.ToolCallUpdate = chatUpdate.ToolCallUpdates;
        this.FinishReason = chatUpdate.FinishReason;
        this.Items = CreateContentItems(chatUpdate.ContentUpdate);
    }

    /// <summary>
    /// Create a new instance of the <see cref="AzureOpenAIStreamingChatMessageContent"/> class.
    /// </summary>
    /// <param name="authorRole">Author role of the message</param>
    /// <param name="content">Content of the message</param>
    /// <param name="tootToolCallUpdate">Tool call update</param>
    /// <param name="completionsFinishReason">Completion finish reason</param>
    /// <param name="choiceIndex">Index of the choice</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="metadata">Additional metadata</param>
    internal AzureOpenAIStreamingChatMessageContent(
        AuthorRole? authorRole,
        string? content,
        IReadOnlyList<StreamingChatToolCallUpdate>? tootToolCallUpdate = null,
        ChatFinishReason? completionsFinishReason = null,
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
    public IReadOnlyList<StreamingChatToolCallUpdate>? ToolCallUpdate { get; }

    /// <inheritdoc/>
    public override byte[] ToByteArray() => this.Encoding.GetBytes(this.ToString());

    /// <inheritdoc/>
    public override string ToString() => this.Content ?? string.Empty;

    private static StreamingKernelContentItemCollection CreateContentItems(IReadOnlyList<ChatMessageContentPart> contentUpdate)
    {
        StreamingKernelContentItemCollection collection = [];

        foreach (var content in contentUpdate)
        {
            // We only support text content for now.
            if (content.Kind == ChatMessageContentPartKind.Text)
            {
                collection.Add(new StreamingTextContent(content.Text));
            }
        }

        return collection;
    }
}
