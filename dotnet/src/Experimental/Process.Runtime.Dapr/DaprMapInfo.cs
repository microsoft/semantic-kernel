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
    public required DaprStepInfo Operation { get; init; }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessMap"/> class from this instance of <see cref="DaprMapInfo"/>.
    /// </summary>
    /// <returns>An instance of <see cref="KernelProcessMap"/></returns>
    /// <exception cref="KernelException"></exception>
    public KernelProcessMap ToKernelProcessMap()
    {
        KernelProcessStepInfo processStepInfo = this.ToKernelProcessStepInfo();
        if (this.State is not KernelProcessMapState state)
        {
            throw new KernelException($"Unable to read state from map with name '{this.State.StepId}' and Id '{this.State.RunId}'.");
        }

        KernelProcessStepInfo operationStep =
            this.Operation is DaprProcessInfo processInfo
                ? processInfo.ToKernelProcess()
                : this.Operation.ToKernelProcessStepInfo();

        return new KernelProcessMap(state, operationStep, this.Edges);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="DaprMapInfo"/> class from an instance of <see cref="KernelProcessMap"/>.
    /// </summary>
    /// <param name="processMap">The <see cref="KernelProcessMap"/> used to build the <see cref="DaprMapInfo"/></param>
    /// <returns>An instance of <see cref="DaprProcessInfo"/></returns>
    public static DaprMapInfo FromKernelProcessMap(KernelProcessMap processMap)
    {
        Verify.NotNull(processMap);

        DaprStepInfo operationInfo =
            processMap.Operation is KernelProcess processOperation
                ? DaprProcessInfo.FromKernelProcess(processOperation)
                : DaprStepInfo.FromKernelStepInfo(processMap.Operation);
        DaprStepInfo mapStepInfo = DaprStepInfo.FromKernelStepInfo(processMap);

        return new DaprMapInfo
        {
            InnerStepDotnetType = mapStepInfo.InnerStepDotnetType,
            State = mapStepInfo.State,
            Edges = mapStepInfo.Edges,
            Operation = operationInfo,
        };
    }
}
