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
    /// <param name="externalEvent">The external event to enqueue as JSON.</param>
    /// <returns>A <see cref="Task"/></returns>
    Task EnqueueAsync(string externalEvent);

    /// <summary>
    /// Dequeues all external events.
    /// </summary>
    /// <returns>A <see cref="IList{T}"/> where T is the JSON representation of a <see cref="KernelProcessEvent"/></returns>
    Task<IList<string>> DequeueAllAsync();
}
