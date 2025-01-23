// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides step related functionality for Kernel Functions running in a step.
/// </summary>
public sealed class KernelProcessProxyStepExternalContext
{
    private readonly IKernelExternalMessageChannel _stepMessageChannel;

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessStepContext"/> class.
    /// </summary>
    /// <param name="channel">An instance of <see cref="IKernelExternalMessageChannel"/>.</param>
    public KernelProcessProxyStepExternalContext(IKernelExternalMessageChannel channel)
    {
        this._stepMessageChannel = channel;
    }

    public ValueTask EmitExternalEventAsync(string externalEventName, object? externalEventData = null)
    {
        return this._stepMessageChannel.EmitExternalEventAsync(externalEventName, externalEventData);
    }

    public ValueTask SubscribeToExternalEventAsync(string externalEventName, int timeoutInMilliseconds = 10000)
    {
        return this._stepMessageChannel.SubscribeToExternalEventAsync(externalEventName);
    }

    public ValueTask UnsubscribeToExternalEventAsync(string externalEventName)
    {
        return this._stepMessageChannel.UnsubscribeToExternalEventAsync(externalEventName);
    }
}
