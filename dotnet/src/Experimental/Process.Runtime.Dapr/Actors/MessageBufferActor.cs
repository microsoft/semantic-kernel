﻿// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Dapr.Actors.Runtime;

namespace Microsoft.SemanticKernel;

/// <summary>
/// An actor that represents an external event queue.
/// </summary>
internal class MessageBufferActor : Actor, IMessageBuffer
{
    private const string EventQueueState = "DaprMessageBufferState";
    private Queue<DaprMessage>? _queue = new();

    /// <summary>
    /// Required constructor for Dapr Actor.
    /// </summary>
    /// <param name="host">The actor host.</param>
    public MessageBufferActor(ActorHost host) : base(host)
    {
    }

    /// <summary>
    /// Dequeues an event.
    /// </summary>
    /// <returns>A <see cref="List{T}"/> where T is <see cref="DaprEvent"/></returns>
    public async Task<List<DaprMessage>> DequeueAllAsync()
    {
        // Dequeue and clear the queue.
        var items = this._queue!.ToList();
        this._queue!.Clear();

        // Save the state.
        await this.StateManager.SetStateAsync(EventQueueState, this._queue).ConfigureAwait(false);
        await this.StateManager.SaveStateAsync().ConfigureAwait(false);

        return items;
    }

    public async Task EnqueueAsync(DaprMessage message)
    {
        this._queue!.Enqueue(message);

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
        var eventQueueState = await this.StateManager.TryGetStateAsync<Queue<DaprMessage>>(EventQueueState).ConfigureAwait(false);
        if (eventQueueState.HasValue)
        {
            this._queue = eventQueueState.Value;
        }
        else
        {
            this._queue = new Queue<DaprMessage>();
        }
    }
}
