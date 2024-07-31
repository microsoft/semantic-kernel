// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Extensions;
using Microsoft.SemanticKernel.Agents.History;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// A <see cref="AgentChannel"/> specialization for that acts upon a <see cref="IChatHistoryHandler"/>.
/// </summary>
public sealed class ChatHistoryChannel : AgentChannel
{
    private readonly ChatHistory _history;
    private readonly Dictionary<int, ChatHistory> _reducedHistory = [];
    private readonly Dictionary<string, int> _reductionMap = [];

    /// <inheritdoc/>
    protected override async IAsyncEnumerable<(bool IsVisible, ChatMessageContent Message)> InvokeAsync(
        Agent agent,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        if (agent is not IChatHistoryHandler historyHandler)
        {
            throw new KernelException($"Invalid channel binding for agent: {agent.Id} ({agent.GetType().FullName})");
        }

        // Pre-process history reduction.
        ChatHistory reducedHistory = await this.GetReducedHistoryAsync(agent.Id, historyHandler.HistoryReducer, cancellationToken).ConfigureAwait(false);

        // Capture the current message count to evaluate history mutation.
        int messageCount = reducedHistory.Count;
        HashSet<ChatMessageContent> mutatedHistory = [];

        // Utilize a queue as a "read-ahead" cache to evaluate message sequencing (i.e., which message is final).
        Queue<ChatMessageContent> messageQueue = [];

        ChatMessageContent? yieldMessage = null;
        await foreach (ChatMessageContent responseMessage in historyHandler.InvokeAsync(reducedHistory, cancellationToken).ConfigureAwait(false))
        {
            // Capture all messages that have been included in the mutated the history.
            for (int messageIndex = messageCount; messageIndex < reducedHistory.Count; messageIndex++)
            {
                ChatMessageContent mutatedMessage = reducedHistory[messageIndex];
                mutatedHistory.Add(mutatedMessage);
                messageQueue.Enqueue(mutatedMessage);
            }

            // Update the message count pointer to reflect the current history.
            messageCount = reducedHistory.Count;

            // Avoid duplicating any message included in the mutated history and also returned by the enumeration result.
            if (!mutatedHistory.Contains(responseMessage))
            {
                reducedHistory.Add(responseMessage);
                messageQueue.Enqueue(responseMessage);
            }

            // Dequeue the next message to yield.
            yieldMessage = messageQueue.Dequeue();
            yield return (IsMessageVisible(yieldMessage), yieldMessage);
        }

        // Dequeue any remaining messages to yield.
        while (messageQueue.Count > 0)
        {
            yieldMessage = messageQueue.Dequeue();

            yield return (IsMessageVisible(yieldMessage), yieldMessage);
        }

        // Function content not visible, unless result is the final message.
        bool IsMessageVisible(ChatMessageContent message) =>
            (!message.Items.Any(i => i is FunctionCallContent || i is FunctionResultContent) ||
              messageQueue.Count == 0);
    }

    /// <inheritdoc/>
    protected override Task ReceiveAsync(IEnumerable<ChatMessageContent> history, CancellationToken cancellationToken)
    {
        this._history.AddRange(history);

        return Task.CompletedTask;
    }

    /// <inheritdoc/>
    protected override IAsyncEnumerable<ChatMessageContent> GetHistoryAsync(CancellationToken cancellationToken)
    {
        return this._history.ToDescendingAsync();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatHistoryChannel"/> class.
    /// </summary>
    public ChatHistoryChannel()
    {
        this._history = [];
    }

    private async Task<ChatHistory> GetReducedHistoryAsync(string agentId, IChatHistoryReducer? reducer, CancellationToken cancellationToken)
    {
        if (reducer == null)
        {
            return this._history;
        }

        int reducerKey = reducer.GetHashCode();

        if (!this._reducedHistory.TryGetValue(reducerKey, out ChatHistory? history))
        {
            history = this._history;
        }

        (bool isReduced, ChatHistory reducedHistory) = await history.ReduceAsync(reducer, cancellationToken).ConfigureAwait(false);

        if (isReduced)
        {
            this._reducedHistory[reducerKey] = reducedHistory;
            this._reductionMap[agentId] = reducerKey;
        }

        return reducedHistory;
    }
}
