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
    private readonly KernelProcess _process;

    internal DaprKernelProcessContext(KernelProcess process)
    {
        Verify.NotNull(process);
        Verify.NotNullOrWhiteSpace(process.State?.Name);

        if (string.IsNullOrWhiteSpace(process.State.Id))
        {
            process = process with { State = process.State with { Id = Guid.NewGuid().ToString() } };
        }

        this._process = process;
        var processId = new ActorId(process.State.Id);
        this._daprProcess = ActorProxy.Create<IProcess>(processId, nameof(ProcessActor));
    }

    /// <summary>
    /// Starts the process with an initial event.
    /// </summary>
    /// <param name="initialEvent">The initial event.</param>
    /// <returns></returns>
    internal async Task StartWithEventAsync(KernelProcessEvent initialEvent)
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
