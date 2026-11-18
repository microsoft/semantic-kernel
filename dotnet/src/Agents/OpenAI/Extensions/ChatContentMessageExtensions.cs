// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using OpenAI.Responses;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Convenience extensions for converting <see cref="ChatMessageContent"/>.
/// </summary>
public static class ChatContentMessageExtensions
{
    /// <summary>
    /// Converts a <see cref="ChatMessageContent"/> instance to a <see cref="ResponseItem"/>.
    /// </summary>
    /// <param name="message">The chat message content to convert.</param>
    /// <returns>A <see cref="ResponseItem"/> instance.</returns>
    public static ResponseItem ToResponseItem(this ChatMessageContent message)
    {
        var items = message.Items;
        IEnumerable<ResponseContentPart> contentParts = items.Select(item => item.ToResponseContentPart());
        return message.Role.Label.ToUpperInvariant() switch
        {
            "SYSTEM" => ResponseItem.CreateSystemMessageItem(contentParts),
            "USER" => ResponseItem.CreateUserMessageItem(contentParts),
            "DEVELOPER" => ResponseItem.CreateDeveloperMessageItem(contentParts),
            "ASSISTANT" => ResponseItem.CreateAssistantMessageItem(contentParts),
            _ => throw new NotSupportedException($"Unsupported role {message.Role.Label}. Only system, user, developer or assistant roles are allowed."),
        };
    }
}
