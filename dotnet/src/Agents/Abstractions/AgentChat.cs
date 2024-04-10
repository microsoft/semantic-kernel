// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Extensions;
using Microsoft.SemanticKernel.Agents.Internal;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Point of interaction for one or more agents.
/// </summary>
/// <remarks>
/// Any <see cref="AgentChat" /> instance does not support concurrent invocation and
/// will throw exception if concurrent activity is attempted for:
/// - <see cref="AddChatMessage"/>
/// - <see cref="AddChatMessages"/>
/// - <see cref="GetChatMessagesAsync"/>
/// - <see cref="InvokeAgentAsync"/>
/// </remarks>
public abstract class AgentChat
{
    private readonly BroadcastQueue _broadcastQueue;
    private readonly Dictionary<string, AgentChannel> _agentChannels; // Map channel hash to channel: one entry per channel.
    private readonly Dictionary<Agent, string> _channelMap; // Map agent to its channel-hash: one entry per agent.

    private int _isActive;

    /// <summary>
    /// Indicates if a chat operation is active.  This includes:
    /// - <see cref="AddChatMessage"/>
    /// - <see cref="AddChatMessages"/>
    /// - <see cref="GetChatMessagesAsync"/>
    /// - <see cref="InvokeAgentAsync"/>
    /// </summary>
    public bool IsActive => Interlocked.CompareExchange(ref this._isActive, 1, 1) > 0;

    /// <summary>
    /// Exposes the internal history to subclasses.
    /// </summary>
    protected ChatHistory History { get; }

    /// <summary>
    /// Retrieve the message history, either the primary history or
    /// an agent specific version.
    /// </summary>
    /// <param name="agent">An optional agent, if requesting an agent history.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The message history</returns>
    public async IAsyncEnumerable<ChatMessageContent> GetChatMessagesAsync(
        Agent? agent = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this.ThrowIfActive();

        try
        {
            IAsyncEnumerable<ChatMessageContent>? messages = null;

            if (agent == null)
            {
                // Provide primary history
                messages = this.History.ToDescendingAsync();
            }
            else // else provide channel specific history
            {
                // Retrieve the requested channel, if exists, and block until channel is synchronized.
                string channelKey = this.GetAgentHash(agent);
                AgentChannel? channel = await this.SynchronizeChannelAsync(channelKey, cancellationToken).ConfigureAwait(false);
                if (channel != null)
                {
                    messages = channel.GetHistoryAsync(cancellationToken);
                }
            }

            if (messages != null)
            {
                await foreach (ChatMessageContent message in messages)
                {
                    yield return message;
                }
            }
        }
        finally
        {
            this.ClearActivitySignal(); // $$$ RACE ???
        }
    }

    /// <summary>
    /// Append a message to the conversation.  Adding a message while an agent
    /// is active is not allowed.
    /// </summary>
    /// <param name="message">A of non-system messages with which to append to the conversation.</param>
    /// <remarks>
    /// Adding a message to the conversation requires any active <see cref="AgentChannel"/> remains
    /// synchronized, so the message is broadcast to all channels.
    /// </remarks>
    /// <throws>KernelException if a system message is present, without taking any other action</throws>
    public void AddChatMessage(ChatMessageContent message)
    {
        this.AddChatMessages(new[] { message });
    }

    /// <summary>
    /// Append messages to the conversation.  Adding messages while an agent
    /// is active is not allowed.
    /// </summary>
    /// <param name="messages">Set of non-system messages with which to append to the conversation.</param>
    /// <remarks>
    /// Adding messages to the conversation requires any active <see cref="AgentChannel"/> remains
    /// synchronized, so the messages are broadcast to all channels.
    /// </remarks>
    /// <throws>KernelException if a system message is present, without taking any other action</throws>
    /// <throws>KernelException chat has current activity.</throws>
    /// <remarks>
    /// </remarks>
    public void AddChatMessages(IReadOnlyList<ChatMessageContent> messages)
    {
        this.ThrowIfActive();

        for (int index = 0; index < messages.Count; ++index)
        {
            if (messages[index].Role == AuthorRole.System)
            {
                throw new KernelException($"History does not support messages with Role of {AuthorRole.System}.");
            }
        }

        try
        {
            // Append to chat history
            this.History.AddRange(messages);

            // Broadcast message to other channels (in parallel)
            // Note: Able to queue messages without synchronizing channels.
            var channelRefs = this._agentChannels.Select(kvp => new ChannelReference(kvp.Value, kvp.Key));
            this._broadcastQueue.Enqueue(channelRefs, messages);
        }
        finally
        {
            this.ClearActivitySignal();
        }
    }

