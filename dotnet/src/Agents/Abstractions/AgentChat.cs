﻿// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Agents.Extensions;
using Microsoft.SemanticKernel.Agents.Internal;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Point of interaction for one or more agents.
/// </summary>
/// <remarks>
/// Any <see cref="AgentChat" /> instance does not support concurrent invocation and
/// will throw exception if concurrent activity is attempted for any public method.
/// </remarks>
public abstract class AgentChat
{
    private readonly BroadcastQueue _broadcastQueue;
    private readonly Dictionary<string, AgentChannel> _agentChannels; // Map channel hash to channel: one entry per channel.
    private readonly Dictionary<Agent, string> _channelMap; // Map agent to its channel-hash: one entry per agent.

    private int _isActive;
    private ILogger? _logger;

    /// <summary>
    /// Indicates if a chat operation is active.  Activity is defined as
    /// any the execution of any public method.
    /// </summary>
    public bool IsActive => Interlocked.CompareExchange(ref this._isActive, 1, 1) > 0;

    /// <summary>
    /// The <see cref="ILoggerFactory"/> associated with the <see cref="AgentChat"/>.
    /// </summary>
    public ILoggerFactory LoggerFactory { get; init; } = NullLoggerFactory.Instance;

    /// <summary>
    /// The <see cref="ILogger"/> associated with this chat.
    /// </summary>
    protected ILogger Logger => this._logger ??= this.LoggerFactory.CreateLogger(this.GetType());

    /// <summary>
    /// Exposes the internal history to subclasses.
    /// </summary>
    protected ChatHistory History { get; }

    /// <summary>
    /// Process a series of interactions between the agents participating in this chat.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    public abstract IAsyncEnumerable<ChatMessageContent> InvokeAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Process a series of interactions between the agents participating in this chat.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    public abstract IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Retrieve the chat history.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The message history</returns>
    public IAsyncEnumerable<ChatMessageContent> GetChatMessagesAsync(CancellationToken cancellationToken = default) =>
        this.GetChatMessagesAsync(agent: null, cancellationToken);

    /// <summary>
    /// Retrieve the message history, either the primary history or
    /// an agent specific version.
    /// </summary>
    /// <param name="agent">An optional agent, if requesting an agent history.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The message history</returns>
    /// <remarks>
    /// Any <see cref="AgentChat" /> instance does not support concurrent invocation and
    /// will throw exception if concurrent activity is attempted.
    /// </remarks>
    public async IAsyncEnumerable<ChatMessageContent> GetChatMessagesAsync(
        Agent? agent,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this.SetActivityOrThrow(); // Disallow concurrent access to chat history

        this.Logger.LogAgentChatGetChatMessages(nameof(GetChatMessagesAsync), agent);

        try
        {
            IAsyncEnumerable<ChatMessageContent>? messages = null;

            if (agent is null)
            {
                // Provide primary history
                messages = this.History.ToDescendingAsync();
            }
            else // else provide channel specific history
            {
                // Retrieve the requested channel, if exists, and block until channel is synchronized.
                string channelKey = this.GetAgentHash(agent);
                AgentChannel? channel = await this.SynchronizeChannelAsync(channelKey, cancellationToken).ConfigureAwait(false);
                if (channel is not null)
                {
                    messages = channel.GetHistoryAsync(cancellationToken);
                }
            }

            if (messages is not null)
            {
                await foreach (ChatMessageContent message in messages.ConfigureAwait(false))
                {
                    yield return message;
                }
            }
        }
        finally
        {
            this.ClearActivitySignal(); // Signal activity hash completed
        }
    }

