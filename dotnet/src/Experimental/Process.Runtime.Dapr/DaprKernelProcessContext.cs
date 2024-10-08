// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Dapr.Actors;
using Dapr.Actors.Client;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A context for a Dapr kernel process.
/// </summary>
public class DaprKernelProcessContext
{
    private readonly IProcess _daprProcess;
    private readonly Kernel _kernel;
    private readonly KernelProcess _process;

    internal DaprKernelProcessContext(KernelProcess process, Kernel kernel)
    {
        Verify.NotNull(process);
        Verify.NotNullOrWhiteSpace(process.State?.Name);
        Verify.NotNull(kernel);

        if (string.IsNullOrWhiteSpace(process.State.Id))
        {
            process = process with { State = process.State with { Id = Guid.NewGuid().ToString() } };
        }

        this._process = process;
        this._kernel = kernel;
        var processId = new ActorId(process.State.Id);
        this._daprProcess = ActorProxy.Create<IProcess>(processId, nameof(ProcessActor));
    }

    internal async Task StartWithEventAsync(KernelProcessEvent initialEvent, Kernel? kernel = null)
    {
        var daprProcess = DaprProcessInfo.FromKernelProcess(this._process);
        await this._daprProcess.InitializeProcessAsync(daprProcess, null).ConfigureAwait(false);
        await this._daprProcess.RunOnceAsync(initialEvent).ConfigureAwait(false);
    }

    /// <summary>
    /// Sends a message to the process.
    /// </summary>
    /// <param name="processEvent">The event to sent to the process.</param>
    /// <returns>A <see cref="Task"/></returns>
    public async Task SendEventAsync(KernelProcessEvent processEvent) =>
        await this._daprProcess.SendMessageAsync(processEvent).ConfigureAwait(false);

    /// <summary>
    /// Stops the process.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    public async Task StopAsync() => await this._daprProcess.StopAsync().ConfigureAwait(false);

    /// <summary>
    /// Gets a snapshot of the current state of the process.
    /// </summary>
    /// <returns>A <see cref="Task{T}"/> where T is <see cref="KernelProcess"/></returns>
    public async Task<KernelProcess> GetStateAsync()
    {
        var daprProcessInfo = await this._daprProcess.GetProcessInfoAsync().ConfigureAwait(false);
        return daprProcessInfo.ToKernelProcess();
    }
}
