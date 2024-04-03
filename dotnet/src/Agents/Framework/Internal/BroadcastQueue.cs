// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using ChannelQueue = System.Collections.Concurrent.ConcurrentQueue<System.Collections.Generic.IList<Microsoft.SemanticKernel.ChatMessageContent>>;

namespace Microsoft.SemanticKernel.Agents.Internal;

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
    private int _isActive;
    private readonly Dictionary<string, ChannelQueue> _queues = new();
    private readonly Dictionary<string, Task> _tasks = new();
    private readonly Dictionary<string, Exception> _failures = new();
    private readonly object _queueLock = new(); // Synchronize access to _isActive, _queue and _tasks.

    /// <summary>
    /// Defines the yield duration when blocking for a channel-queue.
    /// to drain.
    /// </summary>
    public TimeSpan BlockDuration { get; set; } = TimeSpan.FromSeconds(1);

    /// <summary>
    /// Enqueue a set of messages for a given channel.
    /// </summary>
    /// <param name="channels">The target channels for which to broadcast.</param>
    /// <param name="messages">The messages being broadcast.</param>
    public void Enqueue(IEnumerable<ChannelReference> channels, IList<ChatMessageContent> messages)
    {
        lock (this._queueLock)
        {
            foreach (var channel in channels)
            {
                var queue = this.GetQueue(channel);
                queue.Enqueue(messages);

                if (!this._tasks.ContainsKey(channel.Hash))
                {
                    this._tasks.Add(channel.Hash, this.ReceiveAsync(channel, queue));
                }
            }
        }
    }

    /// <summary>
    /// Ensure all channels are synchronized.
    /// </summary>
    public void Synchronize(IEnumerable<ChannelReference> channels)
    {
        lock (this._queueLock)
        {
            foreach (var channel in channels)
            {
                var queue = this.GetQueue(channel);
                if (!queue.IsEmpty && !this._tasks.ContainsKey(channel.Hash))
                {
                    this._tasks.Add(channel.Hash, this.ReceiveAsync(channel, queue));
                }
            }
        }
    }

    private async Task ReceiveAsync(ChannelReference channel, ChannelQueue queue)
    {
        Interlocked.CompareExchange(ref this._isActive, 1, 0); // Set regardless of current state.

        Exception? failure = null;

        while (!queue.IsEmpty)
        {
            if (queue.TryPeek(out var messages)) // Leave payload on queue for retry on failure
            {
                try
                {
                    await channel.Channel.ReceiveAsync(messages).ConfigureAwait(false);
                    queue.TryDequeue(out _); // Queue has already been peeked.  Remove head on success.
                }
                catch (Exception exception) when (!exception.IsCriticalException())
                {
                    failure = exception;
                    break;
                }
            }
        }

        lock (this._queueLock)
        {
            this._tasks.Remove(channel.Hash);
            this._isActive = this._tasks.Count == 0 ? 0 : this._isActive; // Clear if channel queue has drained.
            if (failure != null)
            {
                this._failures.Add(channel.Hash, failure);
            }
        }
    }

    private ChannelQueue GetQueue(ChannelReference channel)
    {
        if (!this._queues.TryGetValue(channel.Hash, out var queue))
        {
            queue = new ChannelQueue();
            this._queues.Add(channel.Hash, queue);
        }

        return queue;
    }

    /// <summary>
    /// Blocks until a channel-queue is not in a receive state.
    /// </summary>
    /// <param name="channel">A <see cref="ChannelReference"/> structure.</param>
    /// <returns>false when channel is no longer receiving.</returns>
    /// <throws>
    /// When channel is out of sync.
    /// </throws>
    public async Task<bool> IsReceivingAsync(ChannelReference channel)
    {
        ChannelQueue queue;

        lock (this._queueLock)
        {
            if (this._failures.TryGetValue(channel.Hash, out var failure))
            {
                this._failures.Remove(channel.Hash);
                throw new AgentException($"Unexpected failure broadcasting to channel: {channel.Channel.GetType().Name}", failure);
            }

            if (!this._queues.TryGetValue(channel.Hash, out queue))
            {
                return false;
            }
        }

        while (!queue.IsEmpty) // ChannelQueue is ConcurrentQueue, no need for _queueLock
        {
            await Task.Delay(this.BlockDuration).ConfigureAwait(false);
        }

        return false;
    }
}
