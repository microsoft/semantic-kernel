// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.Extensions;

/// <summary>
/// Extension methods for <see cref="ChatMessageContent"/>
/// </summary>
public static class ChatHistoryExtensions
{
    /// <summary>
    /// Enumeration of chat-history in descending order.
    /// </summary>
    /// <param name="history">The chat-history</param>
    public static IEnumerable<ChatMessageContent> ToDescending(this ChatHistory history)
    {
        for (int index = history.Count; index > 0; --index)
        {
            yield return history[index - 1];
        }
    }

    /// <summary>
    /// Asynchronous enumeration of chat-history in descending order.
    /// </summary>
    /// <param name="history">The chat-history</param>
    public static IAsyncEnumerable<ChatMessageContent> ToDescendingAsync(this ChatHistory history)
    {
        return history.ToDescending().ToAsyncEnumerable();
    }
}
