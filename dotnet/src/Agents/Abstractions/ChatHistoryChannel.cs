// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
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

        await foreach (var message in historyHandler.InvokeAsync(this._history, cancellationToken))
        {
            this._history.Add(message);

            yield return message;
        }
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

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatHistoryChannel"/> class.
    /// </summary>
    public ChatHistoryChannel()
    {
        this._history = new();
    }
}
