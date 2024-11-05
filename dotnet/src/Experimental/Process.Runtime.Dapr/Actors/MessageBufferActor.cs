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
internal class MessageBufferActor : Actor, IMessageBuffer
{
    private List<ProcessMessage> _queue = [];

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
    /// <returns>A <see cref="List{T}"/> where T is <see cref="ProcessEvent"/></returns>
    public async Task<IList<ProcessMessage>> DequeueAllAsync()
    {
        // Dequeue and clear the queue.
        ProcessMessage[] items = [.. this._queue];
        this._queue.Clear();

        // Save the state.
        await this.StateManager.SetStateAsync(ActorStateKeys.MessageQueueState, ProcessMessageSerializer.Write(this._queue)).ConfigureAwait(false);
        await this.StateManager.SaveStateAsync().ConfigureAwait(false);

        return items;
    }

    public async Task EnqueueAsync(ProcessMessage message)
    {
        this._queue.Add(message);

        // Save the state.
        await this.StateManager.SetStateAsync(ActorStateKeys.MessageQueueState, ProcessMessageSerializer.Write(this._queue)).ConfigureAwait(false);
        await this.StateManager.SaveStateAsync().ConfigureAwait(false);
    }

    /// <summary>
    /// Called when the actor is activated. Used to initialize the state of the actor.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    protected override async Task OnActivateAsync()
    {
        var eventQueueState = await this.StateManager.TryGetStateAsync<string>(ActorStateKeys.MessageQueueState).ConfigureAwait(false);
        if (eventQueueState.HasValue)
        {
            this._queue = ProcessMessageSerializer.Read(eventQueueState.Value).ToList();
        }
        else
        {
            this._queue = [];
        }
    }
}
