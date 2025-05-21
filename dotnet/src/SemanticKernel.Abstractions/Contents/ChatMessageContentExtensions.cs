// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel;

internal static class ChatMessageContentExtensions
{
    /// <summary>Converts a <see cref="ChatMessageContent"/> to a <see cref="ChatMessage"/>.</summary>
    /// <remarks>This conversion should not be necessary once SK eventually adopts the shared content types.</remarks>
    internal static ChatMessage ToChatMessage(this ChatMessageContent content)
    {
        ChatMessage message = new()
        {
            AdditionalProperties = content.Metadata is not null ? new(content.Metadata) : null,
            AuthorName = content.AuthorName,
            RawRepresentation = content.InnerContent,
            Role = content.Role.Label is string label ? new ChatRole(label) : ChatRole.User,
        };

        foreach (var item in content.Items)
        {
            AIContent? aiContent = null;
            switch (item)
            {
                case Microsoft.SemanticKernel.TextContent tc:
                    aiContent = new Microsoft.Extensions.AI.TextContent(tc.Text);
                    break;

                case Microsoft.SemanticKernel.ImageContent ic:
                    aiContent =
                        ic.DataUri is not null ? new Microsoft.Extensions.AI.DataContent(ic.DataUri, ic.MimeType) :
                        ic.Uri is not null ? new Microsoft.Extensions.AI.UriContent(ic.Uri, ic.MimeType ?? "image/*") :
                        null;
                    break;

                case Microsoft.SemanticKernel.AudioContent ac:
                    aiContent =
                        ac.DataUri is not null ? new Microsoft.Extensions.AI.DataContent(ac.DataUri, ac.MimeType) :
                        ac.Uri is not null ? new Microsoft.Extensions.AI.UriContent(ac.Uri, ac.MimeType ?? "audio/*") :
                        null;
                    break;

                case Microsoft.SemanticKernel.BinaryContent bc:
                    aiContent =
                        bc.DataUri is not null ? new Microsoft.Extensions.AI.DataContent(bc.DataUri, bc.MimeType) :
                        bc.Uri is not null ? new Microsoft.Extensions.AI.UriContent(bc.Uri, bc.MimeType ?? "application/octet-stream") :
                        null;
                    break;

                case Microsoft.SemanticKernel.FunctionCallContent fcc:
                    aiContent = new Microsoft.Extensions.AI.FunctionCallContent(fcc.Id ?? string.Empty, fcc.FunctionName, fcc.Arguments);
                    break;

                case Microsoft.SemanticKernel.FunctionResultContent frc:
                    aiContent = new Microsoft.Extensions.AI.FunctionResultContent(frc.CallId ?? string.Empty, frc.Result);
                    break;
            }

            if (aiContent is not null)
            {
                aiContent.RawRepresentation = item.InnerContent;
                aiContent.AdditionalProperties = item.Metadata is not null ? new(item.Metadata) : null;

                message.Contents.Add(aiContent);
            }
        }

        return message;
    }
}
