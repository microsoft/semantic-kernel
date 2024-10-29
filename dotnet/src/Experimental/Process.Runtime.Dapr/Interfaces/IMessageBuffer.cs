// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Dapr.Actors;
using Microsoft.SemanticKernel.Process.Runtime;

namespace Microsoft.SemanticKernel;

/// <summary>
/// An interface for a buffer of <see cref="ProcessMessage"/>s.
/// </summary>
public interface IMessageBuffer : IActor
{
    /// <summary>
    /// Enqueues an external event.
    /// </summary>
    /// <param name="message">The message to enqueue.</param>
    /// <returns>A <see cref="Task"/></returns>
    Task EnqueueAsync(ProcessMessage message);

    /// <summary>
    /// Dequeues all external events.
    /// </summary>
    /// <returns>A <see cref="List{T}"/> where T is <see cref="ProcessMessage"/></returns>
    Task<List<ProcessMessage>> DequeueAllAsync();
}
