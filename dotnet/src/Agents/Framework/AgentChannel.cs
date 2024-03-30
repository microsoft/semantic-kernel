// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Defines the communication protocol for a particular <see cref="Agent"/> type.
/// An agent provides it own <see cref="AgentChannel"/> via <see cref="Agent.CreateChannelAsync(CancellationToken)"/>.
/// </summary>
public abstract class AgentChannel
{
    /// <summary>
    /// Recieve the converation messages.  Used when joining a converation and also during each agent interaction..
    /// </summary>
    /// <param name="history">The nexus history at the point the channel is created.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    protected internal abstract Task RecieveAsync(IEnumerable<ChatMessageContent> history, CancellationToken cancellationToken = default);

    /// <summary>
    /// Perform a discrete incremental interaction between a single <see cref="Agent"/> and <see cref="AgentNexus"/>.
    /// </summary>
    /// <param name="agent">The agent actively interacting with the nexus.</param>
    /// <param name="input">Optional input to add to the converation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    protected internal abstract IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        Agent agent,
        ChatMessageContent? input = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Retrieve the message history specific to this channel.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    protected internal abstract IAsyncEnumerable<ChatMessageContent> GetHistoryAsync(CancellationToken cancellationToken);
}

/// <summary>
/// Defines the communication protocol for a particular <see cref="Agent"/> type.
/// An agent provides it own <see cref="AgentChannel"/> via <see cref="Agent.CreateChannelAsync(CancellationToken)"/>.
/// </summary>
/// <typeparam name="TAgent">The agent type for this channel</typeparam>
/// <remarks>
/// Convenience upcast to agent for <see cref="AgentChannel{TAgent}.InvokeAsync(TAgent, Microsoft.SemanticKernel.ChatMessageContent?, CancellationToken)"/>.
/// </remarks>
public abstract class AgentChannel<TAgent> : AgentChannel where TAgent : Agent
{
    /// <summary>
    /// Process a discrete incremental interaction between a single <see cref="Agent"/> an a <see cref="AgentNexus"/>.
    /// </summary>
    /// <param name="agent">The agent actively interacting with the nexus.</param>
    /// <param name="input">Optional user input.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    protected internal abstract IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        TAgent agent,
        ChatMessageContent? input = null,
        CancellationToken cancellationToken = default);

    /// <inheritdoc/>
    protected internal override IAsyncEnumerable<ChatMessageContent> InvokeAsync(
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
}
