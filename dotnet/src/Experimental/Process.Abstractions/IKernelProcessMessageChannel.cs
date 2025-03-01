// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// An interface that provides a channel for emitting messages from a step.
/// </summary>
public interface IKernelProcessMessageChannel
{
    /// <summary>
    /// Emits the specified event from the step.
    /// </summary>
    /// <param name="processEvent">The event to emit.</param>
    /// <returns>A <see cref="ValueTask"/></returns>
    abstract ValueTask EmitEventAsync(KernelProcessEvent processEvent);
}
