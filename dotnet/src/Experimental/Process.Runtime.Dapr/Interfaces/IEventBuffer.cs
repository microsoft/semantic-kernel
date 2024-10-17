// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Dapr.Actors;

namespace Microsoft.SemanticKernel;

/// <summary>
/// An interface for a buffer of <see cref="DaprEvent"/>s.
/// </summary>
public interface IEventBuffer : IActor
{
    /// <summary>
    /// Enqueues an external event.
    /// </summary>
    /// <param name="stepEvent">The event to enqueue.</param>
    /// <returns>A <see cref="Task"/></returns>
    Task EnqueueAsync(DaprEvent stepEvent);

    /// <summary>
    /// Dequeues all external events.
    /// </summary>
    /// <returns>A <see cref="List{T}"/> where T is <see cref="DaprEvent"/></returns>
    Task<List<DaprEvent>> DequeueAllAsync();
}
