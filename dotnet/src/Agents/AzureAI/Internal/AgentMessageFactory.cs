// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.ChatCompletion;
using Azure.AI.Projects;

namespace Microsoft.SemanticKernel.Agents.AzureAI.Internal;

/// <summary>
/// Factory for creating <see cref="MessageContent"/> based on <see cref="ChatMessageContent"/>.
/// </summary>
/// <remarks>
/// Improves testability.
/// </remarks>
internal static class AgentMessageFactory
{
    /// <summary>
    /// Translate metadata from a <see cref="ChatMessageContent"/> to be used for a <see cref="ThreadMessage"/> or
    /// <see cref="ThreadMessageOptions"/>.
    /// </summary>
    /// <param name="message">The message content.</param>
    public static Dictionary<string, string> GetMetadata(ChatMessageContent message)
    {
        return message.Metadata?.ToDictionary(kvp => kvp.Key, kvp => kvp.Value?.ToString() ?? string.Empty) ?? [];
    }

    /// <summary>
    /// Translates a set of <see cref="ChatMessageContent"/> to a set of <see cref="ThreadMessageOptions"/>."/>
    /// </summary>
    /// <param name="messages">A list of <see cref="ChatMessageContent"/> objects/</param>
    public static IEnumerable<ThreadMessageOptions> GetThreadMessages(IEnumerable<ChatMessageContent>? messages)
    {
        if (messages is not null)
        {
            foreach (ChatMessageContent message in messages)
            {
                string? content = message.Content;
                if (string.IsNullOrWhiteSpace(content))
                {
                    continue;
                }

                ThreadMessageOptions threadMessage = new(
                    role: message.Role == AuthorRole.User ? MessageRole.User : MessageRole.Agent,
                    content: message.Content)
                {
                    Attachments = message.Items.OfType<FileReferenceContent>().Select(fileContent => new MessageAttachment(fileContent.FileId, [])).ToArray(),
                };

                if (message.Metadata != null)
                {
                    foreach (string key in message.Metadata.Keys)
                    {
                        threadMessage.Metadata = GetMetadata(message);
                    }
                }

                yield return threadMessage;
            }
        }
    }
}
