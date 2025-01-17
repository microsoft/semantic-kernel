// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides step related functionality for Kernel Functions running in a step.
/// </summary>
public sealed class KernelProcessStepContext
{
    private readonly IKernelProcessMessageChannel _stepMessageChannel;
    private readonly IExternalKernelProcessMessageChannelEmitter? _externalMessageChannel;

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessStepContext"/> class.
    /// </summary>
    /// <param name="channel">An instance of <see cref="IKernelProcessMessageChannel"/>.</param>
    /// <param name="externalMessageChannel">An instance of <see cref="IExternalKernelProcessMessageChannelEmitter"/></param>
    public KernelProcessStepContext(IKernelProcessMessageChannel channel, IExternalKernelProcessMessageChannelEmitter? externalMessageChannel = null)
    {
        this._stepMessageChannel = channel;
        this._externalMessageChannel = externalMessageChannel;
    }

    /// <summary>
    /// Emit an SK process event from the current step.
    /// </summary>
    /// <param name="processEvent">An instance of <see cref="KernelProcessEvent"/> to be emitted from the <see cref="KernelProcessStep"/></param>
    /// <returns>A <see cref="ValueTask"/></returns>
    public ValueTask EmitEventAsync(KernelProcessEvent processEvent)
    {
        return this._stepMessageChannel.EmitEventAsync(processEvent);
    }

    /// <summary>
    /// Emit an SK process event from the current step with a simplified method signature.
    /// </summary>
    /// <param name="eventId"></param>
    /// <param name="data"></param>
    /// <param name="visibility"></param>
    /// <returns></returns>
    public ValueTask EmitEventAsync(
        string eventId,
        object? data = null,
        KernelProcessEventVisibility visibility = KernelProcessEventVisibility.Internal)
    {
        Verify.NotNullOrWhiteSpace(eventId, nameof(eventId));

        return this._stepMessageChannel.EmitEventAsync(
            new KernelProcessEvent
            {
                Id = eventId,
                Data = data,
                Visibility = visibility
            });
    }

    /// <summary>
    /// Emit an external event to through a <see cref="IExternalKernelProcessMessageChannelEmitter"/>
    /// componenet if connected from within the SK process
    /// </summary>
    /// <param name="externalTopicName"></param>
    /// <param name="processEventData"></param>
    /// <returns></returns>
    /// <exception cref="KernelException"></exception>
    public async Task EmitExternalEventAsync(string externalTopicName, object? processEventData = null)
    {
        if (this._externalMessageChannel == null)
        {
            throw new KernelException($"External message channel not configured for step with topic {externalTopicName}");
        }

        await this._externalMessageChannel.EmitExternalEventAsync(externalTopicName, processEventData).ConfigureAwait(false);
    }
}
