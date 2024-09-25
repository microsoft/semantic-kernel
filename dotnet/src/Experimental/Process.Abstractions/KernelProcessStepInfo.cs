﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Contains information about a Step in a Process including it's state and edges.
/// </summary>
public record KernelProcessStepInfo
{
    private KernelProcessStepState _state;

    /// <summary>
    /// A mapping of output edges from the Step using the .
    /// </summary>
    private readonly Dictionary<string, List<KernelProcessEdge>> _outputEdges;

    /// <summary>
    /// The type of the inner step.
    /// </summary>
    public Type InnerStepType { get; }

    /// <summary>
    /// The state of the Step.
    /// </summary>
    public KernelProcessStepState State
    {
        get => this._state;
        init
        {
            Verify.NotNull(value);
            this._state = value;
        }
    }

    /// <summary>
    /// A read-only dictionary of output edges from the Step.
    /// </summary>
    public IReadOnlyDictionary<string, IReadOnlyCollection<KernelProcessEdge>> Edges =>
        this._outputEdges.ToDictionary(kvp => kvp.Key, kvp => (IReadOnlyCollection<KernelProcessEdge>)kvp.Value.AsReadOnly());

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessStepInfo"/> class.
    /// </summary>
    public KernelProcessStepInfo(Type innerStepType, KernelProcessStepState state, Dictionary<string, List<KernelProcessEdge>> edges)
    {
        Verify.NotNull(innerStepType);
        Verify.NotNull(edges);
        Verify.NotNull(state);

        this.InnerStepType = innerStepType;
        this._outputEdges = edges;
        this._state = state;
    }
}
