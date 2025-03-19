// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.Extensions.AI;

internal static class ChatMessageExtensions
{
    /// <summary>Converts a <see cref="ChatMessage"/> to a <see cref="ChatMessageContent"/>.</summary>
    /// <remarks>This conversion should not be necessary once SK eventually adopts the shared content types.</remarks>
    internal static ChatMessageContent ToChatMessageContent(this ChatMessage message, Microsoft.Extensions.AI.ChatResponse? response = null)
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
            KernelContent? resultContent = content switch
            {
                Microsoft.Extensions.AI.TextContent tc => new Microsoft.SemanticKernel.TextContent(tc.Text),
                Microsoft.Extensions.AI.DataContent dc when dc.HasTopLevelMediaType("image") => new Microsoft.SemanticKernel.ImageContent(dc.Uri),
                Microsoft.Extensions.AI.UriContent uc when uc.HasTopLevelMediaType("image") => new Microsoft.SemanticKernel.ImageContent(uc.Uri),
                Microsoft.Extensions.AI.DataContent dc when dc.HasTopLevelMediaType("audio") => new Microsoft.SemanticKernel.AudioContent(dc.Uri),
                Microsoft.Extensions.AI.UriContent uc when uc.HasTopLevelMediaType("audio") => new Microsoft.SemanticKernel.AudioContent(uc.Uri),
                Microsoft.Extensions.AI.DataContent dc => new Microsoft.SemanticKernel.BinaryContent(dc.Uri),
                Microsoft.Extensions.AI.UriContent uc => new Microsoft.SemanticKernel.BinaryContent(uc.Uri),
                Microsoft.Extensions.AI.FunctionCallContent fcc => new Microsoft.SemanticKernel.FunctionCallContent(fcc.Name, null, fcc.CallId, fcc.Arguments is not null ? new(fcc.Arguments) : null),
                Microsoft.Extensions.AI.FunctionResultContent frc => new Microsoft.SemanticKernel.FunctionResultContent(callId: frc.CallId, result: frc.Result),
                _ => null
            };

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
