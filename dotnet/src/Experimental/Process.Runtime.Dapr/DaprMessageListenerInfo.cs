// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A serializable representation of a Dapr Message Listener.
/// </summary>
[KnownType(typeof(KernelProcessEdge))]
[KnownType(typeof(KernelProcessStepState))]
[KnownType(typeof(KernelProcessStepState<>))]
internal record DaprMessageListenerInfo : DaprStepInfo
{
    private readonly List<KernelProcessMessageSource> _messageSources;
    private readonly string _destinationStepId;

    public DaprMessageListenerInfo(List<KernelProcessMessageSource> messageSources, string destinationStepId)
    {
        this._messageSources = messageSources;
        this._destinationStepId = destinationStepId;
    }

    /// <summary>
    /// Gets the list of message sources that this event listener is listening to.
    /// </summary>
    public List<KernelProcessMessageSource> MessageSources => this._messageSources;

    /// <summary>
    /// Gets the unique identifier of the destination step that this event listener routes messages to.
    /// </summary>
    public string DestinationStepId => this._destinationStepId;

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessMap"/> class from this instance of <see cref="DaprMapInfo"/>.
    /// </summary>
    /// <returns>An instance of <see cref="KernelProcessMap"/></returns>
    /// <exception cref="KernelException"></exception>
    public KernelProcessEventListener ToKernelProcessMessageListener()
    {
        KernelProcessStepInfo processStepInfo = this.ToKernelProcessStepInfo();
        if (this.State is not KernelProcessStepState state)
        {
            throw new KernelException($"Unable to read state from listener with name '{this.State.Name}', Id '{this.State.Id}' and type {this.State.GetType()}.");
        }

        return new KernelProcessEventListener(this.MessageSources, this.DestinationStepId, state, this.Edges);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="DaprProxyInfo"/> class from an instance of <see cref="KernelProcessProxy"/>.
    /// </summary>
    /// <param name="kernelEventListenerInfo">The <see cref="KernelProcessProxy"/> used to build the <see cref="DaprProxyInfo"/></param>
    /// <returns></returns>
    public static DaprMessageListenerInfo FromKernelProxyInfo(KernelProcessEventListener kernelEventListenerInfo)
    {
        Verify.NotNull(kernelEventListenerInfo, nameof(kernelEventListenerInfo));

        DaprStepInfo proxyStepInfo = DaprStepInfo.FromKernelStepInfo(kernelEventListenerInfo);

        return new DaprMessageListenerInfo(kernelEventListenerInfo.MessageSources, kernelEventListenerInfo.DestinationStepId)
        {
            InnerStepDotnetType = proxyStepInfo.InnerStepDotnetType,
            State = proxyStepInfo.State,
            Edges = proxyStepInfo.Edges
        };
    }
}
