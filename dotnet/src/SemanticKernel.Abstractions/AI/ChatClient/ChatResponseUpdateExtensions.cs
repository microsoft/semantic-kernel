// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.Extensions.AI;

/// <summary>Provides extension methods for <see cref="ChatResponseUpdate"/>.</summary>
internal static class ChatResponseUpdateExtensions
{
    /// <summary>Converts a <see cref="ChatResponseUpdate"/> to a <see cref="StreamingChatMessageContent"/>.</summary>
    /// <remarks>This conversion should not be necessary once SK eventually adopts the shared content types.</remarks>
    internal static StreamingChatMessageContent ToStreamingChatMessageContent(this ChatResponseUpdate update)
    {
        StreamingChatMessageContent content = new(
            update.Role is not null ? new AuthorRole(update.Role.Value.Value) : null,
            null)
        {
            InnerContent = update.RawRepresentation,
            Metadata = update.AdditionalProperties,
            ModelId = update.ModelId
        };

        foreach (AIContent item in update.Contents)
        {
            StreamingKernelContent? resultContent =
                item is Microsoft.Extensions.AI.TextContent tc ? new Microsoft.SemanticKernel.StreamingTextContent(tc.Text) :
                item is Microsoft.Extensions.AI.FunctionCallContent fcc ?
                    new Microsoft.SemanticKernel.StreamingFunctionCallUpdateContent(fcc.CallId, fcc.Name, fcc.Arguments is not null ?
                        JsonSerializer.Serialize(fcc.Arguments!, AbstractionsJsonContext.Default.IDictionaryStringObject!) :
                        null) :
                null;

            if (resultContent is not null)
            {
                resultContent.InnerContent = item.RawRepresentation;
                resultContent.ModelId = update.ModelId;
                content.Items.Add(resultContent);
            }

            if (item is Microsoft.Extensions.AI.UsageContent uc)
            {
                content.Metadata = new Dictionary<string, object?>(update.AdditionalProperties ?? [])
                {
                    ["Usage"] = uc
                };
            }
        }

        return content;
    }
}
