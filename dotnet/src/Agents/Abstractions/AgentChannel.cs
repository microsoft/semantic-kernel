// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Defines the communication protocol for a particular <see cref="Agent"/> type.
/// </summary>
/// <remarks>
/// An agent provides it own <see cref="AgentChannel"/> via <see cref="Agent.CreateChannelAsync"/>.
/// </remarks>
[Experimental("SKEXP0110")]
public abstract class AgentChannel
{
    /// <summary>
    /// Gets or sets the <see cref="ILogger"/> associated with the <see cref="AgentChannel"/>.
    /// </summary>
    public ILogger Logger { get; set; } = NullLogger.Instance;

    /// <summary>
    /// Responsible for providing the serialized representation of the channel.
    /// </summary>
    protected internal abstract string Serialize();

    /// <summary>
    /// Receive the conversation messages.  Used when joining a conversation and also during each agent interaction.
    /// </summary>
    /// <param name="history">The chat history at the point the channel is created.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    protected internal abstract Task ReceiveAsync(IEnumerable<ChatMessageContent> history, CancellationToken cancellationToken = default);

    /// <summary>
    /// Reset any persistent state associated with the channel.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <remarks>
    /// The channel won't be reused; rather, it will be discarded and a new one created.
    /// </remarks>
    protected internal abstract Task ResetAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Perform a discrete incremental interaction between a single <see cref="Agent"/> and <see cref="AgentChat"/>.
    /// </summary>
    /// <param name="agent">The agent actively interacting with the chat.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    /// <remarks>
    /// In the enumeration returned by this method, a message is considered visible if it is intended to be displayed to the user.
    /// Example of a non-visible message is function-content for functions that are automatically executed.
    /// </remarks>
    protected internal abstract IAsyncEnumerable<(bool IsVisible, ChatMessageContent Message)> InvokeAsync(
        Agent agent,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Perform a discrete incremental interaction between a single <see cref="Agent"/> and <see cref="AgentChat"/> with streaming results.
    /// </summary>
    /// <param name="agent">The agent actively interacting with the chat.</param>
    /// <param name="messages">The receiver for the completed messages generated</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of streaming messages.</returns>
    protected internal abstract IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(
        Agent agent,
        IList<ChatMessageContent> messages,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Retrieve the message history specific to this channel.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    protected internal abstract IAsyncEnumerable<ChatMessageContent> GetHistoryAsync(CancellationToken cancellationToken = default);
}

/// <summary>
/// Defines the communication protocol for a particular <see cref="Agent"/> type.
/// </summary>
/// <typeparam name="TAgent">The agent type for this channel.</typeparam>
/// <remarks>
/// An agent provides it own <see cref="AgentChannel"/> via <see cref="Agent.CreateChannelAsync"/>.
/// This class is a convenience upcast to an agent for <see cref="AgentChannel{TAgent}.InvokeAsync(TAgent, CancellationToken)"/>.
/// </remarks>
[Experimental("SKEXP0110")]
public abstract class AgentChannel<TAgent> : AgentChannel where TAgent : Agent
{
    /// <summary>
    /// Process a discrete incremental interaction between a single <see cref="Agent"/> and a <see cref="AgentChat"/>.
    /// </summary>
    /// <param name="agent">The agent actively interacting with the chat.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    /// <remarks>
    /// In the enumeration returned by this method, a message is considered visible if it is intended to be displayed to the user.
    /// Example of a non-visible message is function-content for functions that are automatically executed.
    /// </remarks>
    protected internal abstract IAsyncEnumerable<(bool IsVisible, ChatMessageContent Message)> InvokeAsync(
        TAgent agent,
        CancellationToken cancellationToken = default);

    /// <inheritdoc/>
    protected internal override IAsyncEnumerable<(bool IsVisible, ChatMessageContent Message)> InvokeAsync(
        Agent agent,
        CancellationToken cancellationToken = default)
    {
        if (agent.GetType() != typeof(TAgent))
        {
            throw new KernelException($"Invalid agent channel: {typeof(TAgent).Name}/{agent.GetType().Name}");
        }

        return this.InvokeAsync((TAgent)agent, cancellationToken);
    }
    /// <summary>
    /// Process a discrete incremental interaction between a single <see cref="Agent"/> and a <see cref="AgentChat"/>.
    /// </summary>
    /// <param name="agent">The agent actively interacting with the chat.</param>
    /// <param name="messages">The receiver for the completed messages generated</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    /// <remarks>
    /// In the enumeration returned by this method, a message is considered visible if it is intended to be displayed to the user.
    /// Example of a non-visible message is function-content for functions that are automatically executed.
    /// </remarks>
    protected internal abstract IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(
        TAgent agent,
        IList<ChatMessageContent> messages,
        CancellationToken cancellationToken = default);

    /// <inheritdoc/>
    protected internal override IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(
        Agent agent,
        IList<ChatMessageContent> messages,
        CancellationToken cancellationToken = default)
    {
        if (agent.GetType() != typeof(TAgent))
        {
            throw new KernelException($"Invalid agent channel: {typeof(TAgent).Name}/{agent.GetType().Name}");
        }

        return this.InvokeStreamingAsync((TAgent)agent, messages, cancellationToken);
    }
}
