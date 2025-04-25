// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Text.Json;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Extensions;

/// <summary>
/// Extension methods for <see cref="ChatMessageContent"/>.
/// </summary>
public static class ChatMessageContentExtensions
{
    /// <summary>
    /// Convert message content to a specific type.
    /// </summary>
    /// <remarks>
    /// This is used for structured output where an extremely strong expectation exists
    /// around the expected message structure.
    /// </remarks>
    internal static TValue GetValue<TValue>(this ChatMessageContent message) where TValue : class
    {
        if (string.IsNullOrWhiteSpace(message.Content))
        {
            throw new InvalidDataException("Message content is empty.");
        }

        return
            JsonSerializer.Deserialize<TValue>(message.Content) ??
            throw new InvalidDataException($"Message content does not align with requested type: {typeof(TValue).Name}.");
    }
}
