// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using Azure.AI.Agents.Persistent;
using Microsoft.SemanticKernel.Agents.AzureAI.Internal;

namespace Microsoft.SemanticKernel.Agents.AzureAI;

/// <summary>
/// Exposes patterns for creating and managing agent threads.
/// </summary>
/// <remarks>
/// This class supports translation of <see cref="ChatMessageContent"/> from native models.
/// </remarks>
public static class AzureAIThreadMessageFactory
{
    /// <summary>
    /// Translates <see cref="ChatMessageContent"/> to <see cref="ThreadMessageOptions"/> for thread creation.
    /// </summary>
    public static IEnumerable<ThreadMessageOptions> Translate(IEnumerable<ChatMessageContent> messages)
    {
        return AgentMessageFactory.GetThreadMessages(messages);
    }
}
