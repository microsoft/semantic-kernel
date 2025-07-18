// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.Serialization;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Class used to allow using <see cref="IExternalEventBuffer"/> as <see cref="IExternalKernelProcessMessageChannel"/>
/// in SK Process shared abstractions
/// </summary>
[KnownType(typeof(KernelProcessProxyMessage))]
public class ExternalMessageBufferActorWrapper : IExternalKernelProcessMessageChannel
{
    private readonly IExternalMessageBuffer _actor;

    /// <summary>
    /// Constructor to wrap <see cref="IExternalMessageBuffer"/> as <see cref="IExternalKernelProcessMessageChannel"/>
    /// </summary>
    /// <param name="actor">The actor host.</param>
    public ExternalMessageBufferActorWrapper(IExternalMessageBuffer actor)
    {
        this._actor = actor;
    }

    /// <inheritdoc cref="IExternalMessageBuffer.EmitExternalEventAsync(string, KernelProcessProxyMessage)"/>
    public async Task EmitExternalEventAsync(string externalTopicEvent, KernelProcessProxyMessage message)
    {
        await this._actor.EmitExternalEventAsync(externalTopicEvent, message).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public ValueTask Initialize()
    {
        // When using Dapr initialization is already taken care of by Dapr Actors
        throw new System.NotImplementedException();
    }

    /// <inheritdoc/>
    public ValueTask Uninitialize()
    {
        // When using Dapr uninitialization is already taken care of by Dapr Actors
        throw new System.NotImplementedException();
    }
}
