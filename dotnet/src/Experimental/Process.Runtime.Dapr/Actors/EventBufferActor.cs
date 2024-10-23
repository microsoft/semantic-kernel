// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Dapr.Actors.Runtime;
using Microsoft.SemanticKernel.Process.Runtime;

namespace Microsoft.SemanticKernel;

/// <summary>
/// An actor that represents an event queue.
/// </summary>
internal class EventBufferActor : Actor, IEventBuffer
{
    private const string EventQueueState = "DaprEventBufferState";
    private Queue<ProcessEvent>? _queue = new();

    /// <summary>
    /// Required constructor for Dapr Actor.
    /// </summary>
    /// <param name="host">The actor host.</param>
    public EventBufferActor(ActorHost host) : base(host)
    {
    }

    /// <summary>
    /// Dequeues an event.
    /// </summary>
    /// <returns>A <see cref="List{T}"/> where T is <see cref="ProcessEvent"/></returns>
    public async Task<List<ProcessEvent>> DequeueAllAsync()
    {
        // Dequeue and clear the queue.
        var items = this._queue!.ToList();
        this._queue!.Clear();

        // Save the state.
        await this.StateManager.SetStateAsync(EventQueueState, this._queue).ConfigureAwait(false);
        await this.StateManager.SaveStateAsync().ConfigureAwait(false);

        return items;
    }

    public async Task EnqueueAsync(ProcessEvent stepEvent)
    {
        this._queue!.Enqueue(stepEvent);

        // Save the state.
        await this.StateManager.SetStateAsync(EventQueueState, this._queue).ConfigureAwait(false);
        await this.StateManager.SaveStateAsync().ConfigureAwait(false);
    }

    /// <summary>
    /// Called when the actor is activated. Used to initialize the state of the actor.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    protected override async Task OnActivateAsync()
    {
        var eventQueueState = await this.StateManager.TryGetStateAsync<Queue<ProcessEvent>>(EventQueueState).ConfigureAwait(false);
        if (eventQueueState.HasValue)
        {
            this._queue = eventQueueState.Value;
        }
        else
        {
            this._queue = new Queue<ProcessEvent>();
        }
    }
}
