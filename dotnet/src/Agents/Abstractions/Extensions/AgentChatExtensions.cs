// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.Extensions;

/// <summary>
/// Extension methods for <see cref="KernelAgent"/>
/// </summary>
public static class AgentChatExtensions
{
    /// <summary>
    /// Add user message to chat history
    /// </summary>
    /// <param name="chat">The target chat.</param>
    /// <param name="input">Optional user input.</param>
    public static ChatMessageContent? AppendUserMessageToHistory(this AgentChat chat, string? input)
    {
        var message = string.IsNullOrWhiteSpace(input) ? null : new ChatMessageContent(AuthorRole.User, input);

        if (message != null)
        {
            chat.AddChatMessage(message);
        }

        return message;
    }
}
