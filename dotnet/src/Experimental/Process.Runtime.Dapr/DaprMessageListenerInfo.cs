// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A serializable representation of a Dapr Message Listener.
/// </summary>
[KnownType(typeof(KernelProcessEdge))]
[KnownType(typeof(KernelProcessMapState))]
[KnownType(typeof(KernelProcessStepState))]
[KnownType(typeof(KernelProcessStepState<>))]
[KnownType(typeof(KernelProcessMessageSource))]
public record DaprMessageListenerInfo : DaprStepInfo
{
    /// <summary>
    /// Gets the list of message sources that this event listener is listening to.
    /// </summary>
    public required List<KernelProcessMessageSource> MessageSources { get; init; }

    /// <summary>
    /// Gets the unique identifier of the destination step that this event listener routes messages to.
    /// </summary>
    public required string DestinationStepId { get; init; }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessEventListener"/> class from this instance of <see cref="KernelProcessEventListener"/>.
    /// </summary>
    /// <returns>An instance of <see cref="KernelProcessEventListener"/></returns>
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

        return new()
        {
            InnerStepDotnetType = proxyStepInfo.InnerStepDotnetType,
            State = proxyStepInfo.State,
            Edges = proxyStepInfo.Edges,
            MessageSources = kernelEventListenerInfo.MessageSources,
            DestinationStepId = kernelEventListenerInfo.DestinationStepId
        };
    }
}
