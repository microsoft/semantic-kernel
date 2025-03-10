// Copyright (c) Microsoft. All rights reserved.
using System.Runtime.Serialization;
using Microsoft.SemanticKernel.Process.Models;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A serializable representation of a Dapr Proxy.
/// </summary>
[KnownType(typeof(KernelProcessEdge))]
[KnownType(typeof(KernelProcessStepState))]
[KnownType(typeof(KernelProcessStepState<>))]
public sealed record DaprProxyInfo : DaprStepInfo
{
    /// <summary>
    /// Proxy related data to be able to emit the events externally
    /// </summary>
    public required KernelProcessProxyStateMetadata? ProxyMetadata { get; init; }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessMap"/> class from this instance of <see cref="DaprMapInfo"/>.
    /// </summary>
    /// <returns>An instance of <see cref="KernelProcessMap"/></returns>
    /// <exception cref="KernelException"></exception>
    public KernelProcessProxy ToKernelProcessProxy()
    {
        KernelProcessStepInfo processStepInfo = this.ToKernelProcessStepInfo();
        if (this.State is not KernelProcessStepState state)
        {
            throw new KernelException($"Unable to read state from proxy with name '{this.State.Name}', Id '{this.State.Id}' and type {this.State.GetType()}.");
        }

        return new KernelProcessProxy(state, this.Edges)
        {
            ProxyMetadata = this.ProxyMetadata,
        };
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="DaprProxyInfo"/> class from an instance of <see cref="KernelProcessProxy"/>.
    /// </summary>
    /// <param name="kernelProxyInfo">The <see cref="KernelProcessProxy"/> used to build the <see cref="DaprProxyInfo"/></param>
    /// <returns></returns>
    public static DaprProxyInfo FromKernelProxyInfo(KernelProcessProxy kernelProxyInfo)
    {
        Verify.NotNull(kernelProxyInfo, nameof(kernelProxyInfo));

        DaprStepInfo proxyStepInfo = DaprStepInfo.FromKernelStepInfo(kernelProxyInfo);

        return new DaprProxyInfo
        {
            InnerStepDotnetType = proxyStepInfo.InnerStepDotnetType,
            State = proxyStepInfo.State,
            Edges = proxyStepInfo.Edges,
            ProxyMetadata = kernelProxyInfo.ProxyMetadata,
        };
    }
}
