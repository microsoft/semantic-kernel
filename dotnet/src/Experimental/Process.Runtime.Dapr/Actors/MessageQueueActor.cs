// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Dapr.Actors.Runtime;

namespace Microsoft.SemanticKernel;

/// <summary>
/// An actor that represents a message queue.
/// </summary>
internal class MessageQueueActor : Actor, IMessageQueue
{
    private readonly Queue<DaprMessage> _queue = new();

    public MessageQueueActor(ActorHost host) : base(host)
    {
    }

    public Task<List<DaprMessage>> DequeueAllAsync()
    {
        var items = this._queue.ToList();
        this._queue.Clear();
        return Task.FromResult(items);
    }

    public Task EnqueueAsync(DaprMessage message)
    {
        this._queue.Enqueue(message);
        return Task.CompletedTask;
    }
}
