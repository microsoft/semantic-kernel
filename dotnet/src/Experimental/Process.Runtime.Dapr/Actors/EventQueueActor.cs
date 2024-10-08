// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Dapr.Actors.Runtime;

namespace Microsoft.SemanticKernel;

/// <summary>
/// An actor that represents an event queue.
/// </summary>
internal class EventQueueActor : Actor, IEventQueue
{
    private readonly Queue<DaprEvent> _queue = new();

    public EventQueueActor(ActorHost host) : base(host)
    {
    }

    public Task<List<DaprEvent>> DequeueAllAsync()
    {
        var items = this._queue.ToList();
        this._queue.Clear();
        return Task.FromResult(items);
    }

    public Task EnqueueAsync(DaprEvent stepEvent)
    {
        this._queue.Enqueue(stepEvent);
        return Task.CompletedTask;
    }
}
