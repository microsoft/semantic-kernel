// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using Azure.AI.Agents.Persistent;
using Microsoft.SemanticKernel.ChatCompletion;

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
    /// Translate metadata from a <see cref="ChatMessageContent"/> to be used for a <see cref="PersistentThreadMessage"/> or
    /// <see cref="ThreadMessageOptions"/>.
    /// </summary>
    /// <param name="message">The message content.</param>
    public static Dictionary<string, string> GetMetadata(ChatMessageContent message)
    {
        return message.Metadata?.ToDictionary(kvp => kvp.Key, kvp => kvp.Value?.ToString() ?? string.Empty) ?? [];
    }

    /// <summary>
    /// Translate attachments from a <see cref="ChatMessageContent"/> to be used for a <see cref="PersistentThreadMessage"/> or
    /// </summary>
    /// <param name="message">The message content.</param>
    public static IEnumerable<MessageAttachment> GetAttachments(ChatMessageContent message)
    {
        return
            message.Items
                .OfType<FileReferenceContent>()
                .Select(
                    fileContent =>
                        new MessageAttachment(fileContent.FileId, [.. GetToolDefinition(fileContent.Tools)]));
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
                    Attachments = [.. GetAttachments(message)],
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

    private static readonly Dictionary<string, ToolDefinition> s_toolMetadata = new()
    {
        { AzureAIAgent.Tools.CodeInterpreter, new CodeInterpreterToolDefinition() },
        { AzureAIAgent.Tools.FileSearch, new FileSearchToolDefinition() },
    };

    private static IEnumerable<ToolDefinition> GetToolDefinition(IEnumerable<string>? tools)
    {
        if (tools is null)
        {
            yield break;
        }

        foreach (string tool in tools)
        {
            if (s_toolMetadata.TryGetValue(tool, out ToolDefinition? toolDefinition))
            {
                yield return toolDefinition;
            }
        }
    }
}
