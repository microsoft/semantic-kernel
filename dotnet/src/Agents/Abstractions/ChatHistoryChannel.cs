// Copyright (c) Microsoft. All rights reserved.
using System;
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
    private readonly ChatHistory _history;

    /// <inheritdoc/>
    protected internal sealed override async IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        Agent agent,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        if (agent is not IChatHistoryHandler historyHandler)
        {
            throw new KernelException($"Invalid channel binding for agent: {agent.Id} ({agent.GetType().FullName})");
        }

        bool didPostFunctionResult;
        do
        {
            didPostFunctionResult = false; // Clear on each iteration

            int messageCount = this._history.Count;
            HashSet<ChatMessageContent> mutatedHistory = [];

            Queue<ChatMessageContent> messageQueue = [];
            ChatMessageContent? yieldMessage = null;
            await foreach (ChatMessageContent responseMessage in historyHandler.InvokeAsync(this._history, cancellationToken).ConfigureAwait(false))
            {
                for (int messageIndex = messageCount; messageIndex < this._history.Count; messageIndex++)
                {
                    ChatMessageContent mutatedMessage = this._history[messageIndex];
                    mutatedHistory.Add(mutatedMessage);
                    messageQueue.Enqueue(mutatedMessage);
                }

                if (!mutatedHistory.Contains(responseMessage))
                {
                    this._history.Add(responseMessage);
                    messageQueue.Enqueue(responseMessage);
                }

                yieldMessage = messageQueue.Dequeue();
                yield return yieldMessage;
            }

            while (messageQueue.Count > 0)
            {
                yieldMessage = messageQueue.Dequeue();

                yield return yieldMessage;
            }

            if (yieldMessage != null)
            {
                // Process manual Function Invocation
                if (yieldMessage.Items.Any(i => i is FunctionCallContent))
                {
                    ChatMessageContent functionResultContent = await this.OnManualFunctionCallAsync(agent, yieldMessage, cancellationToken).ConfigureAwait(false);
                    yield return functionResultContent;
                    didPostFunctionResult = true;
                }

                // Autocomplete Function Termination, et al...
                if (yieldMessage.Items.Any(i => i is FunctionResultContent))
                {
                    yield return await this.OnTerminatedFunctionResultAsync(agent, yieldMessage, cancellationToken).ConfigureAwait(false);
                }
            }
        }
        while (didPostFunctionResult);
    }

    /// <inheritdoc/>
    protected internal sealed override Task ReceiveAsync(IEnumerable<ChatMessageContent> history, CancellationToken cancellationToken)
    {
        this._history.AddRange(history);

        return Task.CompletedTask;
    }

    /// <inheritdoc/>
    protected internal sealed override IAsyncEnumerable<ChatMessageContent> GetHistoryAsync(CancellationToken cancellationToken)
    {
        return this._history.ToDescendingAsync();
    }

    /// <inheritdoc/>
    protected internal override Task CaptureFunctionResultAsync(ChatMessageContent functionResultsMessage, CancellationToken cancellationToken = default)
    {
        this._history.Add(functionResultsMessage);

        return Task.CompletedTask;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatHistoryChannel"/> class.
    /// </summary>
    public ChatHistoryChannel()
    {
        this._history = [];
    }
}
