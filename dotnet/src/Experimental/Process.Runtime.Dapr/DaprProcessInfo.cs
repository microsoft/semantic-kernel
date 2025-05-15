// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A serializable representation of a Dapr Process.
/// </summary>
[KnownType(typeof(KernelProcessEdge))]
[KnownType(typeof(KernelProcessState))]
[KnownType(typeof(KernelProcessMapState))]
[KnownType(typeof(KernelProcessStepState))]
[KnownType(typeof(KernelProcessStepState<>))]
public sealed record DaprProcessInfo : DaprStepInfo
{
    /// <summary>
    /// The collection of Steps in the Process.
    /// </summary>
    public required IList<DaprStepInfo> Steps { get; init; }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcess"/> class from this instance of <see cref="DaprProcessInfo"/>.
    /// </summary>
    /// <returns>An instance of <see cref="KernelProcess"/></returns>
    /// <exception cref="KernelException"></exception>
    public KernelProcess ToKernelProcess()
    {
        var processStepInfo = this.ToKernelProcessStepInfo();
        if (this.State is not KernelProcessState state)
        {
            throw new KernelException($"Unable to read state from process with name '{this.State.Name}' and Id '{this.State.Id}'.");
        }

        List<KernelProcessStepInfo> steps = [];
        foreach (var step in this.Steps)
        {
            if (step is DaprProcessInfo processStep)
            {
                steps.Add(processStep.ToKernelProcess());
            }
            else if (step is DaprMapInfo mapStep)
            {
                steps.Add(mapStep.ToKernelProcessMap());
            }
            else if (step is DaprProxyInfo proxyStep)
            {
                steps.Add(proxyStep.ToKernelProcessProxy());
            }
            else
            {
                steps.Add(step.ToKernelProcessStepInfo());
            }
        }

        return new KernelProcess(state, steps, this.Edges);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="DaprProcessInfo"/> class from an instance of <see cref="KernelProcess"/>.
    /// </summary>
    /// <param name="kernelProcess">The <see cref="KernelProcess"/> used to build the <see cref="DaprProcessInfo"/></param>
    /// <returns>An instance of <see cref="DaprProcessInfo"/></returns>
    public static DaprProcessInfo FromKernelProcess(KernelProcess kernelProcess)
    {
        Verify.NotNull(kernelProcess);

        DaprStepInfo daprStepInfo = DaprStepInfo.FromKernelStepInfo(kernelProcess);
        List<DaprStepInfo> daprSteps = [];

        foreach (var step in kernelProcess.Steps)
        {
            if (step is KernelProcess processStep)
            {
                daprSteps.Add(DaprProcessInfo.FromKernelProcess(processStep));
            }
            else if (step is KernelProcessMap mapStep)
            {
                daprSteps.Add(DaprMapInfo.FromKernelProcessMap(mapStep));
            }
            else if (step is KernelProcessProxy proxyStep)
            {
                daprSteps.Add(DaprProxyInfo.FromKernelProxyInfo(proxyStep));
            }
            else
            {
                daprSteps.Add(DaprStepInfo.FromKernelStepInfo(step));
            }
        }

        return new DaprProcessInfo
        {
            InnerStepDotnetType = daprStepInfo.InnerStepDotnetType,
            State = daprStepInfo.State,
            Edges = daprStepInfo.Edges,
            Steps = daprSteps,
        };
    }
}
