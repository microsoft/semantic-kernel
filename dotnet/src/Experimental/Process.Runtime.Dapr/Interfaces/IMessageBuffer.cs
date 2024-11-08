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
    /// <param name="message">The message to enqueue as JSON.</param>
    /// <returns>A <see cref="Task"/></returns>
    Task EnqueueAsync(string message);

    /// <summary>
    /// Dequeues all external events.
    /// </summary>
    /// <returns>A <see cref="IList{T}"/> where T is the JSON representation of a <see cref="ProcessMessage"/></returns>
    Task<IList<string>> DequeueAllAsync();
}
