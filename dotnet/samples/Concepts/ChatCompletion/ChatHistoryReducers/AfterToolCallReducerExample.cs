// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace ChatCompletion;

/// <summary>
/// Example reducer that demonstrates usage of the AfterToolCallResponseReceived trigger.
/// This reducer keeps only the last N messages and triggers after each tool call response.
/// </summary>
/// <remarks>
/// This is useful for long-running agentic workflows where multiple tool calls
/// can cause the chat history to exceed token limits.
/// </remarks>
public sealed class AfterToolCallReducerExample : ChatHistoryReducerBase
{
    private readonly int _maxMessages;

    /// <summary>
    /// Creates a new instance of <see cref="AfterToolCallReducerExample"/>.
    /// </summary>
    /// <param name="maxMessages">Maximum number of messages to keep in history.</param>
    public AfterToolCallReducerExample(int maxMessages)
        : base(ChatReducerTriggerEvent.AfterToolCallResponseReceived)
    {
        this._maxMessages = maxMessages;
    }

    /// <inheritdoc/>
    public override Task<IEnumerable<ChatMessageContent>?> ReduceAsync(
        IReadOnlyList<ChatMessageContent> chatHistory,
        CancellationToken cancellationToken = default)
    {
        // If history is within limits, no reduction needed
        if (chatHistory.Count <= this._maxMessages)
        {
            return Task.FromResult<IEnumerable<ChatMessageContent>?>(null);
        }

        // Keep only the last N messages
        var reducedHistory = chatHistory.Skip(chatHistory.Count - this._maxMessages).ToList();
        return Task.FromResult<IEnumerable<ChatMessageContent>?>(reducedHistory);
    }
}
