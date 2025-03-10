// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Process;
using Microsoft.VisualStudio.Threading;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides context and actions on a process that is running locally.
/// </summary>
public sealed class LocalKernelProcessContext : KernelProcessContext, IDisposable
{
    private readonly JoinableTaskFactory _joinableTaskFactory;
    private readonly JoinableTaskContext _joinableTaskContext;

    private readonly LocalProcess _localProcess;
    private readonly Kernel _kernel;

    internal LocalKernelProcessContext(KernelProcess process, Kernel kernel, ProcessEventProxy? eventProxy = null, IExternalKernelProcessMessageChannel? externalMessageChannel = null)
    {
        Verify.NotNull(process, nameof(process));
        Verify.NotNull(kernel, nameof(kernel));
        Verify.NotNullOrWhiteSpace(process.State?.Name);

        this._kernel = kernel;
        this._localProcess = new LocalProcess(process, kernel)
        {
            EventProxy = eventProxy,
            ExternalMessageChannel = externalMessageChannel,
        };

        this._joinableTaskContext = new JoinableTaskContext();
        this._joinableTaskFactory = new JoinableTaskFactory(this._joinableTaskContext);
    }

    internal Task StartWithEventAsync(KernelProcessEvent initialEvent, Kernel? kernel = null) =>
        this._localProcess.RunOnceAsync(initialEvent, kernel);

    /// <summary>
    /// Sends a message to the process.
    /// </summary>
    /// <param name="processEvent">The event to sent to the process.</param>
    /// <returns>A <see cref="Task"/></returns>
    public override Task SendEventAsync(KernelProcessEvent processEvent) =>
        this._localProcess.SendMessageAsync(processEvent);

    /// <summary>
    /// Stops the process.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    public override Task StopAsync() => this._localProcess.StopAsync();

    /// <summary>
    /// Gets a snapshot of the current state of the process.
    /// </summary>
    /// <returns>A <see cref="Task{T}"/> where T is <see cref="KernelProcess"/></returns>
    public override Task<KernelProcess> GetStateAsync() => this._localProcess.GetProcessInfoAsync();

    /// <summary>
    /// Disposes of the resources used by the process.
    /// </summary>
    public void Dispose()
    {
        this._joinableTaskFactory.Run(() => this._localProcess.DisposeAsync().AsTask());
        this._joinableTaskContext.Dispose();
    }

    /// <inheritdoc/>
    public override Task<IExternalKernelProcessMessageChannel?> GetExternalMessageChannelAsync()
    {
        return Task.FromResult(this._localProcess.ExternalMessageChannel);
    }

    /// <inheritdoc/>
    public override Task<string> GetProcessIdAsync() => Task.FromResult(this._localProcess.Id);
}
