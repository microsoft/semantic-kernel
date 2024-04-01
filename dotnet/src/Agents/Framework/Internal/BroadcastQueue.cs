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
    private readonly Dictionary<string, ChannelQueue> _queue = new();
    private readonly Dictionary<string, Task> _tasks = new();
    private readonly object _queueLock = new(); // Synchronize access to _isActive, _queue and _tasks.

    /// <summary>
    /// Defines the yield duration when blocking for a channel-queue.
    /// to drain.
    /// </summary>
    public TimeSpan BlockDuration { get; set; } = TimeSpan.FromSeconds(1);

    /// <summary>
    /// Indicates if the queue is broadcasting messages.
    /// </summary>
    public bool IsActive => this._isActive != 0;

    /// <summary>
    /// Block until queue not broadcasting messages.
    /// </summary>
    /// <remarks>
    /// No guarantee that it won't be broadcasting immediately after drained.
    /// </remarks>
    public async Task FlushAsync()
    {
        while (this.IsActive)
        {
            await Task.Delay(this.BlockDuration).ConfigureAwait(false);
        }
    }

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
            Interlocked.CompareExchange(ref this._isActive, 1, 0); // Set regardless of current state.

            while (queue.TryDequeue(out var messages)) // ChannelQueue is ConcurrentQueue, no need for _queueLock
            {
                await channel.Channel.ReceiveAsync(messages).ConfigureAwait(false);
            }

            lock (this._queueLock)
            {
                this._tasks.Remove(channel.Hash);
                this._isActive = this._tasks.Count == 0 ? 0 : this._isActive; // Clear if channel queue has drained.
            }
        }
    }

    /// <summary>
    /// Blocks until a channel-queue is not in a receive state.
    /// </summary>
    /// <param name="hash">The base-64 encoded channel hash.</param>
    /// <returns>false when channel is no longer receiving.</returns>
    public async Task<bool> IsReceivingAsync(string hash)
    {
        ChannelQueue queue;

        lock (this._queueLock)
        {
            if (!this._queue.TryGetValue(hash, out queue))
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
