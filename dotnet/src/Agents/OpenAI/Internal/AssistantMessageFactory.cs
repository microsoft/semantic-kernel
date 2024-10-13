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
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
                    yield return MessageContent.FromImageUrl(imageContent.Uri);
                }
                else if (string.IsNullOrWhiteSpace(imageContent.DataUri))
                {
                    yield return MessageContent.FromImageUrl(new(imageContent.DataUri!));
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
=======
<<<<<<< div
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
                    yield return MessageContent.FromImageUri(imageContent.Uri);
                }
                else if (string.IsNullOrWhiteSpace(imageContent.DataUri))
                {
                    yield return MessageContent.FromImageUri(new(imageContent.DataUri!));
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
                }
            }
            else if (content is FileReferenceContent fileContent)
            {
                yield return MessageContent.FromImageFileId(fileContent.FileId);
            }
        }
    }
}
