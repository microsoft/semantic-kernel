// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Agents.OpenAI.Internal;
using OpenAI.Assistants;
using OpenAI.Responses;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Convenience extensions for converting <see cref="ChatMessageContent"/>.
/// </summary>
public static class ChatContentMessageExtensions
{
    /// <summary>
    /// Converts a <see cref="ChatMessageContent"/> instance to a <see cref="ThreadInitializationMessage"/>.
    /// </summary>
    /// <param name="message">The chat message content to convert.</param>
    /// <returns>A <see cref="ThreadInitializationMessage"/> instance.</returns>
    public static ThreadInitializationMessage ToThreadInitializationMessage(this ChatMessageContent message)
    {
        return
            new ThreadInitializationMessage(
                role: message.Role.ToMessageRole(),
                content: AssistantMessageFactory.GetMessageContents(message));
    }

    /// <summary>
    /// Converts a collection of <see cref="ChatMessageContent"/> instances to a collection of <see cref="ThreadInitializationMessage"/> instances.
    /// </summary>
    /// <param name="messages">The collection of chat message contents to convert.</param>
    /// <returns>A collection of <see cref="ThreadInitializationMessage"/> instances.</returns>
    public static IEnumerable<ThreadInitializationMessage> ToThreadInitializationMessages(this IEnumerable<ChatMessageContent> messages)
    {
        return messages.Select(message => message.ToThreadInitializationMessage());
    }

    /// <summary>
    /// Converts a <see cref="ChatMessageContent"/> instance to a <see cref="ResponseItem"/>.
    /// </summary>
    /// <param name="message">The chat message content to convert.</param>
    /// <returns>A <see cref="ResponseItem"/> instance.</returns>
    public static ResponseItem ToResponseItem(this ChatMessageContent message)
    {
        string content = message.Content ?? string.Empty;
        return message.Role.Label switch
        {
            "system" => ResponseItem.CreateSystemMessageItem(content),
            "user" => ResponseItem.CreateUserMessageItem(content),
            "developer" => ResponseItem.CreateDeveloperMessageItem(content),
            "assistant" => ResponseItem.CreateAssistantMessageItem(content),
            _ => throw new NotSupportedException($"Unsupported role {message.Role.Label}. Only system, user, developer or assistant roles are allowed."),
        };
    }
}
