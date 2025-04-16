// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using Microsoft.SemanticKernel;
using ModelContextProtocol.Protocol.Types;

namespace MCPClient;

/// <summary>
/// Extension methods for <see cref="ChatMessageContent"/>.
/// </summary>
public static class ChatMessageContentExtensions
{
    /// <summary>
    /// Converts a <see cref="ChatMessageContent"/> to a <see cref="CreateMessageResult"/>.
    /// </summary>
    /// <param name="chatMessageContent">The <see cref="ChatMessageContent"/> to convert.</param>
    /// <returns>The corresponding <see cref="CreateMessageResult"/>.</returns>
    public static CreateMessageResult ToCreateMessageResult(this ChatMessageContent chatMessageContent)
    {
        // Using the same heuristic as in the original MCP SDK code: McpClientExtensions.ToCreateMessageResult for consistency.
        // ChatMessageContent can contain multiple items of different modalities, while the CreateMessageResult
        // can only have a single content type: text, image, or audio. First, look for image or audio content,
        // and if not found, fall back to the text content type by concatenating the text of all text contents.
        Content? content = null;

        foreach (KernelContent item in chatMessageContent.Items)
        {
            if (item is ImageContent image)
            {
                content = new Content
                {
                    Type = "image",
                    Data = Convert.ToBase64String(image.Data!.Value.Span),
                    MimeType = image.MimeType
                };
                break;
            }
            else if (item is AudioContent audio)
            {
                content = new Content
                {
                    Type = "audio",
                    Data = Convert.ToBase64String(audio.Data!.Value.Span),
                    MimeType = audio.MimeType
                };
                break;
            }
        }

        content ??= new Content
        {
            Type = "text",
            Text = string.Concat(chatMessageContent.Items.OfType<TextContent>()),
            MimeType = "text/plain"
        };

        return new CreateMessageResult
        {
            Role = chatMessageContent.Role.ToMCPRole(),
            Model = chatMessageContent.ModelId ?? "unknown",
            Content = content
        };
    }
}
