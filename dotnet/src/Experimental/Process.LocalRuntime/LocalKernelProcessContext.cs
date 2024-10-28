// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides context and actions on a process that is running locally.
/// </summary>
public sealed class LocalKernelProcessContext : IDisposable
{
    private readonly LocalProcess _localProcess;
    private readonly Kernel _kernel;

    internal LocalKernelProcessContext(KernelProcess process, Kernel kernel, ProcessEventFilter? filter = null)
    {
        Verify.NotNull(kernel, nameof(kernel));
        Verify.NotNull(process, nameof(process));
        Verify.NotNullOrWhiteSpace(process.State?.Name);

        this._kernel = kernel;
        this._localProcess = new LocalProcess(
            process,
            kernel)
        {
            EventFilter = filter,
            LoggerFactory = kernel.LoggerFactory,
        };
    }

    internal Task StartWithEventAsync(KernelProcessEvent? initialEvent, Kernel? kernel = null)
    {
        return this._localProcess.RunOnceAsync(initialEvent);
    }

    /// <summary>
    /// Sends a message to the process.
    /// </summary>
    /// <param name="processEvent">The event to sent to the process.</param>
    /// <returns>A <see cref="Task"/></returns>
    public Task SendEventAsync(KernelProcessEvent processEvent) =>
        this._localProcess.SendMessageAsync(processEvent);

    /// <summary>
    /// Stops the process.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    public Task StopAsync() => this._localProcess.StopAsync();

    /// <summary>
    /// Gets a snapshot of the current state of the process.
    /// </summary>
    /// <returns>A <see cref="Task{T}"/> where T is <see cref="KernelProcess"/></returns>
    public Task<KernelProcess> GetStateAsync() => this._localProcess.GetProcessInfoAsync();

    /// <summary>
    /// Disposes of the resources used by the process.
    /// </summary>
    public void Dispose() => this._localProcess?.Dispose();
}
