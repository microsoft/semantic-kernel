// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Dapr.Actors;

namespace Microsoft.SemanticKernel;

/// <summary>
/// An interface for a buffer of <see cref="DaprMessage"/>s.
/// </summary>
public interface IMessageBuffer : IActor
{
    /// <summary>
    /// Enqueues an external event.
    /// </summary>
    /// <param name="message">The message to enqueue.</param>
    /// <returns>A <see cref="Task"/></returns>
    Task EnqueueAsync(DaprMessage message);

    /// <summary>
    /// Dequeues all external events.
    /// </summary>
    /// <returns>A <see cref="List{T}"/> where T is <see cref="DaprMessage"/></returns>
    Task<List<DaprMessage>> DequeueAllAsync();
}
