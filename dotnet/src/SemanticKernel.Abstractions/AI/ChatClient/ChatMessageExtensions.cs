// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.ChatCompletion;

internal static class ChatMessageExtensions
{
    /// <summary>Converts a <see cref="ChatMessage"/> to a <see cref="ChatMessageContent"/>.</summary>
    internal static ChatMessageContent ToChatMessageContent(this ChatMessage message, Microsoft.Extensions.AI.ChatResponse? response = null)
    {
        ChatMessageContent result = new()
        {
            ModelId = response?.ModelId,
            AuthorName = message.AuthorName,
            InnerContent = response?.RawRepresentation ?? message.RawRepresentation,
            Metadata = new AdditionalPropertiesDictionary(message.AdditionalProperties ?? []) { ["Usage"] = response?.Usage },
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

    /// <summary>Converts a list of <see cref="ChatMessage"/> to a <see cref="ChatHistory"/>.</summary>
    internal static ChatHistory ToChatHistory(this IEnumerable<ChatMessage> chatMessages)
    {
        ChatHistory chatHistory = [];
        foreach (var message in chatMessages)
        {
            chatHistory.Add(message.ToChatMessageContent());
        }
        return chatHistory;
    }
}
