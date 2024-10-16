// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A serializable representation of a Process.
/// </summary>
public sealed record KernelProcessMap : KernelProcessStepInfo
{
    /// <summary>
    /// The collection of Steps in the Process.
    /// </summary>
    public KernelProcess TransformStep { get; }

    /// <summary>
    /// Creates a new instance of the <see cref="KernelProcess"/> class.
    /// </summary>
    /// <param name="state">The process state.</param>
    /// <param name="step">The steps of the process.</param>
    /// <param name="edges">The edges of the process.</param>
    public KernelProcessMap(KernelProcessStepState state, KernelProcess step, Dictionary<string, List<KernelProcessEdge>>? edges = null)
        : base(typeof(KernelProcessMap), state, edges ?? [])
    {
        Verify.NotNull(step);
        Verify.NotNullOrWhiteSpace(state.Name);

        this.TransformStep = step;
    }
}
