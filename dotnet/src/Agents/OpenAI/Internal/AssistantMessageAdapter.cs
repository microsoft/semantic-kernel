// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using OpenAI.Assistants;

namespace Microsoft.SemanticKernel.Agents.OpenAI.Internal;

internal static class AssistantMessageAdapter
{
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

    public static IEnumerable<MessageContent> GetMessageContents(ChatMessageContent message, MessageCreationOptions options)
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
                //else if (string.IsNullOrWhiteSpace(imageContent.DataUri))
                //{
                //    %%% BUG: https://github.com/openai/openai-dotnet/issues/135
                //        URI does not accept the format used for `DataUri`
                //        Approach is inefficient anyway...
                //    yield return MessageContent.FromImageUrl(new Uri(imageContent.DataUri!));
                //}
            }
            else if (content is MessageAttachmentContent attachmentContent)
            {
                options.Attachments.Add(new MessageCreationAttachment(attachmentContent.FileId, [ToolDefinition.CreateCodeInterpreter()])); // %%% TODO: Tool Type
            }
            else if (content is FileReferenceContent fileContent)
            {
                yield return MessageContent.FromImageFileId(fileContent.FileId);
            }
        }
    }
}
