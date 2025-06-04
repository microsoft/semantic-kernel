// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;
using ChannelQueue = System.Collections.Generic.Queue<System.Collections.Generic.IReadOnlyList<Microsoft.SemanticKernel.ChatMessageContent>>;

namespace Microsoft.SemanticKernel.Agents.Internal;

/// <summary>
/// Utility class used by <see cref="AgentChat"/> to manage the broadcast of
/// conversation messages via the <see cref="AgentChannel.ReceiveAsync"/>.
/// Interaction occurs via two methods:
/// - <see cref="BroadcastQueue.Enqueue"/>: Adds messages to a channel specific queue for processing.
/// - <see cref="BroadcastQueue.EnsureSynchronizedAsync"/>: Blocks until the specified channel's processing queue is empty.
/// </summary>
/// <remarks>
/// Maintains a set of channel specific queues, each with individual locks.
/// Queue specific locks exist to synchronize access to an individual queue only.
/// Due to the closed "friend" relationship between with <see cref="AgentChat"/>,
/// <see cref="BroadcastQueue"/> is never invoked concurrently, which eliminates
/// race conditions over the queue dictionary.
/// </remarks>
[Experimental("SKEXP0110")]
internal sealed class BroadcastQueue
{
    private readonly Dictionary<string, QueueReference> _queues = [];

    /// <summary>
    /// Defines the yield duration when waiting on a channel-queue to synchronize
    /// and drain.
    /// </summary>
    public TimeSpan BlockDuration { get; set; } = TimeSpan.FromSeconds(0.1);

    /// <summary>
    /// Enqueue a set of messages for a given channel.
    /// </summary>
    /// <param name="channelRefs">The target channels for which to broadcast.</param>
    /// <param name="messages">The messages being broadcast.</param>
    public void Enqueue(IEnumerable<ChannelReference> channelRefs, IReadOnlyList<ChatMessageContent> messages)
    {
        // Ensure mutating _queues
        foreach (var channelRef in channelRefs)
        {
            if (!this._queues.TryGetValue(channelRef.Hash, out var queueRef))
            {
                queueRef = new();
                this._queues.Add(channelRef.Hash, queueRef);
            }

            lock (queueRef.QueueLock)
            {
                queueRef.Queue.Enqueue(messages);

                if (queueRef.ReceiveTask?.IsCompleted ?? true)
                {
                    queueRef.ReceiveTask = ReceiveAsync(channelRef, queueRef);
                }
            }
        }
    }

    /// <summary>
    /// Blocks until a channel-queue is not in a receive state to ensure that
    /// channel history is complete.
    /// </summary>
    /// <param name="channelRef">A <see cref="ChannelReference"/> structure.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>false when channel is no longer receiving.</returns>
    /// <throws>
    /// When channel is out of sync.
    /// </throws>
    public async Task EnsureSynchronizedAsync(ChannelReference channelRef, CancellationToken cancellationToken = default)
    {
        // Either won race with Enqueue or lost race with ReceiveAsync.
        // Missing queue is synchronized by definition.
        if (!this._queues.TryGetValue(channelRef.Hash, out QueueReference? queueRef))
        {
            return;
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

                // Propagate prior failure (inform caller of synchronization issue)
                if (queueRef.ReceiveFailure is not null)
                {
                    Exception failure = queueRef.ReceiveFailure;
                    queueRef.ReceiveFailure = null;
                    throw new KernelException($"Unexpected failure broadcasting to channel: {channelRef.Channel.GetType()}", failure);
                }

                // Activate non-empty queue
                if (!isEmpty)
                {
                    if (queueRef.ReceiveTask?.IsCompleted ?? true)
                    {
                        queueRef.ReceiveTask = ReceiveAsync(channelRef, queueRef, cancellationToken);
                    }
                }
            }

            if (!isEmpty)
            {
                await Task.Delay(this.BlockDuration, cancellationToken).ConfigureAwait(false);
            }
        }
        while (!isEmpty);
    }

    /// <summary>
    /// Processes the specified queue with the provided channel, until queue is empty.
    /// </summary>
    private static async Task ReceiveAsync(ChannelReference channelRef, QueueReference queueRef, CancellationToken cancellationToken = default)
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
                receiveTask = channelRef.Channel.ReceiveAsync(messages, cancellationToken);
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

            lock (queueRef.QueueLock)
            {
                // Propagate failure or update queue
                if (failure is not null)
                {
                    queueRef.ReceiveFailure = failure;
                    break; // Failure on non-empty queue means, still not empty.
                }

                // Queue has already been peeked.  Remove head on success.
                queueRef.Queue.Dequeue();

                isEmpty = queueRef.IsEmpty; // Re-evaluate state
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
        /// Convenience logic
        /// </summary>
        public bool IsEmpty => this.Queue.Count == 0;

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
        /// The task receiving and processing messages from <see cref="Queue" />.
        /// </summary>
        public Task? ReceiveTask { get; set; }

        /// <summary>
        /// Capture any failure that may occur during execution of <see cref="ReceiveTask"/>.
        /// </summary>
        public Exception? ReceiveFailure { get; set; }
    }
}
