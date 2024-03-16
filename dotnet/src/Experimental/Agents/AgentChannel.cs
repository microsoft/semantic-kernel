// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Agents.Exceptions;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Manages communication protocol for a particular <see cref="Agent"/> implementation.
/// </summary>
/// <typeparam name="TAgent">The agent type for this channel</typeparam>
public abstract class AgentChannel<TAgent> : AgentChannel where TAgent : Agent
{
    /// <inheritdoc/>
    public override IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        Agent agent,
        ChatMessageContent? input = null,
        CancellationToken cancellationToken = default)
    {
        if (agent is not TAgent castAgent)
        {
            throw new AgentException($"Invalid agent channel: {typeof(TAgent).Name}/{agent.GetType().Name}");
        }

        return this.InvokeAsync(castAgent, input, cancellationToken);
    }

    /// <summary>
    /// Process a discrete incremental interaction between a single <see cref="Agent"/> an a <see cref="AgentNexus"/>.
    /// </summary>
    /// <param name="agent">The agent actively interacting with the nexus.</param>
    /// <param name="input">Optional user input.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    protected abstract IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        TAgent agent,
        ChatMessageContent? input = null,
        CancellationToken cancellationToken = default);
}

/// <summary>
/// Manages communication protocol for a particular <see cref="Agent"/> implementation.
/// </summary>
public abstract class AgentChannel
{
    /// <summary>
    /// Recieve the nexus history.  Used when joining a nexus and also to remain in sync.
    /// </summary>
    /// <param name="history">The nexus history at the point the channel is created.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public abstract Task RecieveAsync(IEnumerable<ChatMessageContent> history, CancellationToken cancellationToken = default);

    /// <summary>
    /// Process a discrete incremental interaction between a single <see cref="Agent"/> an a <see cref="AgentNexus"/>.
    /// </summary>
    /// <param name="agent">The agent actively interacting with the nexus.</param>
    /// <param name="input">Optional user input.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    public abstract IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        Agent agent,
        ChatMessageContent? input = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Retrieve the message history specific to this channel.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    public abstract IAsyncEnumerable<ChatMessageContent> GetHistoryAsync(CancellationToken cancellationToken);
}
