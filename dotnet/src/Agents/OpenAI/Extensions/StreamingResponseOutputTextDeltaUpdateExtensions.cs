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
    public static StreamingChatMessageContent ToStreamingChatMessageContent(this StreamingResponseOutputTextDeltaUpdate update)
    {
        StreamingChatMessageContent content =
            new(AuthorRole.Assistant, content: null)
            {
                InnerContent = update,
            };

        content.Items.Add(new StreamingTextContent(update.Delta));

        return content;
    }
}
