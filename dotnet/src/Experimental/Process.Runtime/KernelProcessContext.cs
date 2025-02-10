// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Threading.Tasks;
using Microsoft.AutoGen.Contracts;
using IKernelProcessContext = Microsoft.SemanticKernel.Process.KernelProcessContext;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides context and actions on a process that is running locally.
/// </summary>
public sealed class KernelProcessContext : IKernelProcessContext, IDisposable
{
    private readonly RuntimeProcess _process;

    internal KernelProcessContext(
        KernelProcess process,
        Kernel kernel,
        IAgentRuntime runtime,
        ProcessEventProxy? eventProxy = null,
        IExternalKernelProcessMessageChannel? externalMessageChannel = null)
    {
        Verify.NotNull(process, nameof(process));
        Verify.NotNull(kernel, nameof(kernel));
        Verify.NotNullOrWhiteSpace(process.State?.Name);

        // %%% HACK: RuntimeStep constructor (see note)
        if (string.IsNullOrEmpty(process.State.Id))
        {
            process = process with { State = process.State with { Id = Guid.NewGuid().ToString() } };
        }

        this._process =
            new RuntimeProcess(process, kernel, runtime)
            {
                EventProxy = eventProxy,
                ExternalMessageChannel = externalMessageChannel,
            };
    }

    /// <summary>
    /// Disposes of the resources used by the process.
    /// </summary>
    public void Dispose() => this._process.Dispose();

    /// <summary>
    /// Sends a message to the process.
    /// </summary>
    /// <param name="processEvent">The event to sent to the process.</param>
    /// <returns>A <see cref="Task"/></returns>
    public override Task SendEventAsync(KernelProcessEvent processEvent) =>
        this._process.SendMessageAsync(processEvent);

    /// <summary>
    /// Stops the process.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    public override Task StopAsync() => this._process.StopAsync();

    /// <summary>
    /// Gets a snapshot of the current state of the process.
    /// </summary>
    /// <returns>A <see cref="Task{T}"/> where T is <see cref="KernelProcess"/></returns>
    public override Task<KernelProcess> GetStateAsync() => this._process.GetProcessInfoAsync();

    /// <inheritdoc/>
    public override Task<IExternalKernelProcessMessageChannel?> GetExternalMessageChannelAsync()
    {
        return Task.FromResult(this._process.ExternalMessageChannel);
    }

    internal Task StartWithEventAsync(KernelProcessEvent initialEvent, Kernel? kernel = null) =>
        this._process.RunOnceAsync(initialEvent, kernel);
}
