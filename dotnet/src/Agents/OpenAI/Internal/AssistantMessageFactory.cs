// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using OpenAI.Assistants;

namespace Microsoft.SemanticKernel.Agents.OpenAI.Internal;

/// <summary>
/// Factory for creating <see cref="MessageContent"/> based on <see cref="ChatMessageContent"/>.
/// Also able to produce <see cref="MessageCreationOptions"/>.
/// </summary>
/// <remarks>
/// Improves testability.
/// </remarks>
internal static class AssistantMessageFactory
{
    /// <summary>
    /// Produces <see cref="MessageCreationOptions"/> based on <see cref="ChatMessageContent"/>.
    /// </summary>
    /// <param name="message">The message content.</param>
    public static MessageCreationOptions CreateOptions(ChatMessageContent message)
    {
        MessageCreationOptions options = new();

        if (message.Metadata != null)
        {
            foreach (var metadata in message.Metadata)
            {
                options.Metadata.Add(metadata.Key, metadata.Value?.ToString() ?? string.Empty);
            }
        }

        return options;
    }

    /// <summary>
    /// Translates <see cref="ChatMessageContent.Items"/> into enumeration of <see cref="MessageContent"/>.
    /// </summary>
    /// <param name="message">The message content.</param>
    public static IEnumerable<MessageContent> GetMessageContents(ChatMessageContent message)
    {
        foreach (KernelContent content in message.Items)
        {
            if (content is TextContent textContent)
            {
                yield return MessageContent.FromText(content.ToString());
            }
            else if (content is ImageContent imageContent)
            {
                if (imageContent.Uri != null)
                {
                    yield return MessageContent.FromImageUrl(imageContent.Uri);
                }
                else if (string.IsNullOrWhiteSpace(imageContent.DataUri))
                {
                    yield return MessageContent.FromImageUrl(new(imageContent.DataUri!));
                }
            }
            else if (content is FileReferenceContent fileContent)
            {
                yield return MessageContent.FromImageFileId(fileContent.FileId);
            }
        }
    }
}
