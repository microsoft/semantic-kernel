// Copyright (c) Microsoft. All rights reserved.
using System.Runtime.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A serializable representation of a Dapr Map.
/// </summary>
[KnownType(typeof(KernelProcessEdge))]
[KnownType(typeof(KernelProcessMapState))]
[KnownType(typeof(KernelProcessStepState))]
[KnownType(typeof(KernelProcessStepState<>))]
public sealed record DaprMapInfo : DaprStepInfo
{
    /// <summary>
    /// The map operation
    /// </summary>
    public required DaprProcessInfo MapStep { get; init; }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessMap"/> class from this instance of <see cref="DaprMapInfo"/>.
    /// </summary>
    /// <returns>An instance of <see cref="KernelProcessMap"/></returns>
    /// <exception cref="KernelException"></exception>
    public KernelProcessMap ToKernelProcessMap()
    {
        var processStepInfo = this.ToKernelProcessStepInfo();
        if (this.State is not KernelProcessMapState state)
        {
            throw new KernelException($"Unable to read state from map with name '{this.State.Name}' and Id '{this.State.Id}'.");
        }

        KernelProcess mapOperation = this.MapStep.ToKernelProcess();

        return new KernelProcessMap(state, mapOperation, this.Edges);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="DaprMapInfo"/> class from an instance of <see cref="KernelProcessMap"/>.
    /// </summary>
    /// <param name="processMap">The <see cref="KernelProcessMap"/> used to build the <see cref="DaprMapInfo"/></param>
    /// <returns>An instance of <see cref="DaprProcessInfo"/></returns>
    public static DaprMapInfo FromKernelProcessMap(KernelProcessMap processMap)
    {
        Verify.NotNull(processMap);

        DaprStepInfo daprStepInfo = DaprStepInfo.FromKernelStepInfo(processMap);

        DaprProcessInfo daprProcess = DaprProcessInfo.FromKernelProcess(processMap.Operation);

        return new DaprMapInfo
        {
            InnerStepDotnetType = daprStepInfo.InnerStepDotnetType,
            State = daprStepInfo.State,
            Edges = daprStepInfo.Edges,
            MapStep = daprProcess,
        };
    }
}
