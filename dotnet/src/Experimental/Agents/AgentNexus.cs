// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Experimental.Agents.Exceptions;
using Microsoft.SemanticKernel.Experimental.Agents.Extensions;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Associate a <see cref="ChatMessageContent"/> with an agent source.
/// </summary>
/// <param name="AgentId">The agent identifier</param>
/// <param name="MessageId">An optional message identifier.</param>
public record AgentMessageSource(string AgentId, string? MessageId = null)
{
    internal string ToJson()
    {
        return BinaryData.FromObjectAsJson(this).ToString();
    }
}

/// <summary>
/// Point of interaction for one or more agents.
/// </summary>
public abstract class AgentNexus
{
    private static readonly SHA256CryptoServiceProvider s_sha256 = new();

    private readonly BroadcastQueue _broadcastQueue;
    private readonly Dictionary<string, AgentChannel> _agentChannels;
    private readonly Dictionary<Agent, string> _channelMap;
    private int _isActive;

    /// <summary>
    /// The primary nexus history.
    /// </summary>
    internal ChatHistory History { get; } // $$$ PUBLIC LIST OF MESSAGESS

    /// <summary>
    /// Retrieve the message history, either the primary history or
    /// an agent specific version.
    /// </summary>
    /// <param name="agent">An optional agent, if requesting an agent history.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The message history</returns>
    public IAsyncEnumerable<ChatMessageContent> GetHistoryAsync(Agent? agent = null, CancellationToken cancellationToken = default)
    {
        if (agent == null)
        {
            return this.History.ToDescending();
        }

        var channelKey = this.GetHash(agent);
        if (!this._agentChannels.TryGetValue(channelKey, out var channel))
        {
            return Array.Empty<ChatMessageContent>().ToAsyncEnumerable();
        }

        return channel.GetHistoryAsync(cancellationToken);
    }

    /// <summary>
    /// Process a discrete incremental interaction between a single <see cref="Agent"/> an a <see cref="AgentNexus"/>.
    /// </summary>
    /// <param name="agent">The agent actively interacting with the nexus.</param>
    /// <param name="input">Optional user input.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    protected async IAsyncEnumerable<ChatMessageContent> InvokeAgentAsync(
        Agent agent,
        ChatMessageContent? input = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        // Verify only a single operation is active
        int wasActive = Interlocked.CompareExchange(ref this._isActive, 1, 0);
        if (wasActive > 0)
        {
            throw new AgentException("Unable to proceed while another agent is active.");
        }

        try
        {
            // Manifest the required channel
            var channel = await this.GetChannelAsync(agent, cancellationToken).ConfigureAwait(false);

            if (input.TryGetContent(out var content))
            {
                this.History.AddUserMessage(content, input!.Name);
                yield return input!;
            }

            // Invoke agent & process response
            List<ChatMessageContent> messages = [];
            await foreach (var message in channel.InvokeAsync(agent, input, cancellationToken).ConfigureAwait(false))
            {
                // Add to primary history
                this.History.Add(message);
                messages.Add(message);

                // Yield message to caller
                yield return message;
            }

            // Broadcast message to other channels (in parallel)
            var channelRefs =
                this._agentChannels
                    .Where(kvp => kvp.Value != channel)
                    .Select(kvp => new ChannelRef(kvp.Value, kvp.Key));
            this._broadcastQueue.Queue(channelRefs, messages);
        }
        finally
        {
            Interlocked.Exchange(ref this._isActive, 0);
        }
    }

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="history"></param>
    public void Bind(ChatHistory history) // $$$ SCOPE / CONTRACT (PROVIDER?)
    {
        if (this.History.Count == 0)
        {
            this.History.AddRange(history);
        }
        // $$$ ELSE EXCEPTION
    }

    private async Task<AgentChannel> GetChannelAsync(Agent agent, CancellationToken cancellationToken)
    {
        var channelKey = this.GetHash(agent);

        await this._broadcastQueue.IsRecievingAsync(channelKey).ConfigureAwait(false);

        if (!this._agentChannels.TryGetValue(channelKey, out var channel))
        {
            channel = await agent.CreateChannelAsync(cancellationToken).ConfigureAwait(false);

            if (this.History.Count > 0)
            {
                await channel.RecieveAsync(this.History, cancellationToken).ConfigureAwait(false);
            }

            this._agentChannels.Add(channelKey, channel);
        }

        return channel;
    }

    private string GetHash(Agent agent)
    {
        if (this._channelMap.TryGetValue(agent, out var hash))
        {
            return hash;
        }

        var buffer = Encoding.UTF8.GetBytes(string.Join(":", agent.GetChannelKeys()));
        var result = s_sha256.ComputeHash(buffer);

        hash = Convert.ToBase64String(result);

        this._channelMap.Add(agent, hash);

        return hash;
    }

    /// <summary>
    /// Transform text into a user message.
    /// </summary>
    /// <param name="input">Optional user input.</param>
    protected static ChatMessageContent? CreateUserMessage(string? input)
    {
        return string.IsNullOrWhiteSpace(input) ? null : new ChatMessageContent(AuthorRole.User, input);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentNexus"/> class.
    /// </summary>
    protected AgentNexus()
    {
        this._agentChannels = [];
        this._channelMap = [];
        this.History = [];
        this._broadcastQueue = new();
    }

    private record ChannelRef(AgentChannel Channel, string Hash);
    private class ChannelQueue : ConcurrentQueue<IList<ChatMessageContent>>;

    private class BroadcastQueue
    {
        private readonly Dictionary<string, ChannelQueue> _queue = [];
        private readonly Dictionary<string, Task> _tasks = [];
        private readonly object _queueLock = new();

        public TimeSpan BlockDuration { get; set; } = TimeSpan.FromSeconds(1);

        public void Queue(IEnumerable<ChannelRef> channels, IList<ChatMessageContent> messages)
        {
            lock (this._queueLock)
            {
                foreach (var channel in channels)
                {
                    var queue = GetQueue(channel);
                    queue.Enqueue(messages);

                    if (!this._tasks.ContainsKey(channel.Hash))
                    {
                        this._tasks.Add(channel.Hash, RecieveAsync(channel, queue));
                    }
                }
            }

            ChannelQueue GetQueue(ChannelRef channel)
            {
                if (!this._queue.TryGetValue(channel.Hash, out var queue))
                {
                    queue = new ChannelQueue();
                    this._queue.Add(channel.Hash, queue);
                }

                return queue;
            }

            async Task RecieveAsync(ChannelRef channel, ChannelQueue queue)
            {
                while (queue.TryDequeue(out var messages))
                {
                    await channel.Channel.RecieveAsync(messages).ConfigureAwait(false);
                }

                lock (this._queueLock)
                {
                    this._tasks.Remove(channel.Hash);
                }
            }
        }

        public async Task<bool> IsRecievingAsync(string hash)
        {
            ChannelQueue queue;

            lock (this._queueLock)
            {
                if (!this._queue.TryGetValue(hash, out queue))
                {
                    return false;
                }
            }

            while (queue.Count > 0)
            {
                await Task.Delay(this.BlockDuration).ConfigureAwait(false);
            }

            return false;
        }
    }
}
