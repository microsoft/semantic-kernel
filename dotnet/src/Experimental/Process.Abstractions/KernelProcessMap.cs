// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A serializable representation of a Process.
/// </summary>
public sealed record KernelProcessMap : KernelProcessStepInfo
{
    /// <summary>
    /// Event Id used internally to initiate the map operation.
    /// </summary>
    public const string MapEventId = "Map";

    /// <summary>
    /// The discrete map operation.
    /// </summary>
    public KernelProcess MapStep { get; }

    /// <summary>
    /// The event that signals the completion of the map operation.
    /// </summary>
    public string CompleteEventId { get; }

    /// <summary>
    /// The name of the input parameter for the map operation.
    /// </summary>
    public string InputParameterName { get; }

    /// <summary>
    /// Creates a new instance of the <see cref="KernelProcess"/> class.
    /// </summary>
    /// <param name="state">The process state.</param>
    /// <param name="step">The discrete map operation.</param>
    /// <param name="completeEventId">The event that signals the completion of the map operation.</param>
    /// <param name="inputParameter">name of the input parameter for the map operation.</param>
    /// <param name="edges">// %%% COMMENT</param>
    public KernelProcessMap(KernelProcessMapState state, KernelProcess step, string completeEventId, string inputParameter, Dictionary<string, List<KernelProcessEdge>> edges)
        : base(typeof(KernelProcessMap), state, edges)
    {
        Verify.NotNull(step);
        Verify.NotNullOrWhiteSpace(state.Name);

        //Console.WriteLine($"\nPROCESS MAP: {state.Id}");

        this.MapStep = step;
        this.CompleteEventId = completeEventId;
        this.InputParameterName = inputParameter;
    }
}
