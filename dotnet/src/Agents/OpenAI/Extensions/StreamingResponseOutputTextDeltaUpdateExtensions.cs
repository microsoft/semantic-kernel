// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Responses;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

[ExcludeFromCodeCoverage]
internal static class StreamingResponseOutputTextDeltaUpdateExtensions
{
    /// <summary>
    /// Converts a <see cref="StreamingResponseOutputTextDeltaUpdate"/> instance to a <see cref="StreamingChatMessageContent"/>.
    /// </summary>
    /// <param name="update">Instance of <see cref="StreamingResponseOutputTextDeltaUpdate"/></param>
    /// <param name="modelId"></param>
    /// <param name="role"></param>
    public static StreamingChatMessageContent ToStreamingChatMessageContent(this StreamingResponseOutputTextDeltaUpdate update, string? modelId, AuthorRole? role)
    {
        StreamingChatMessageContent content =
            new(role ?? AuthorRole.Assistant, content: null)
            {
                ModelId = modelId,
                InnerContent = update,
            };

        content.Items.Add(new StreamingTextContent(update.Delta));

        return content;
    }

    /// <summary>
    /// Converts a <see cref="StreamingResponseErrorUpdate"/> instance to a <see cref="StreamingChatMessageContent"/>.
    /// </summary>
    /// <param name="update">Instance of <see cref="StreamingResponseOutputTextDeltaUpdate"/></param>
    /// <param name="modelId"></param>
    /// <param name="role"></param>
    public static StreamingChatMessageContent ToStreamingChatMessageContent(this StreamingResponseErrorUpdate update, string? modelId, AuthorRole? role)
    {
        StreamingChatMessageContent content =
            new(role ?? AuthorRole.Assistant, content: null)
            {
                ModelId = modelId,
                InnerContent = update,
            };

        content.Items.Add(new StreamingTextContent(update.Message));

        return content;
    }

    /// <summary>
    /// Converts a <see cref="StreamingResponseRefusalDoneUpdate"/> instance to a <see cref="StreamingChatMessageContent"/>.
    /// </summary>
    /// <param name="update">Instance of <see cref="StreamingResponseOutputTextDeltaUpdate"/></param>
    /// <param name="modelId"></param>
    /// <param name="role"></param>
    public static StreamingChatMessageContent ToStreamingChatMessageContent(this StreamingResponseRefusalDoneUpdate update, string? modelId, AuthorRole? role)
    {
        StreamingChatMessageContent content =
            new(role ?? AuthorRole.Assistant, content: null)
            {
                ModelId = modelId,
                InnerContent = update,
            };

        content.Items.Add(new StreamingTextContent(update.Refusal));

        return content;
    }
}
