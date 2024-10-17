// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Dapr.Actors;

namespace Microsoft.SemanticKernel;

/// <summary>
/// An interface for a buffer of <see cref="KernelProcessEvent"/>s.
/// </summary>
public interface IExternalEventBuffer : IActor
{
    /// <summary>
    /// Enqueues an external event.
    /// </summary>
    /// <param name="externalEvent">The external event to enqueue.</param>
    /// <returns>A <see cref="Task"/></returns>
    Task EnqueueAsync(KernelProcessEvent externalEvent);

    /// <summary>
    /// Dequeues all external events.
    /// </summary>
    /// <returns>A <see cref="List{T}"/> where T is <see cref="KernelProcessEvent"/></returns>
    Task<List<KernelProcessEvent>> DequeueAllAsync();
}
