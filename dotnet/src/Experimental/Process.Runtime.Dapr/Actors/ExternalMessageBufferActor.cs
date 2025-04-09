// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Dapr.Actors.Runtime;

namespace Microsoft.SemanticKernel;

/// <summary>
/// An actor that represents en external event messaging buffer.
/// </summary>
internal sealed class ExternalMessageBufferActor : Actor, IExternalMessageBuffer
{
    private readonly IExternalKernelProcessMessageChannel _externalMessageChannel;

    /// <summary>
    /// Required constructor for Dapr Actor.
    /// </summary>
    /// <param name="host">The actor host.</param>
    /// <param name="externalMessageChannel">Instance of <see cref="IExternalKernelProcessMessageChannel"/></param>
    public ExternalMessageBufferActor(ActorHost host, IExternalKernelProcessMessageChannel externalMessageChannel) : base(host)
    {
        this._externalMessageChannel = externalMessageChannel;
    }

    public async Task EmitExternalEventAsync(string externalTopicEvent, KernelProcessProxyMessage eventData)
    {
        await this._externalMessageChannel.EmitExternalEventAsync(externalTopicEvent, eventData).ConfigureAwait(false);
    }

    protected override async Task OnDeactivateAsync()
    {
        await this._externalMessageChannel.Uninitialize().ConfigureAwait(false);
    }

    protected override async Task OnActivateAsync()
    {
        await this._externalMessageChannel.Initialize().ConfigureAwait(false);
    }
}
