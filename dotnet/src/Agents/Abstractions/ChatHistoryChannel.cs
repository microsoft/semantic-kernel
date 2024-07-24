// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Extensions;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// A <see cref="AgentChannel"/> specialization for that acts upon a <see cref="IChatHistoryHandler"/>.
/// </summary>
public class ChatHistoryChannel : AgentChannel
{
    /// <summary>
    /// %%%
    /// </summary>
    protected ChatHistory History { get; }

    /// <inheritdoc/>
    protected internal override IAsyncEnumerable<(bool IsVisible, ChatMessageContent Message)> InvokeAsync(
        Agent agent,
        CancellationToken cancellationToken = default)
        => this.InvokeAsync(agent, this.History, cancellationToken);

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="agent"></param>
    /// <param name="history"></param>
    /// <param name="cancellationToken"></param>
    protected internal async IAsyncEnumerable<(bool IsVisible, ChatMessageContent Message)> InvokeAsync(
        Agent agent,
        ChatHistory history,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        if (agent is not IChatHistoryHandler historyHandler)
        {
            throw new KernelException($"Invalid channel binding for agent: {agent.Id} ({agent.GetType().FullName})");
        }

        // Capture the current message count to evaluate history mutation.
        int messageCount = this.History.Count;
        HashSet<ChatMessageContent> mutatedHistory = [];

        // Utilize a queue as a "read-ahead" cache to evaluate message sequencing (i.e., which message is final).
        Queue<ChatMessageContent> messageQueue = [];

        ChatMessageContent? yieldMessage = null;
        await foreach (ChatMessageContent responseMessage in historyHandler.InvokeAsync(this.History, cancellationToken).ConfigureAwait(false))
        {
            // Capture all messages that have been included in the mutated the history.
            for (int messageIndex = messageCount; messageIndex < this.History.Count; messageIndex++)
            {
                ChatMessageContent mutatedMessage = this.History[messageIndex];
                mutatedHistory.Add(mutatedMessage);
                messageQueue.Enqueue(mutatedMessage);
            }

            // Update the message count pointer to reflect the current history.
            messageCount = this.History.Count;

            // Avoid duplicating any message included in the mutated history and also returned by the enumeration result.
            if (!mutatedHistory.Contains(responseMessage))
            {
                this.History.Add(responseMessage);
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
    protected internal sealed override Task ReceiveAsync(IEnumerable<ChatMessageContent> history, CancellationToken cancellationToken)
    {
        this.History.AddRange(history);

        return Task.CompletedTask;
    }

    /// <inheritdoc/>
    protected internal sealed override IAsyncEnumerable<ChatMessageContent> GetHistoryAsync(CancellationToken cancellationToken)
    {
        return this.History.ToDescendingAsync();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatHistoryChannel"/> class.
    /// </summary>
    public ChatHistoryChannel()
    {
        this.History = [];
    }
}
