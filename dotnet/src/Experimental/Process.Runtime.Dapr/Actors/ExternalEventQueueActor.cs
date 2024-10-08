// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Dapr.Actors.Runtime;

namespace Microsoft.SemanticKernel;

/// <summary>
/// An actor that represents an external event queue.
/// </summary>
internal class ExternalEventQueueActor : Actor, IExternalEventQueue
{
    private readonly Queue<KernelProcessEvent> _queue = new();

    public ExternalEventQueueActor(ActorHost host) : base(host)
    {
    }

    public Task<List<KernelProcessEvent>> DequeueAllAsync()
    {
        var items = this._queue.ToList();
        this._queue.Clear();
        return Task.FromResult(items);
    }

    public Task EnqueueAsync(KernelProcessEvent externalEvent)
    {
        this._queue.Enqueue(externalEvent);
        return Task.CompletedTask;
    }
}
