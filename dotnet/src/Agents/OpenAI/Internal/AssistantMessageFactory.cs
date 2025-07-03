// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Connectors.FunctionCalling;
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
        bool hasTextContent = message.Items.OfType<TextContent>().Any();
        foreach (KernelContent content in message.Items)
        {
            if (content is TextContent textContent)
            {
                var text = content.ToString();
                if (string.IsNullOrWhiteSpace(text))
                {
                    // Message content must be non-empty.
                    continue;
                }
                yield return MessageContent.FromText(text);
            }
            else if (content is ImageContent imageContent)
            {
                if (imageContent.Uri != null)
                {
                    yield return MessageContent.FromImageUri(imageContent.Uri);
                }
                else if (!string.IsNullOrWhiteSpace(imageContent.DataUri))
                {
                    yield return MessageContent.FromImageUri(new(imageContent.DataUri!));
                }
            }
            else if (content is FileReferenceContent fileContent)
            {
                yield return MessageContent.FromImageFileId(fileContent.FileId);
            }
            else if (content is FunctionResultContent resultContent && resultContent.Result != null && !hasTextContent)
            {
                // Only convert a function result when text-content is not already present
                yield return MessageContent.FromText(FunctionCallsProcessor.ProcessFunctionResult(resultContent.Result));
            }
        }
    }
}
