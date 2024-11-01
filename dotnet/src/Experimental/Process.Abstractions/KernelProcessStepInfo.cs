﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Process.Internal;
using Microsoft.SemanticKernel.Process.Models;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Contains information about a Step in a Process including it's state and edges.
/// </summary>
public record KernelProcessStepInfo
{
    private KernelProcessStepState _state;

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
    /// Captures Kernel Process Step State into <see cref="KernelProcessStateMetadata"/>
    /// </summary>
    /// <returns><see cref="KernelProcessStateMetadata"/></returns>
    public virtual KernelProcessStateMetadata ToProcessStateMetadata()
    {
        KernelProcessStateMetadata metadata = new()
        {
            Name = this.State.Name,
            Id = this.State.Id,
        };

        if (this.InnerStepType.TryGetSubtypeOfStatefulStep(out var genericStateType) && genericStateType != null)
        {
            var userStateType = genericStateType.GetGenericArguments()[0];
            var stateOriginalType = typeof(KernelProcessStepState<>).MakeGenericType(userStateType);

            var innerState = stateOriginalType.GetProperty(nameof(KernelProcessStepState<object>.State))?.GetValue(this._state);
            if (innerState != null)
            {
                metadata.State = innerState;
            }
        }

        return metadata;
    }

    /// <summary>
    /// A read-only dictionary of output edges from the Step.
    /// </summary>
    public IReadOnlyDictionary<string, IReadOnlyCollection<KernelProcessEdge>> Edges { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessStepInfo"/> class.
    /// </summary>
    public KernelProcessStepInfo(Type innerStepType, KernelProcessStepState state, Dictionary<string, List<KernelProcessEdge>> edges)
    {
        Verify.NotNull(innerStepType);
        Verify.NotNull(edges);
        Verify.NotNull(state);

        this.InnerStepType = innerStepType;
        this.Edges = edges.ToDictionary(kvp => kvp.Key, kvp => (IReadOnlyCollection<KernelProcessEdge>)kvp.Value.AsReadOnly());
        this._state = state;

        // Register the state as a know type for the DataContractSerialization used by Dapr.
        KernelProcessState.RegisterDerivedType(state.GetType());
    }
}
