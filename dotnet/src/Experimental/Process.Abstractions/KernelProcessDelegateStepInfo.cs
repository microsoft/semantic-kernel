// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Process;

/// <summary>
/// Delegate step in a Kernel Process.
/// </summary>
public record KernelProcessDelegateStepInfo : KernelProcessStepInfo
{
    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessDelegateStepInfo"/> class.
    /// </summary>
    public KernelProcessDelegateStepInfo(
        KernelProcessStepState state,
        StepFunction stepFunction,
        Dictionary<string, List<KernelProcessEdge>> edges) :
        base(typeof(KernelDelegateProcessStep), state, edges, incomingEdgeGroups: null)
    {
        this.StepFunction = stepFunction;
    }

    /// <summary>
    /// Step function
    /// </summary>
    public StepFunction StepFunction { get; }
}