    /// <summary>
    /// Process a discrete incremental interaction between a single <see cref="Agent"/> an a <see cref="AgentChat"/>.
    /// </summary>
    /// <param name="agent">The agent actively interacting with the chat.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    protected async IAsyncEnumerable<ChatMessageContent> InvokeAgentAsync(
        Agent agent,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this.ThrowIfActive();

        try
        {
            // Get or create the required channel and block until channel is synchronized.
            // Will throw exception when propagating a processing failure.
            AgentChannel channel = await GetOrCreateChannelAsync().ConfigureAwait(false);

            // Invoke agent & process response
            List<ChatMessageContent> messages = new();
            await foreach (var message in channel.InvokeAsync(agent, cancellationToken).ConfigureAwait(false))
            {
                // Add to primary history
                this.History.Add(message);
                messages.Add(message);

                // Yield message to caller
                yield return message;
            }

            // Broadcast message to other channels (in parallel)
            // Note: Able to queue messages without synchronizing channels.
            var channelRefs =
                this._agentChannels
                    .Where(kvp => kvp.Value != channel)
                    .Select(kvp => new ChannelReference(kvp.Value, kvp.Key));
            this._broadcastQueue.Enqueue(channelRefs, messages);
        }
        finally
        {
            this.ClearActivitySignal();
        }

        async Task<AgentChannel> GetOrCreateChannelAsync()
        {
            string channelKey = this.GetAgentHash(agent);
            AgentChannel channel = await this.SynchronizeChannelAsync(channelKey, cancellationToken).ConfigureAwait(false);
            if (channel == null)
            {
                channel = await agent.CreateChannelAsync(cancellationToken).ConfigureAwait(false);
                this._agentChannels.Add(channelKey, channel);

                if (this.History.Count > 0)
                {
                    await channel.ReceiveAsync(this.History, cancellationToken).ConfigureAwait(false);
                }

            }

            return channel;
        }
    }

    /// <summary>
    /// Clear activity marker.
    /// </summary>
    private void ClearActivitySignal()
    {
        Interlocked.Exchange(ref this._isActive, 0);
    }

    /// <summary>
    /// Test to ensure chat is not concurrently active and throw exception if it is.
    /// If not, activity is signaled.
    /// </summary>
    private void ThrowIfActive()
    {
        int wasActive = Interlocked.CompareExchange(ref this._isActive, 1, 0);
        if (wasActive > 0)
        {
            throw new KernelException("Unable to proceed while another agent is active.");
        }
    }

    private string GetAgentHash(Agent agent)
    {
        if (!this._channelMap.TryGetValue(agent, out var hash))
        {
            hash = KeyEncoder.GenerateHash(agent.GetChannelKeys());

            // Ok if already present: same agent always produces the same hash
            this._channelMap.Add(agent, hash);
        }

        return hash;
    }

    private async Task<AgentChannel> SynchronizeChannelAsync(string channelKey, CancellationToken cancellationToken)
    {
        if (this._agentChannels.TryGetValue(channelKey, out AgentChannel channel))
        {
            await this._broadcastQueue.EnsureSynchronizedAsync(
                new ChannelReference(channel, channelKey), cancellationToken).ConfigureAwait(false);
        }

        return channel;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentChat"/> class.
    /// </summary>
    protected AgentChat()
    {
        this._agentChannels = new();
        this._broadcastQueue = new();
        this._channelMap = new();
        this.History = new();
    }
}
