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
    /// Asynchronous enumeration of chat-history in descending order.
    /// </summary>
    /// <param name="history">The chat-history</param>
    public static IAsyncEnumerable<ChatMessageContent> ToDescending(this ChatHistory history)
    {
        return Reverse().ToAsyncEnumerable();

        IEnumerable<ChatMessageContent> Reverse()
        {
            for (int index = history.Count - 1; index >= 0; --index)
            {
                yield return history[index];
            }
        }
    }
}
