// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Dapr.Actors;

namespace Microsoft.SemanticKernel;

/// <summary>
/// An interface for a message queue.
/// </summary>
public interface IMessageQueue : IActor
{
    Task EnqueueAsync(DaprMessage message);

    Task<List<DaprMessage>> DequeueAllAsync();
}
