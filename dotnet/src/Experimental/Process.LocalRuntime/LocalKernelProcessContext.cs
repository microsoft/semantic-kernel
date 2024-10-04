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

    internal LocalKernelProcessContext(KernelProcess process, Kernel kernel)
    {
        Verify.NotNull(process);
        Verify.NotNullOrWhiteSpace(process.State?.Name);
        Verify.NotNull(kernel);

        this._kernel = kernel;
        this._localProcess = new LocalProcess(
            process,
            kernel: kernel,
            parentProcessId: null,
            loggerFactory: null);
    }

    internal async Task StartWithEventAsync(KernelProcessEvent? initialEvent, Kernel? kernel = null)
    {
        await this._localProcess.RunOnceAsync(initialEvent).ConfigureAwait(false);
    }

    /// <summary>
    /// Sends a message to the process.
    /// </summary>
    /// <param name="processEvent">The event to sent to the process.</param>
    /// <returns>A <see cref="Task"/></returns>
    public async Task SendEventAsync(KernelProcessEvent processEvent) =>
        await this._localProcess.SendMessageAsync(processEvent).ConfigureAwait(false);

    /// <summary>
    /// Stops the process.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    public async Task StopAsync() => await this._localProcess.StopAsync().ConfigureAwait(false);

    /// <summary>
    /// Gets a snapshot of the current state of the process.
    /// </summary>
    /// <returns>A <see cref="Task{T}"/> where T is <see cref="KernelProcess"/></returns>
    public async Task<KernelProcess> GetStateAsync() => await this._localProcess.GetProcessInfoAsync().ConfigureAwait(false);

    /// <summary>
    /// Disposes of the resources used by the process.
    /// </summary>
    public void Dispose() => this._localProcess?.Dispose();
}
