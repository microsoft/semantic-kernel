// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Dapr.Actors;
using Dapr.Actors.Client;
using Microsoft.SemanticKernel.Process;
using Microsoft.SemanticKernel.Process.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A context for a Dapr kernel process.
/// </summary>
public class DaprKernelProcessContext : KernelProcessContext
{
    private readonly IProcess _daprProcess;
    private readonly KernelProcess _process;

    internal DaprKernelProcessContext(KernelProcess process, IActorProxyFactory? actorProxyFactory = null)
    {
        Verify.NotNull(process);
        Verify.NotNullOrWhiteSpace(process.State?.StepId);

        if (string.IsNullOrWhiteSpace(process.State.RunId))
        {
            process = process with { State = process.State with { RunId = Guid.NewGuid().ToString() } };
        }

        this._process = process;
        var processId = new ActorId(process.State.RunId);

        // For a non-dependency-injected application, the static methods on ActorProxy are used.
        // Since the ActorProxy methods are error prone, try to avoid using them when using
        // dependency-injected applications
        if (actorProxyFactory != null)
        {
            this._daprProcess = actorProxyFactory.CreateActorProxy<IProcess>(processId, nameof(ProcessActor));
        }
        else
        {
            this._daprProcess = ActorProxy.Create<IProcess>(processId, nameof(ProcessActor));
        }
    }

    /// <summary>
    /// Starts the process with an initial event.
    /// </summary>
    /// <param name="key">The registration key of the Process to be run.</param>
    /// <param name="processId">The unique Id of the process to be run.</param>
    /// <param name="initialEvent">The initial event.</param>
    /// <param name="eventProxyStepId">The id of the event proxy.</param>
    /// <returns></returns>
    internal async Task KeyedStartWithEventAsync(string key, string processId, KernelProcessEvent initialEvent, ActorId? eventProxyStepId = null)
    {
        await this._daprProcess.KeyedRunOnceAsync(key, processId, "", eventProxyStepId?.GetId(), initialEvent.ToJson()).ConfigureAwait(false);
    }

    /// <summary>
    /// Sends a message to the process.
    /// </summary>
    /// <param name="processEvent">The event to sent to the process.</param>
    /// <returns>A <see cref="Task"/></returns>
    public override async Task SendEventAsync(KernelProcessEvent processEvent) =>
        await this._daprProcess.SendMessageAsync(processEvent.ToJson()).ConfigureAwait(false);

    /// <summary>
    /// Stops the process.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    public override async Task StopAsync() => await this._daprProcess.StopAsync().ConfigureAwait(false);

    /// <summary>
    /// Gets a snapshot of the step states.
    /// </summary>
    public override async Task<IDictionary<string, KernelProcessStepState>> GetStepStatesAsync()
    {
        IDictionary<string, KernelProcessStepState> stepStates = await this._daprProcess.GetProcessInfoAsync().ConfigureAwait(false);
        return stepStates;
    }

    /// <summary>
    /// Gets a snapshot of the current state of the process.
    /// </summary>
    /// <returns>A <see cref="Task{T}"/> where T is <see cref="KernelProcess"/></returns>
    public override async Task<KernelProcess> GetStateAsync()
    {
        IDictionary<string, KernelProcessStepState> stepStates = await this._daprProcess.GetProcessInfoAsync().ConfigureAwait(false);

        // Build the process with the new state
        List<KernelProcessStepInfo> kernelProcessSteps = [];

        foreach (var step in this._process.Steps)
        {
            kernelProcessSteps.Add(step with { State = stepStates[step.State.StepId] });
        }

        return this._process with { Steps = kernelProcessSteps };
    }

    /// <inheritdoc/>
    public override Task<IExternalKernelProcessMessageChannel?> GetExternalMessageChannelAsync()
    {
        throw new NotImplementedException();
    }

    /// <inheritdoc/>
    public override async Task<string> GetProcessIdAsync()
    {
        var processInfo = await this.GetStateAsync().ConfigureAwait(false);
        return processInfo.State.RunId!;
    }
}
