// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using ModelContextProtocol.Protocol.Types;

namespace MCPClient;

/// <summary>
/// Extension methods for <see cref="GetPromptResult"/>.
/// </summary>
internal static class PromptResultExtensions
{
    /// <summary>
    /// Converts a <see cref="GetPromptResult"/> to a <see cref="ChatHistory"/>.
    /// </summary>
    /// <param name="result">The prompt result to convert.</param>
    /// <returns>The corresponding <see cref="ChatHistory"/>.</returns>
    public static ChatHistory ToChatHistory(this GetPromptResult result)
    {
        ChatHistory chatHistory = [];

        foreach (PromptMessage message in result.Messages)
        {
            ChatMessageContentItemCollection items = [];

            switch (message.Content.Type)
            {
                case "text":
                    items.Add(new TextContent(message.Content.Text));
                    break;
                case "image":
                    items.Add(new ImageContent(Convert.FromBase64String(message.Content.Data!), message.Content.MimeType));
                    break;
                default:
                    throw new InvalidOperationException($"Unexpected message content type '{message.Content.Type}'");
            }

            chatHistory.Add(new ChatMessageContent(message.Role.ToAuthorRole(), items));
        }

        return chatHistory;
    }
}
