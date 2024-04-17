// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Extensions;
using Microsoft.SemanticKernel.Agents.Filters;
using Microsoft.SemanticKernel.Agents.Internal;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Point of interaction for one or more agents.
/// </summary>
public abstract class AgentChat
{
    private readonly BroadcastQueue _broadcastQueue;
    private readonly Dictionary<string, AgentChannel> _agentChannels;
    private readonly Dictionary<Agent, string> _channelMap;
    private readonly ChatHistory _history;

    private int _isActive;
    private List<IAgentChatFilter>? _filters;

    /// <summary>
    /// %%%
    /// </summary>
    public IList<IAgentChatFilter> Filters =>
        this._filters ??
            Interlocked.CompareExchange(ref this._filters, [], null) ??
                this._filters;

    /// <summary>
    /// Retrieve the message history, either the primary history or
    /// an agent specific version.
    /// </summary>
    /// <param name="agent">An optional agent, if requesting an agent history.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The message history</returns>
    public IAsyncEnumerable<ChatMessageContent> GetChatMessagesAsync(Agent? agent = null, CancellationToken cancellationToken = default)
    {
        if (agent == null)
        {
            return this._history.ToDescendingAsync();
        }

        var channelKey = this.GetAgentHash(agent);
        if (!this._agentChannels.TryGetValue(channelKey, out var channel))
        {
            return Array.Empty<ChatMessageContent>().ToAsyncEnumerable();
        }

        return channel.GetHistoryAsync(cancellationToken);
    }

    /// <summary>
    /// Append messages to the conversation.
    /// </summary>
    /// <param name="message">Set of non-system messages with which to seed the conversation.</param>
    /// <remarks>
    /// Adding a message to the conversation requires any active <see cref="AgentChannel"/> remains
    /// synchronized, so the message is broadcast to all channels.
    /// </remarks>
    /// <throws>KernelException if a system message is present, without taking any other action</throws>
    public void AddChatMessage(ChatMessageContent message)
    {
        this.AddChatMessages([message]);
    }

    /// <summary>
    /// Append messages to the conversation.
    /// </summary>
    /// <param name="messages">Set of non-system messages with which to seed the conversation.</param>
    /// <remarks>
    /// Adding messages to the conversation requires any active <see cref="AgentChannel"/> remains
    /// synchronized, so the messages are broadcast to all channels.
    /// </remarks>
    /// <throws>KernelException if a system message is present, without taking any other action</throws>
    public void AddChatMessages(IReadOnlyList<ChatMessageContent> messages)
    {
        for (int index = 0; index < messages.Count; ++index)
        {
            if (messages[index].Role == AuthorRole.System)
            {
                throw new KernelException($"History does not support messages with Role of {AuthorRole.System}.");
            }
        }

        // Append to chat history
        this._history.AddRange(messages);

        // Broadcast message to other channels (in parallel)
        var channelRefs = this._agentChannels.Select(kvp => new ChannelReference(kvp.Value, kvp.Key));
        this._broadcastQueue.Enqueue(channelRefs, messages);
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
        // Verify only a single operation is active
        int wasActive = Interlocked.CompareExchange(ref this._isActive, 1, 0);
        if (wasActive > 0)
        {
            throw new KernelException("Unable to proceed while another agent is active.");
        }

        try
        {
            this.OnAgentInvokingFilter(agent, this._history);

            // Manifest the required channel.  Will throw if channel not in sync.
            var channel = await this.GetChannelAsync(agent, cancellationToken).ConfigureAwait(false);

            // Invoke agent & process response
            List<ChatMessageContent> messages = [];
            await foreach (var message in channel.InvokeAsync(agent, cancellationToken).ConfigureAwait(false))
            {
                // Invoke filter
                AgentChatFilterInvokedContext? context = this.OnAgentInvokedFilter(agent, this._history, message);

                if (context?.SuppressMessage ?? false)
                {
                    // Suppress message processing
                    continue;
                }

                // Add to primary history
                this._history.Add(message);
                messages.Add(message);

                // Yield message to caller
                yield return message;
            }

            // Broadcast message to other channels (in parallel)
            var channelRefs =
                this._agentChannels
                    .Where(kvp => kvp.Value != channel)
                    .Select(kvp => new ChannelReference(kvp.Value, kvp.Key));
            this._broadcastQueue.Enqueue(channelRefs, messages);
        }
        finally
        {
            Interlocked.Exchange(ref this._isActive, 0);
        }
    }

    private async Task<AgentChannel> GetChannelAsync(Agent agent, CancellationToken cancellationToken)
    {
        var channelKey = this.GetAgentHash(agent);

        if (this._agentChannels.TryGetValue(channelKey, out var channel))
        {
            await this._broadcastQueue.EnsureSynchronizedAsync(new ChannelReference(channel, channelKey)).ConfigureAwait(false);
        }
        else
        {
            channel = await agent.CreateChannelAsync(cancellationToken).ConfigureAwait(false);

            if (this._history.Count > 0)
            {
                await channel.ReceiveAsync(this._history, cancellationToken).ConfigureAwait(false);
            }

            this._agentChannels.Add(channelKey, channel);
        }

        return channel;
    }

    private string GetAgentHash(Agent agent)
    {
        if (this._channelMap.TryGetValue(agent, out var hash))
        {
            return hash;
        }

        hash = KeyEncoder.GenerateHash(agent.GetChannelKeys());

        this._channelMap.Add(agent, hash);

        return hash;
    }

    private AgentChatFilterInvokingContext? OnAgentInvokingFilter(Agent agent, IReadOnlyList<ChatMessageContent> history)
    {
        AgentChatFilterInvokingContext? context = null;

        if (this._filters is { Count: > 0 })
        {
            context = new(agent, history);

            for (int i = 0; i < this._filters.Count; i++)
            {
                this._filters[i].OnAgentInvoking(context);
            }
        }

        return context;
    }

    private AgentChatFilterInvokedContext? OnAgentInvokedFilter(Agent agent, IReadOnlyList<ChatMessageContent> history, ChatMessageContent message)
    {
        AgentChatFilterInvokedContext? context = null;

        if (this._filters is { Count: > 0 })
        {
            context = new(agent, history, message);

            for (int i = 0; i < this._filters.Count; i++)
            {
                this._filters[i].OnAgentInvoked(context);
            }
        }

        return context;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentChat"/> class.
    /// </summary>
    protected AgentChat()
    {
        this._agentChannels = [];
        this._broadcastQueue = new();
        this._channelMap = [];
        this._history = [];
    }
}
