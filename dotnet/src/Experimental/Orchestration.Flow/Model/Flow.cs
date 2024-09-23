// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;

<<<<<<< HEAD
namespace Microsoft.SemanticKernel.Experimental.Orchestration;
=======
#pragma warning disable IDE0130
namespace Microsoft.SemanticKernel.Experimental.Orchestration;
#pragma warning restore IDE0130
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624

/// <summary>
/// Flow data model
/// </summary>
/// <remarks>
/// Principles:
/// 1. The model should be decoupled from execution status
/// 2. The model is mutable to allow dynamic changes
/// 3. The model doesn't enforce any execution order as long as the dependencies are satisfied
/// </remarks>
public sealed class Flow : FlowStep
{
<<<<<<< HEAD
=======
    private List<FlowStep> _steps;

>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
    /// <summary>
    /// Initializes a new instance of the <see cref="Flow"/> class.
    /// </summary>
    /// <param name="name">The name of flow</param>
    /// <param name="goal">The goal of flow</param>
    public Flow(string name, string goal) : base(goal, null)
    {
        this.Name = name;
<<<<<<< HEAD
        this.Steps = [];
=======
        this._steps = new List<FlowStep>();
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
    }

    /// <summary>
    /// Steps of the flow
    /// </summary>
<<<<<<< HEAD
    public List<FlowStep> Steps { get; set; }
=======
    public List<FlowStep> Steps
    {
        get => this._steps;
        set => this._steps = value;
    }
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624

    /// <summary>
    /// Friendly name and identifier of the flow
    /// </summary>
    public string Name { get; set; }

    /// <summary>
    /// Adds a step to the flow
    /// </summary>
    /// <param name="step">the <see cref="FlowStep"/> instance</param>
    public void AddStep(FlowStep step)
    {
<<<<<<< HEAD
        this.Steps.Add(step);
=======
        this._steps.Add(step);
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
    }

    /// <summary>
    /// Adds steps to the flow
    /// </summary>
    /// <param name="steps">the array of <see cref="FlowStep"/> instance to be add</param>
    public void AddSteps(params FlowStep[] steps)
    {
<<<<<<< HEAD
        this.Steps.AddRange(steps);
=======
        this._steps.AddRange(steps);
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
    }

    /// <inheritdoc/>
    public override IEnumerable<string> Requires
    {
        get
        {
            var requires = new List<string>();
<<<<<<< HEAD
            foreach (var step in this.Steps)
=======
            foreach (var step in this._steps)
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
            {
                requires.AddRange(step.Requires);
            }

<<<<<<< HEAD
            foreach (var step in this.Steps)
=======
            foreach (var step in this._steps)
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
            {
                requires.RemoveAll(r => step.Provides.Contains(r));
            }

            return requires;
        }
    }
}
