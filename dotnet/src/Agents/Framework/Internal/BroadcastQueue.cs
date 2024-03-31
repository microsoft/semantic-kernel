// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using ChannelQueue = System.Collections.Concurrent.ConcurrentQueue<System.Collections.Generic.IList<Microsoft.SemanticKernel.ChatMessageContent>>;

namespace Microsoft.SemanticKernel.Agents.Internal;

/// <summary>
/// Tracks channel along with its key (hashed)
/// </summary>
internal readonly struct ChannelReference
{
    public AgentChannel Channel { get; }

    public string Hash { get; }

    public ChannelReference(AgentChannel channel, string hash)
    {
        this.Channel = channel;
        this.Hash = hash;
    }
}

/// <summary>
/// Utility class used by <see cref="AgentNexus"/> to manage the broadcast of
/// conversation messages via the <see cref="AgentChannel"/>.
/// (<see cref="AgentChannel.ReceiveAsync(IEnumerable{ChatMessageContent}, System.Threading.CancellationToken)"/>.)
/// </summary>
/// <remarks>
/// Maintains a set of channel specific queues.
/// </remarks>
internal sealed class BroadcastQueue
{
    private readonly Dictionary<string, ChannelQueue> _queue = new();
    private readonly Dictionary<string, Task> _tasks = new();
    private readonly object _queueLock = new();

    /// <summary>
    /// Defines the yield duration when blocking for a channel-queue.
    /// to drain.
    /// </summary>
    public TimeSpan BlockDuration { get; set; } = TimeSpan.FromSeconds(1);

    /// <summary>
    /// Enqueue a set of messages for a given channel.
    /// </summary>
    /// <param name="channels"></param>
    /// <param name="messages"></param>
    public void Enqueue(IEnumerable<ChannelReference> channels, IList<ChatMessageContent> messages)
    {
        lock (this._queueLock)
        {
            foreach (var channel in channels)
            {
                var queue = GetQueue(channel);
                queue.Enqueue(messages);

                if (!this._tasks.ContainsKey(channel.Hash))
                {
                    this._tasks.Add(channel.Hash, ReceiveAsync(channel, queue));
                }
            }
        }

        ChannelQueue GetQueue(ChannelReference channel)
        {
            if (!this._queue.TryGetValue(channel.Hash, out var queue))
            {
                queue = new ChannelQueue();
                this._queue.Add(channel.Hash, queue);
            }

            return queue;
        }

        async Task ReceiveAsync(ChannelReference channel, ChannelQueue queue)
        {
            while (queue.TryDequeue(out var messages))
            {
                await channel.Channel.ReceiveAsync(messages).ConfigureAwait(false);
            }

            lock (this._queueLock)
            {
                this._tasks.Remove(channel.Hash);
            }
        }
    }

    /// <summary>
    /// Blocks until a channel-queue is not in a recieve state.
    /// </summary>
    /// <param name="hash">The base-64 encoded channel hash.</param>
    /// <returns>false when channel is no longer recieving.</returns>
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

        while (!queue.IsEmpty)
        {
            await Task.Delay(this.BlockDuration).ConfigureAwait(false);
        }

        return false;
    }
}
