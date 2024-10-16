// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Contains information about a Step in a Dapr Process including it's state and edges.
/// </summary>
[KnownType(typeof(KernelProcessEdge))]
[KnownType(typeof(KernelProcessStepState))]
public record DaprStepInfo
{
    /// <summary>
    /// The .Net type of the inner step.
    /// </summary>
    public required string InnerStepDotnetType { get; init; }

    /// <summary>
    /// The state of the Step.
    /// </summary>
    public required KernelProcessStepState State { get; init; }

    /// <summary>
    /// A read-only dictionary of output edges from the Step.
    /// </summary>
    public required Dictionary<string, List<KernelProcessEdge>> Edges { get; init; }

    /// <summary>
    /// Builds an instance of <see cref="KernelProcessStepInfo"/> from the current object.
    /// </summary>
    /// <returns>An instance of <see cref="KernelProcessStepInfo"/></returns>
    /// <exception cref="KernelException"></exception>
    public KernelProcessStepInfo ToKernelProcessStepInfo()
    {
        var innerStepType = Type.GetType(this.InnerStepDotnetType);
        if (innerStepType is null)
        {
            throw new KernelException($"Unable to create inner step type from assembly qualified name `{this.InnerStepDotnetType}`");
        }

        return new KernelProcessStepInfo(innerStepType, this.State, this.Edges);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="DaprStepInfo"/> class from an instance of <see cref="KernelProcessStepInfo"/>.
    /// </summary>
    /// <returns>An instance of <see cref="DaprStepInfo"/></returns>
    public static DaprStepInfo FromKernelStepInfo(KernelProcessStepInfo kernelStepInfo)
    {
        Verify.NotNull(kernelStepInfo);
        return new DaprStepInfo
        {
            InnerStepDotnetType = kernelStepInfo.InnerStepType.AssemblyQualifiedName!,
            State = kernelStepInfo.State,
            Edges = kernelStepInfo.Edges.ToDictionary(kvp => kvp.Key, kvp => new List<KernelProcessEdge>(kvp.Value)),
        };
    }
}
