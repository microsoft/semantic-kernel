// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Dapr.Actors.Runtime;
using Microsoft.SemanticKernel.Process.Runtime;
using Microsoft.SemanticKernel.Process.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// An actor that represents an external event queue.
/// </summary>
internal class ExternalEventBufferActor : Actor, IExternalEventBuffer
{
    private List<KernelProcessEvent> _queue = [];

    /// <summary>
    /// Required constructor for Dapr Actor.
    /// </summary>
    /// <param name="host">The actor host.</param>
    public ExternalEventBufferActor(ActorHost host) : base(host)
    {
    }

    /// <summary>
    /// Dequeues an event.
    /// </summary>
    /// <returns>A <see cref="List{T}"/> where T is <see cref="ProcessEvent"/></returns>
    public async Task<List<KernelProcessEvent>> DequeueAllAsync()
    {
        // Dequeue and clear the queue.
        List<KernelProcessEvent> items = [.. this._queue];
        this._queue!.Clear();

        // Save the state.
        await this.StateManager.SetStateAsync(ActorStateKeys.ExternalEventQueueState, KernelProcessEventSerializer.Prepare(this._queue).ToArray()).ConfigureAwait(false);
        await this.StateManager.SaveStateAsync().ConfigureAwait(false);

        return items;
    }

    public async Task EnqueueAsync(KernelProcessEvent externalEvent)
    {
        this._queue.Add(externalEvent);

        // Save the state.
        await this.StateManager.SetStateAsync(ActorStateKeys.ExternalEventQueueState, KernelProcessEventSerializer.Prepare(this._queue).ToArray()).ConfigureAwait(false);
        await this.StateManager.SaveStateAsync().ConfigureAwait(false);
    }

    /// <summary>
    /// Called when the actor is activated. Used to initialize the state of the actor.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    protected override async Task OnActivateAsync()
    {
        var eventQueueState = await this.StateManager.TryGetStateAsync<EventContainer<KernelProcessEvent>[]>(ActorStateKeys.ExternalEventQueueState).ConfigureAwait(false);
        if (eventQueueState.HasValue)
        {
            this._queue = [.. KernelProcessEventSerializer.Process(eventQueueState.Value)];
        }
        else
        {
            this._queue = [];
        }
    }
}
