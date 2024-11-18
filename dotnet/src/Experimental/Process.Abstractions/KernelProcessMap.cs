﻿// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A serializable representation of a ProcessMap.
/// </summary>
public sealed record KernelProcessMap : KernelProcessStepInfo
{
    /// <summary>
    /// The map operation.
    /// </summary>
    public KernelProcessStepInfo Operation { get; }

    /// <summary>
    /// Creates a new instance of the <see cref="KernelProcess"/> class.
    /// </summary>
    /// <param name="state">The process state.</param>
    /// <param name="operation">The map operation.</param>
    /// <param name="edges">The edges for the map.</param>
    public KernelProcessMap(KernelProcessMapState state, KernelProcessStepInfo operation, Dictionary<string, List<KernelProcessEdge>> edges)
        : base(typeof(KernelProcessMap), state, edges)
    {
        Verify.NotNull(operation, nameof(operation));
        Verify.NotNullOrWhiteSpace(state.Name, $"{nameof(state)}.{nameof(KernelProcessMapState.Name)}");
        Verify.NotNullOrWhiteSpace(state.Id, $"{nameof(state)}.{nameof(KernelProcessMapState.Id)}");

        this.Operation = operation;
    }
}
