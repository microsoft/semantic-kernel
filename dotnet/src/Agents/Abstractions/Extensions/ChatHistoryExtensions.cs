// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.Extensions;

/// <summary>
/// Provides extension methods for <see cref="ChatMessageContent"/>.
/// </summary>
public static class ChatHistoryExtensions
{
    /// <summary>
    /// Enumerates a chat history in descending order.
    /// </summary>
    /// <param name="history">The chat history to sort.</param>
    public static IEnumerable<ChatMessageContent> ToDescending(this ChatHistory history)
    {
        for (int index = history.Count; index > 0; --index)
        {
            yield return history[index - 1];
        }
    }

    /// <summary>
    /// Enumerates a history in descending order asynchronously.
    /// </summary>
    /// <param name="history">The chat history to sort.</param>
    public static async IAsyncEnumerable<ChatMessageContent> ToDescendingAsync(this ChatHistory history)
    {
        for (int index = history.Count; index > 0; --index)
        {
            yield return history[index - 1];
        }
    }
}
