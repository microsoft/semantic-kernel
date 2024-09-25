// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Contains information about a Step in a Process including it's state and edges.
/// </summary>
public class KernelProcessStepInfo
{
    /// <summary>
    /// A mapping of output edges from the Step using the .
    /// </summary>
    private readonly Dictionary<string, List<KernelProcessEdge>> _outputEdges;

    /// <summary>
    /// The type of the inner step.
    /// </summary>
    internal Type InnerStepType { get; }

    /// <summary>
    /// A read-only collection of event Ids that this Step can emit.
    /// </summary>
    public IReadOnlyCollection<string> EventIds => this._outputEdges.Keys.ToArray();

    /// <summary>
    /// The state of the Step.
    /// </summary>
    public KernelProcessStepState State { get; }

    /// <summary>
    /// Retrieves the output edges for a given event Id. Returns an empty list if the event Id is not found.
    /// </summary>
    /// <param name="eventId">The Id of an event.</param>
    /// <returns>An <see cref="IReadOnlyCollection{T}"/> where T is <see cref="KernelProcessEdge"/></returns>
    protected IReadOnlyCollection<KernelProcessEdge> GetOutputEdges(string eventId)
    {
        if (this._outputEdges.TryGetValue(eventId, out List<KernelProcessEdge>? edges))
        {
            return edges.AsReadOnly();
        }

        return [];
    }

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
        this.State = state;
    }
}
