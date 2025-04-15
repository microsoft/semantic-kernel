// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Process;

/// <summary>
/// Represents the context of a running process.
/// </summary>
public abstract class KernelProcessContext
{
    /// <summary>
    /// Sends a message to the process.
    /// </summary>
    /// <param name="processEvent">The event to sent to the process.</param>
    /// <returns>A <see cref="Task"/></returns>
    public abstract Task SendEventAsync(KernelProcessEvent processEvent);

    /// <summary>
    /// Stops the process.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    public abstract Task StopAsync();

    /// <summary>
    /// Gets a snapshot of the current state of the process.
    /// </summary>
    /// <returns>A <see cref="Task{T}"/> where T is <see cref="KernelProcess"/></returns>
    public abstract Task<KernelProcess> GetStateAsync();

    /// <summary>
    /// Gets the instance of <see cref="IExternalKernelProcessMessageChannel"/> used for external messages
    /// </summary>
    /// <returns></returns>
    public abstract Task<IExternalKernelProcessMessageChannel?> GetExternalMessageChannelAsync();

    /// <summary>
    /// Gets the id of the running process instance
    /// </summary>
    /// <returns></returns>
    public abstract Task<string> GetProcessIdAsync();
}
