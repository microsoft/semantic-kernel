﻿// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A serializable representation of a Process.
/// </summary>
public sealed record KernelProcess : KernelProcessStepInfo
{
    /// <summary>
    /// The collection of Steps in the Process.
    /// </summary>
    public IList<KernelProcessStepInfo> Steps { get; }

    /// <summary>
    /// Creates a new instance of the <see cref="KernelProcess"/> class.
    /// </summary>
    /// <param name="name">The human friendly name of the Process.</param>
    /// <param name="steps">The steps of the process.</param>
    /// <param name="edges">The edges of the process.</param>
    public KernelProcess(string name, IList<KernelProcessStepInfo> steps, Dictionary<string, List<KernelProcessEdge>>? edges = null)
        : base(typeof(KernelProcess), new KernelProcessState() { Name = name }, edges ?? [])
    {
        Verify.NotNull(steps);
        Verify.NotNullOrWhiteSpace(name);

        this.Steps = [];
        this.Steps.AddRange(steps);
    }
}
