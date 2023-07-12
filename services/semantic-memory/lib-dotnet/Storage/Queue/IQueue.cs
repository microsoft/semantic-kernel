// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Services.Storage.Queue;

public interface IQueue : IDisposable
{
    /// <summary>
    /// Connect to a queue and (optionally) start dispatching messages
    /// </summary>
    /// <param name="queueName">Name of the queue</param>
    /// <param name="options">Options for the queue connection</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    /// <returns>Queue instance</returns>
    Task<IQueue> ConnectToQueueAsync(string queueName, QueueOptions options = default, CancellationToken cancellationToken = default);

    /// <summary>
    /// Add a message to the queue
    /// </summary>
    /// <param name="message">Message content</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    Task EnqueueAsync(string message, CancellationToken cancellationToken = default);

    /// <summary>
    /// Define the logic to execute when a new message is in the queue.
    /// </summary>
    /// <param name="processMessageAction">Async action to execute</param>
    void OnDequeue(Func<string, Task<bool>> processMessageAction);
}
