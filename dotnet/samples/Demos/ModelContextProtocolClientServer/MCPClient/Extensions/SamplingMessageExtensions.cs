// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel;
using ModelContextProtocol.Protocol.Types;

namespace MCPClient;

/// <summary>
/// Extension methods for <see cref="SamplingMessage"/>.
/// </summary>
public static class SamplingMessageExtensions
{
    /// <summary>
    /// Converts a collection of <see cref="SamplingMessage"/> to a list of <see cref="ChatMessageContent"/>.
    /// </summary>
    /// <param name="samplingMessages">The collection of <see cref="SamplingMessage"/> to convert.</param>
    /// <returns>The corresponding list of <see cref="ChatMessageContent"/>.</returns>
    public static List<ChatMessageContent> ToChatMessageContents(this IEnumerable<SamplingMessage> samplingMessages)
    {
        return [.. samplingMessages.Select(ToChatMessageContent)];
    }

    /// <summary>
    /// Converts a <see cref="SamplingMessage"/> to a <see cref="ChatMessageContent"/>.
    /// </summary>
    /// <param name="message">The <see cref="SamplingMessage"/> to convert.</param>
    /// <returns>The corresponding <see cref="ChatMessageContent"/>.</returns>
    public static ChatMessageContent ToChatMessageContent(this SamplingMessage message)
    {
        return new ChatMessageContent(role: message.Role.ToAuthorRole(), items: [message.Content.ToKernelContent()]);
    }
}
