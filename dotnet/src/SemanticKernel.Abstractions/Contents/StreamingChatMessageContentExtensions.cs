// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel;

/// <summary>Provides extension methods for <see cref="StreamingChatMessageContent"/>.</summary>
internal static class StreamingChatMessageContentExtensions
{
    /// <summary>Converts a <see cref="StreamingChatMessageContent"/> to a <see cref="ChatResponseUpdate"/>.</summary>
    /// <remarks>This conversion should not be necessary once SK eventually adopts the shared content types.</remarks>
    internal static ChatResponseUpdate ToChatResponseUpdate(this StreamingChatMessageContent content)
    {
        ChatResponseUpdate update = new()
        {
            AdditionalProperties = content.Metadata is not null ? new AdditionalPropertiesDictionary(content.Metadata) : null,
            AuthorName = content.AuthorName,
            ModelId = content.ModelId,
            RawRepresentation = content.InnerContent,
            Role = content.Role is not null ? new ChatRole(content.Role.Value.Label) : null,
        };

        foreach (var item in content.Items)
        {
            AIContent? aiContent = null;
            switch (item)
            {
                case Microsoft.SemanticKernel.StreamingTextContent tc:
                    aiContent = new Microsoft.Extensions.AI.TextContent(tc.Text);
                    break;

                case Microsoft.SemanticKernel.StreamingFunctionCallUpdateContent fcc:
                    aiContent = new Microsoft.Extensions.AI.FunctionCallContent(
                        fcc.CallId ?? string.Empty,
                        fcc.Name ?? string.Empty,
                        !string.IsNullOrWhiteSpace(fcc.Arguments) ? JsonSerializer.Deserialize<IDictionary<string, object?>>(fcc.Arguments, AbstractionsJsonContext.Default.IDictionaryStringObject!) : null);
                    break;
            }

            if (aiContent is not null)
            {
                aiContent.RawRepresentation = content;

                update.Contents.Add(aiContent);
            }
        }

        return update;
    }
}
