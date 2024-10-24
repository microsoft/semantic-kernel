// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A serializable representation of a ProcessMap.
/// </summary>
public sealed record KernelProcessMap : KernelProcessStepInfo
{
    /// <summary>
    /// Event Id used internally to initiate the map operation.
    /// </summary>
    public const string MapEventId = "Map";

    /// <summary>
    /// The map operation.
    /// </summary>
    public KernelProcess Operation { get; }

    /// <summary>
    /// The name of the input parameter for the map operation.
    /// </summary>
    public string InputParameterName { get; }

    /// <summary>
    /// Creates a new instance of the <see cref="KernelProcess"/> class.
    /// </summary>
    /// <param name="state">The process state.</param>
    /// <param name="operation">The map operation.</param>
    /// <param name="inputParameter">name of the input parameter for the map operation.</param>
    /// <param name="edges">The edges for the map.</param> // %%% NEEDED ???
    public KernelProcessMap(KernelProcessMapState state, KernelProcess operation, string inputParameter, Dictionary<string, List<KernelProcessEdge>> edges)
        : base(typeof(KernelProcessMap), state, edges)
    {
        Verify.NotNull(operation);
        Verify.NotNullOrWhiteSpace(state.Name);

        this.Operation = operation;
        this.InputParameterName = inputParameter;
    }
}
