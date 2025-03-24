// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides step related functionality for Kernel Functions running in a step to emit events externally.
/// </summary>
public class KernelProcessStepExternalContext
{
    private readonly IExternalKernelProcessMessageChannel? _externalMessageChannel;

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessStepContext"/> class.
    /// </summary>
    /// <param name="externalMessageChannel">An instance of <see cref="IExternalKernelProcessMessageChannel"/></param>
    public KernelProcessStepExternalContext(IExternalKernelProcessMessageChannel? externalMessageChannel = null)
    {
        this._externalMessageChannel = externalMessageChannel;
    }

    /// <summary>
    /// Emit an external event to through a <see cref="IExternalKernelProcessMessageChannel"/>
    /// component if connected from within the SK process
    /// </summary>
    /// <param name="processEventData">data containing event details</param>
    /// <returns></returns>
    /// <exception cref="KernelException"></exception>
    public async Task EmitExternalEventAsync(KernelProcessProxyMessage processEventData)
    {
        if (this._externalMessageChannel == null)
        {
            throw new KernelException($"External message channel not configured for step with topic {processEventData.ExternalTopicName}");
        }

        await this._externalMessageChannel.EmitExternalEventAsync(processEventData.ExternalTopicName, processEventData).ConfigureAwait(false);
    }

    /// <summary>
    /// Closes connection with external messaging channel
    /// </summary>
    /// <returns><see cref="Task"/></returns>
    /// <exception cref="KernelException"></exception>
    public async Task CloseExternalEventChannelAsync()
    {
        if (this._externalMessageChannel == null)
        {
            throw new KernelException("External message channel not configured for step");
        }

        await this._externalMessageChannel.Uninitialize().ConfigureAwait(false);
    }
}
