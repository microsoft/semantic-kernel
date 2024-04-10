// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using ChannelQueue = System.Collections.Generic.Queue<System.Collections.Generic.IReadOnlyList<Microsoft.SemanticKernel.ChatMessageContent>>;

namespace Microsoft.SemanticKernel.Agents.Internal;

/// <summary>
/// Utility class used by <see cref="AgentChat"/> to manage the broadcast of
/// conversation messages via the <see cref="AgentChannel"/>.
/// (<see cref="AgentChannel.ReceiveAsync(IEnumerable{ChatMessageContent}, System.Threading.CancellationToken)"/>.)
/// </summary>
/// <remarks>
/// Maintains a set of channel specific queues, each with individual locks, in addition to a global state lock.
/// Queue specific locks exist to synchronize access to an individual queue without blocking
/// other queue operations or global state.
/// Locking order always state-lock > queue-lock or just single lock, never queue-lock => state-lock.
/// A deadlock cannot occur if locks are always acquired in same order.
/// </remarks>
internal sealed class BroadcastQueue
{
    private readonly Dictionary<string, QueueReference> _queues = new();
    private readonly Dictionary<string, Task> _tasks = new();
    private readonly Dictionary<string, Exception> _failures = new();
    private readonly object _stateLock = new(); // Synchronize access to object state.

    /// <summary>
    /// Defines the yield duration when waiting on a channel-queue to synchronize.
    /// to drain.
    /// </summary>
    public TimeSpan BlockDuration { get; set; } = TimeSpan.FromSeconds(0.1);

    /// <summary>
    /// Enqueue a set of messages for a given channel.
    /// </summary>
    /// <param name="channels">The target channels for which to broadcast.</param>
    /// <param name="messages">The messages being broadcast.</param>
    public void Enqueue(IEnumerable<ChannelReference> channels, IReadOnlyList<ChatMessageContent> messages)
    {
        lock (this._stateLock)
        {
            foreach (var channel in channels)
            {
                if (!this._queues.TryGetValue(channel.Hash, out var queueRef))
                {
                    queueRef = new();
                    this._queues.Add(channel.Hash, queueRef);
                }

                lock (queueRef.QueueLock)
                {
                    queueRef.Queue.Enqueue(messages);
                }

                if (!this._tasks.ContainsKey(channel.Hash))
                {
                    this._tasks.Add(channel.Hash, this.ReceiveAsync(channel, queueRef));
                }
            }
        }
    }

    /// <summary>
    /// Blocks until a channel-queue is not in a receive state.
    /// </summary>
    /// <param name="channelRef">A <see cref="ChannelReference"/> structure.</param>
    /// <returns>false when channel is no longer receiving.</returns>
    /// <throws>
    /// When channel is out of sync.
    /// </throws>
    public async Task EnsureSynchronizedAsync(ChannelReference channelRef)
    {
        QueueReference queueRef;

        lock (this._stateLock)
        {
            // Either won race with Enqueue or lost race with ReceiveAsync.
            // Missing queue is synchronized by definition.
            if (!this._queues.TryGetValue(channelRef.Hash, out queueRef))
            {
                return;
            }
        }

        // Evaluate queue state
        bool isEmpty = true;
        do
        {
            // Queue state is only changed within acquired QueueLock.
            // If its empty here, it is synchronized.
            lock (queueRef.QueueLock)
            {
                isEmpty = queueRef.IsEmpty;
            }

            lock (this._stateLock)
            {
                // Propagate prior failure (inform caller of synchronization issue)
                if (this._failures.TryGetValue(channelRef.Hash, out var failure))
                {
                    this._failures.Remove(channelRef.Hash); // Clearing failure means re-invoking EnsureSynchronizedAsync will activate empty queue
                    throw new KernelException($"Unexpected failure broadcasting to channel: {channelRef.Channel.GetType().Name}", failure);
                }

                // Activate non-empty queue
                if (!isEmpty)
                {
                    if (!this._tasks.TryGetValue(channelRef.Hash, out Task task) || task.IsCompleted)
                    {
                        this._tasks[channelRef.Hash] = this.ReceiveAsync(channelRef, queueRef);
                    }
                }
            }

            if (!isEmpty)
            {
                await Task.Delay(this.BlockDuration).ConfigureAwait(false);
            }
        }
        while (!isEmpty);
    }

    /// <summary>
    /// Processes the specified queue with the provided channel, until queue is empty.
    /// </summary>
    private async Task ReceiveAsync(ChannelReference channelRef, QueueReference queueRef)
    {
        Exception? failure = null;

        bool isEmpty = true; // Default to fall-through state
        do
        {
            Task receiveTask;

            // Queue state is only changed within acquired QueueLock.
            // If its empty here, it is synchronized.
            lock (queueRef.QueueLock)
            {
                isEmpty = queueRef.IsEmpty;

                // Process non empty queue
                if (isEmpty)
                {
                    break;
                }

                var messages = queueRef.Queue.Peek();
                receiveTask = channelRef.Channel.ReceiveAsync(messages);
            }

            // Queue not empty.
            try
            {
                await receiveTask.ConfigureAwait(false);
            }
            catch (Exception exception) when (!exception.IsCriticalException())
            {
                failure = exception;
            }

            // Propagate failure or update queue
            lock (this._stateLock)
            {
                // A failure on non empty queue means, still not empty.
                // Empty queue will have null failure
                if (failure != null)
                {
                    this._failures.Add(channelRef.Hash, failure);
                    break; // Skip dequeue
                }

                // Dequeue processed messages and re-evaluate
                lock (queueRef.QueueLock)
                {
                    // Queue has already been peeked.  Remove head on success.
                    queueRef.Queue.Dequeue();

                    isEmpty = queueRef.IsEmpty;
                }
            }
        }
        while (!isEmpty);
    }

    /// <summary>
    /// Utility class to associate a queue with its specific lock.
    /// </summary>
    private sealed class QueueReference
    {
        /// <summary>
        /// Queue specific lock to control queue access with finer granularity
        /// than the state-lock.
        /// </summary>
        public object QueueLock { get; } = new object();

        /// <summary>
        /// The target queue.
        /// </summary>
        public ChannelQueue Queue { get; } = new ChannelQueue();

        /// <summary>
        /// Convenience logic
        /// </summary>
        public bool IsEmpty => this.Queue.Count == 0;
    }
}
