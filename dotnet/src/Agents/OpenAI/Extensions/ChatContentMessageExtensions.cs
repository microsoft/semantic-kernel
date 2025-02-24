// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Agents.OpenAI.Internal;
using OpenAI.Assistants;

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
}
