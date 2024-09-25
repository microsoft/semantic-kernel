// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// An abstract class that represents a channel for emitting messages from a step.
/// </summary>
public abstract class KernelProcessMessageChannel
{
    /// <summary>
    /// Emits the specified event from the step.
    /// </summary>
    /// <param name="processEvent">The event to emit.</param>
    /// <returns>A <see cref="ValueTask"/></returns>
    public abstract ValueTask EmitEventAsync(KernelProcessEvent processEvent);
}
