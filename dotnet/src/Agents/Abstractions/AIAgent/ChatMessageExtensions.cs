// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel.ChatCompletion;
using MEAI = Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Agents;

#pragma warning disable SKEXP0001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

internal static class ChatMessageExtensions
{
    /// <summary>Converts a <see cref="ChatMessage"/> to a <see cref="ChatMessageContent"/>.</summary>
    internal static ChatMessageContent ToChatMessageContent(this ChatMessage message, ChatResponse? response = null)
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
                MEAI.TextContent tc => new TextContent(tc.Text),
                DataContent dc when dc.HasTopLevelMediaType("image") => new ImageContent(dc.Uri),
                UriContent uc when uc.HasTopLevelMediaType("image") => new ImageContent(uc.Uri),
                DataContent dc when dc.HasTopLevelMediaType("audio") => new AudioContent(dc.Uri),
                UriContent uc when uc.HasTopLevelMediaType("audio") => new AudioContent(uc.Uri),
                DataContent dc => new BinaryContent(dc.Uri),
                UriContent uc => new BinaryContent(uc.Uri),
                MEAI.FunctionCallContent fcc => new FunctionCallContent(
                    functionName: fcc.Name,
                    id: fcc.CallId,
                    arguments: fcc.Arguments is not null ? new(fcc.Arguments) : null),
                MEAI.FunctionResultContent frc => new FunctionResultContent(
                    functionName: GetFunctionCallContent(frc.CallId)?.Name,
                    callId: frc.CallId,
                    result: frc.Result),
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

        MEAI.FunctionCallContent? GetFunctionCallContent(string callId)
            => response?.Messages
                .Select(m => m.Contents
                .FirstOrDefault(c => c is MEAI.FunctionCallContent fcc && fcc.CallId == callId) as MEAI.FunctionCallContent)
                    .FirstOrDefault(fcc => fcc is not null);
    }
}
