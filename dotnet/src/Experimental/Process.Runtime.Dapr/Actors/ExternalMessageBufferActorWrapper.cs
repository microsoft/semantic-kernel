// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Class used to allow using <see cref="IExternalEventBuffer"/> as <see cref="IExternalKernelProcessMessageChannelEmitter"/>
/// in SK Process shared abstractions
/// </summary>
public class ExternalMessageBufferActorWrapper : IExternalKernelProcessMessageChannelEmitter
{
    private readonly IExternalMessageBuffer _actor;

    public ExternalMessageBufferActorWrapper(IExternalMessageBuffer actor)
    {
        this._actor = actor;
    }

    public async Task EmitExternalEventAsync(string externalTopicEvent, object? eventData)
    {
        await this._actor.EmitExternalEventAsync(externalTopicEvent, eventData).ConfigureAwait(false);
    }
}
