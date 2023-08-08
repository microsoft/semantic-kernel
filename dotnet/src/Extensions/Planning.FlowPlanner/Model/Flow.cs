// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0130 // Namespace does not match folder structure
// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticKernel.Planning.Flow;
#pragma warning restore IDE0130 // Namespace does not match folder structure

using System.Collections.Generic;

/// <summary>
/// Flow data model
/// </summary>
/// <remarks>
/// Principles:
/// 1. The model should be decoupled from execution status
/// 2. The model is mutable to allow dynamic changes
/// 3. The model doesn't enforce any execution order as long as the dependencies are satisfied
/// </remarks>
#pragma warning disable CA1724 // The type name conflicts
public sealed class Flow : FlowStep

#pragma warning disable CA1724 // The type name conflicts
{
    private List<FlowStep> _steps;

    public Flow(string name, string goal) : base(goal, null)
    {
        this.Name = name;
        this._steps = new List<FlowStep>();
    }

    /// <summary>
    /// Only for deserialization.
    /// </summary>
    public Flow() : this(string.Empty, string.Empty)
    {
    }

    /// <summary>
    /// Steps of the flow
    /// </summary>
    public List<FlowStep> Steps
    {
        get => this._steps;
        set => this._steps = value;
    }

    /// <summary>
    /// Friendly name of the flow
    /// </summary>
    public string Name { get; set; }

    /// <summary>
    /// Adds a step to the flow
    /// </summary>
    /// <param name="step">the <see cref="FlowStep"/> instance</param>
    public void AddStep(FlowStep step)
    {
        this._steps.Add(step);
    }

    /// <summary>
    /// Adds steps to the flow
    /// </summary>
    /// <param name="steps">the array of <see cref="FlowStep"/> instance to be add</param>
    public void AddSteps(params FlowStep[] steps)
    {
        this._steps.AddRange(steps);
    }
}
