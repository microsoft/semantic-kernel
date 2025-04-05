// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Azure.AI.Projects;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.AzureAI.Extensions;

/// <summary>
/// Extension methods to convert a <see cref="ThreadMessage"/> to a <see cref="ChatMessageContent"/>.
/// </summary>
public static class ThreadMessageExtensions
{
    /// <summary>
    /// Extension method to convert a <see cref="ThreadMessage"/> to a <see cref="ChatMessageContent"/>.
    /// </summary>
    /// <param name="message">The input <see cref="ThreadMessage"/>.</param>
    /// <param name="agentName">The agent name (optional).</param>
    /// <returns>The message as a <see cref="ChatMessageContent"/> instance.</returns>
    public static ChatMessageContent ToChatMessageContent(this ThreadMessage message, string? agentName)
        => message.ToChatMessageContent(agentName, completedStep: null);

    internal static ChatMessageContent ToChatMessageContent(this ThreadMessage message, string? agentName, RunStep? completedStep)
    {
        AuthorRole role = new(message.Role.ToString());

        Dictionary<string, object?>? metadata =
            new()
            {
                { nameof(ThreadMessage.CreatedAt), message.CreatedAt },
                { nameof(ThreadMessage.AssistantId), message.AssistantId },
                { nameof(ThreadMessage.ThreadId), message.ThreadId },
                { nameof(ThreadMessage.RunId), message.RunId },
                { nameof(MessageContentUpdate.MessageId), message.Id },
            };

        if (completedStep != null)
        {
            metadata[nameof(RunStepDetailsUpdate.StepId)] = completedStep.Id;
            metadata[nameof(RunStep.Usage)] = completedStep.Usage;
        }

        ChatMessageContent content =
            new(role, content: null)
            {
                AuthorName = agentName,
                Metadata = metadata,
            };

        foreach (MessageContent itemContent in message.ContentItems)
        {
            // Process text content
            if (itemContent is MessageTextContent textContent)
            {
                content.Items.Add(new TextContent(textContent.Text));

                foreach (MessageTextAnnotation annotation in textContent.Annotations)
                {
                    content.Items.Add(GenerateAnnotationContent(annotation));
                }
            }
            // Process image content
            else if (itemContent is MessageImageFileContent imageContent)
            {
                content.Items.Add(new FileReferenceContent(imageContent.FileId));
            }
        }

        return content;
    }

    private static AnnotationContent GenerateAnnotationContent(MessageTextAnnotation annotation)
    {
        string? fileId = null;

        if (annotation is MessageTextFileCitationAnnotation fileCitationAnnotation)
        {
            fileId = fileCitationAnnotation.FileId;
        }
        else if (annotation is MessageTextFilePathAnnotation filePathAnnotation)
        {
            fileId = filePathAnnotation.FileId;
        }

        return
            new(annotation.Text)
            {
                Quote = annotation.Text,
                FileId = fileId,
            };
    }
}
