// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.Extensions.AI;

internal static class ChatMessageExtensions
{
    /// <summary>Converts a <see cref="ChatMessage"/> to a <see cref="ChatMessageContent"/>.</summary>
    /// <remarks>This conversion should not be necessary once SK eventually adopts the shared content types.</remarks>
    internal static ChatMessageContent ToChatMessageContent(this ChatMessage message, ChatResponse? response = null)
    {
        ChatMessageContent result = new()
        {
            ModelId = response?.ModelId,
            AuthorName = message.AuthorName,
            InnerContent = response?.RawRepresentation ?? message.RawRepresentation,
            Metadata = message.AdditionalProperties,
            Role = new AuthorRole(message.Role.Value),
        };

        foreach (AIContent content in message.Contents)
        {
            KernelContent? resultContent = null;
            switch (content)
            {
                case Microsoft.Extensions.AI.TextContent tc:
                    resultContent = new Microsoft.SemanticKernel.TextContent(tc.Text);
                    break;

                case Microsoft.Extensions.AI.DataContent dc when dc.MediaTypeStartsWith("image/"):
                    resultContent = dc.Data is not null ?
                        new Microsoft.SemanticKernel.ImageContent(dc.Uri) :
                        new Microsoft.SemanticKernel.ImageContent(new Uri(dc.Uri));
                    break;

                case Microsoft.Extensions.AI.DataContent dc when dc.MediaTypeStartsWith("audio/"):
                    resultContent = dc.Data is not null ?
                        new Microsoft.SemanticKernel.AudioContent(dc.Uri) :
                        new Microsoft.SemanticKernel.AudioContent(new Uri(dc.Uri));
                    break;

                case Microsoft.Extensions.AI.DataContent dc:
                    resultContent = dc.Data is not null ?
                        new Microsoft.SemanticKernel.BinaryContent(dc.Uri) :
                        new Microsoft.SemanticKernel.BinaryContent(new Uri(dc.Uri));
                    break;

                case Microsoft.Extensions.AI.FunctionCallContent fcc:
                    resultContent = new Microsoft.SemanticKernel.FunctionCallContent(fcc.Name, null, fcc.CallId, fcc.Arguments is not null ? new(fcc.Arguments) : null);
                    break;

                case Microsoft.Extensions.AI.FunctionResultContent frc:
                    resultContent = new Microsoft.SemanticKernel.FunctionResultContent(callId: frc.CallId, result: frc.Result);
                    break;
            }

            if (resultContent is not null)
            {
                resultContent.Metadata = content.AdditionalProperties;
                resultContent.InnerContent = content.RawRepresentation;
                resultContent.ModelId = response?.ModelId;
                result.Items.Add(resultContent);
            }
        }

        return result;
    }
}
