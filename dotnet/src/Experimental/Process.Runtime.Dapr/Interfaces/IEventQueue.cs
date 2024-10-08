// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Dapr.Actors;

namespace Microsoft.SemanticKernel;

/// <summary>
/// An interface for an event queue.
/// </summary>
public interface IEventQueue : IActor
{
    Task EnqueueAsync(DaprEvent stepEvent);

    Task<List<DaprEvent>> DequeueAllAsync();
}
