// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Dapr.Actors;
using Microsoft.SemanticKernel.Process.Runtime;

namespace Microsoft.SemanticKernel;

/// <summary>
/// An interface for a buffer of <see cref="ProcessEvent"/>s.
/// </summary>
public interface IEventBuffer : IActor
{
    /// <summary>
    /// Enqueues an external event.
    /// </summary>
    /// <param name="stepEvent">The event to enqueue as JSON.</param>
    /// <returns>A <see cref="Task"/></returns>
    Task EnqueueAsync(string stepEvent);

    /// <summary>
    /// Dequeues all external events.
    /// </summary>
    /// <returns>A <see cref="IList{T}"/> where T is the JSON representation of a <see cref="ProcessEvent"/></returns>
    Task<IList<string>> DequeueAllAsync();
}
