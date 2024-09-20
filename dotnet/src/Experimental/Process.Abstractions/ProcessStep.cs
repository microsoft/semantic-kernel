// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Process;

/// <summary>
/// A serializable representation of a Step in a Process.
/// </summary>
public record ProcessStep
{
    /// <summary>
    /// The unique identifier of the Step.
    /// </summary>
    public string? Id { get; init; }

    /// <summary>
    /// The name of the Step. This is intended to be a human-readable name and does not need to be unique.
    /// </summary>
    public string Name { get; init; }

    /// <summary>
    /// The type of the Step.
    /// </summary>
    public string StepType { get; init; }

    /// <summary>
    /// The state of the Step.
    /// </summary>
    public object State { get; init; }

    /// <summary>
    /// The collection of output Edges for the Step.
    /// </summary>
    public Dictionary<string, List<ProcessEdge>> OutputEdges { get; init; } = [];

    /// <summary>
    /// Creates a new instance of the <see cref="ProcessStep"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the Step.</param>
    /// <param name="name">The name of the Step. This is intended to be a human-readable name and does not need to be unique.</param>
    /// <param name="stepType">The type of the Step.</param>
    /// <param name="state">The state of the Step.</param>
    public ProcessStep(string? id, string name, string stepType, object state)
    {
        this.Id = id;
        this.Name = name;
        this.StepType = stepType;
        this.State = state;
    }
}