    /// <summary>
    /// Append a message to the conversation.  Adding a message while an agent
    /// is active is not allowed.
    /// </summary>
    /// <param name="message">A non-system message with which to append to the conversation.</param>
    /// <remarks>
    /// Adding a message to the conversation requires any active <see cref="AgentChannel"/> remains
    /// synchronized, so the message is broadcast to all channels.
    /// </remarks>
    /// <throws>KernelException if a system message is present, without taking any other action</throws>
    /// <remarks>
    /// Any <see cref="AgentChat" /> instance does not support concurrent invocation and
    /// will throw exception if concurrent activity is attempted.
    /// </remarks>
    public void AddChatMessage(ChatMessageContent message)
    {
        this.AddChatMessages([message]);
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
    /// Any <see cref="AgentChat" /> instance does not support concurrent invocation and
    /// will throw exception if concurrent activity is attempted.
    /// </remarks>
    public void AddChatMessages(IReadOnlyList<ChatMessageContent> messages)
    {
        this.SetActivityOrThrow(); // Disallow concurrent access to chat history

        for (int index = 0; index < messages.Count; ++index)
        {
            if (messages[index].Role == AuthorRole.System)
            {
                throw new KernelException($"History does not support messages with Role of {AuthorRole.System}.");
            }
        }

        this.Logger.LogAgentChatAddingMessages(nameof(AddChatMessages), messages.Count);

        try
        {
            // Append to chat history
            this.History.AddRange(messages);

            // Broadcast message to other channels (in parallel)
            // Note: Able to queue messages without synchronizing channels.
            var channelRefs = this._agentChannels.Select(kvp => new ChannelReference(kvp.Value, kvp.Key));
            this._broadcastQueue.Enqueue(channelRefs, messages);

            this.Logger.LogAgentChatAddedMessages(nameof(AddChatMessages), messages.Count);
        }
        finally
        {
            this.ClearActivitySignal(); // Signal activity hash completed
        }
    }

    /// <summary>
    /// Process a discrete incremental interaction between a single <see cref="Agent"/> an a <see cref="AgentChat"/>.
    /// </summary>
    /// <param name="agent">The agent actively interacting with the chat.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    /// <remarks>
    /// Any <see cref="AgentChat" /> instance does not support concurrent invocation and
    /// will throw exception if concurrent activity is attempted.
    /// </remarks>
    protected async IAsyncEnumerable<ChatMessageContent> InvokeAgentAsync(
        Agent agent,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this.SetActivityOrThrow(); // Disallow concurrent access to chat history

        this.Logger.LogAgentChatInvokingAgent(nameof(InvokeAgentAsync), agent.GetType(), agent.Id);

        try
        {
            // Get or create the required channel and block until channel is synchronized.
            // Will throw exception when propagating a processing failure.
            AgentChannel channel = await this.GetOrCreateChannelAsync(agent, cancellationToken).ConfigureAwait(false);

            // Invoke agent & process response
            List<ChatMessageContent> messages = [];

            await foreach ((bool isVisible, ChatMessageContent message) in channel.InvokeAsync(agent, cancellationToken).ConfigureAwait(false))
            {
                this.Logger.LogAgentChatInvokedAgentMessage(nameof(InvokeAgentAsync), agent.GetType(), agent.Id, message);

                messages.Add(message);

                // Add to primary history
                this.History.Add(message);

                if (isVisible)
                {
                    // Yield message to caller
                    yield return message;
                }
            }

            // Broadcast message to other channels (in parallel)
            // Note: Able to queue messages without synchronizing channels.
            var channelRefs =
                this._agentChannels
                    .Where(kvp => kvp.Value != channel)
                    .Select(kvp => new ChannelReference(kvp.Value, kvp.Key));
            this._broadcastQueue.Enqueue(channelRefs, messages);

            this.Logger.LogAgentChatInvokedAgent(nameof(InvokeAgentAsync), agent.GetType(), agent.Id);
        }
        finally
        {
            this.ClearActivitySignal(); // Signal activity hash completed
        }
    }

    /// <summary>
    /// Process a discrete incremental interaction between a single <see cref="Agent"/> an a <see cref="AgentChat"/>.
    /// </summary>
    /// <param name="agent">The agent actively interacting with the chat.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    /// <remarks>
    /// Any <see cref="AgentChat" /> instance does not support concurrent invocation and
    /// will throw exception if concurrent activity is attempted.
    /// </remarks>
    protected async IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAgentAsync(
        Agent agent,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this.SetActivityOrThrow(); // Disallow concurrent access to chat history

        this.Logger.LogAgentChatInvokingAgent(nameof(InvokeAgentAsync), agent.GetType(), agent.Id);

        try
        {
            // Get or create the required channel and block until channel is synchronized.
            // Will throw exception when propagating a processing failure.
            AgentChannel channel = await this.GetOrCreateChannelAsync(agent, cancellationToken).ConfigureAwait(false);

            // Invoke agent & process response
            ChatHistory messages = [];

            await foreach (StreamingChatMessageContent streamingContent in channel.InvokeStreamingAsync(agent, messages, cancellationToken).ConfigureAwait(false))
            {
                yield return streamingContent;
            }

            this.History.AddRange(messages);

            this.Logger.LogAgentChatInvokedStreamingAgentMessages(nameof(InvokeAgentAsync), agent.GetType(), agent.Id, messages);

            // Broadcast message to other channels (in parallel)
            // Note: Able to queue messages without synchronizing channels.
            var channelRefs =
                this._agentChannels
                    .Where(kvp => kvp.Value != channel)
                    .Select(kvp => new ChannelReference(kvp.Value, kvp.Key));
            this._broadcastQueue.Enqueue(channelRefs, messages);

            this.Logger.LogAgentChatInvokedAgent(nameof(InvokeAgentAsync), agent.GetType(), agent.Id);
        }
        finally
        {
            this.ClearActivitySignal(); // Signal activity hash completed
        }
    }

    /// <summary>
    /// Reset the chat, clearing all history and persisted state.
    /// All agents will remain present.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public async Task ResetAsync(CancellationToken cancellationToken = default)
    {
        this.SetActivityOrThrow(); // Disallow concurrent access to chat

        try
        {
            Task[] resetTasks = this._agentChannels.Values.Select(c => c.ResetAsync(cancellationToken)).ToArray();
            await Task.WhenAll(resetTasks).ConfigureAwait(false);
            this._agentChannels.Clear();
            this._channelMap.Clear();
            this.History.Clear();
        }
        finally
        {
            this.ClearActivitySignal();
        }
    }

    /// <summary>
    /// Clear activity signal to indicate that activity has ceased.
    /// </summary>
    private void ClearActivitySignal()
    {
        // Note: Interlocked is the absolute lightest synchronization mechanism available in dotnet.
        Interlocked.Exchange(ref this._isActive, 0);
    }

    /// <summary>
    /// Test to ensure chat is not concurrently active and throw exception if it is.
    /// If not, activity is signaled.
    /// </summary>
    /// <remarks>
    /// Rather than allowing concurrent invocation to result in undefined behavior / failure,
    /// it is preferred to fail-fast in order to avoid side-effects / state mutation.
    /// The activity signal is used to manage ability and visibility for taking actions based
    /// on conversation history.
    /// </remarks>
    protected void SetActivityOrThrow()
    {
        // Note: Interlocked is the absolute lightest synchronization mechanism available in dotnet.
        int wasActive = Interlocked.CompareExchange(ref this._isActive, 1, 0);
        if (wasActive > 0)
        {
            throw new KernelException("Unable to proceed while another agent is active.");
        }
    }

    private string GetAgentHash(Agent agent)
    {
        if (!this._channelMap.TryGetValue(agent, out string? hash))
        {
            hash = KeyEncoder.GenerateHash(agent.GetChannelKeys());

            // Ok if already present: same agent always produces the same hash
            this._channelMap.Add(agent, hash);
        }

        return hash;
    }

    private async Task<AgentChannel> GetOrCreateChannelAsync(Agent agent, CancellationToken cancellationToken)
    {
        string channelKey = this.GetAgentHash(agent);
        AgentChannel? channel = await this.SynchronizeChannelAsync(channelKey, cancellationToken).ConfigureAwait(false);
        if (channel is null)
        {
            this.Logger.LogAgentChatCreatingChannel(nameof(InvokeAgentAsync), agent.GetType(), agent.Id);

            channel = await agent.CreateChannelAsync(cancellationToken).ConfigureAwait(false);

            this._agentChannels.Add(channelKey, channel);

            if (this.History.Count > 0)
            {
                // Sync channel with existing history
                await channel.ReceiveAsync(this.History, cancellationToken).ConfigureAwait(false);
            }

            this.Logger.LogAgentChatCreatedChannel(nameof(InvokeAgentAsync), agent.GetType(), agent.Id);
        }

        return channel;
    }

    private async Task<AgentChannel?> SynchronizeChannelAsync(string channelKey, CancellationToken cancellationToken)
    {
        if (this._agentChannels.TryGetValue(channelKey, out AgentChannel? channel))
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
        this._agentChannels = [];
        this._broadcastQueue = new();
        this._channelMap = [];
        this.History = [];
    }
}
