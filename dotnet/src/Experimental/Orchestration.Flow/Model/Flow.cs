// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;

<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
namespace Microsoft.SemanticKernel.Experimental.Orchestration;
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
namespace Microsoft.SemanticKernel.Experimental.Orchestration;
=======
#pragma warning disable IDE0130
namespace Microsoft.SemanticKernel.Experimental.Orchestration;
#pragma warning restore IDE0130
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

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
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< HEAD
=======
    private List<FlowStep> _steps;

>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    /// <summary>
    /// Initializes a new instance of the <see cref="Flow"/> class.
    /// </summary>
    /// <param name="name">The name of flow</param>
    /// <param name="goal">The goal of flow</param>
    public Flow(string name, string goal) : base(goal, null)
    {
        this.Name = name;
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        this.Steps = [];
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        this.Steps = [];
=======
<<<<<<< HEAD
        this.Steps = [];
=======
        this._steps = new List<FlowStep>();
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    }

    /// <summary>
    /// Steps of the flow
    /// </summary>
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    public List<FlowStep> Steps { get; set; }
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
    public List<FlowStep> Steps { get; set; }
=======
<<<<<<< HEAD
    public List<FlowStep> Steps { get; set; }
=======
    public List<FlowStep> Steps
    {
        get => this._steps;
        set => this._steps = value;
    }
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

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
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        this.Steps.Add(step);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        this.Steps.Add(step);
=======
<<<<<<< HEAD
        this.Steps.Add(step);
=======
        this._steps.Add(step);
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    }

    /// <summary>
    /// Adds steps to the flow
    /// </summary>
    /// <param name="steps">the array of <see cref="FlowStep"/> instance to be add</param>
    public void AddSteps(params FlowStep[] steps)
    {
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        this.Steps.AddRange(steps);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        this.Steps.AddRange(steps);
=======
<<<<<<< HEAD
        this.Steps.AddRange(steps);
=======
        this._steps.AddRange(steps);
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    }

    /// <inheritdoc/>
    public override IEnumerable<string> Requires
    {
        get
        {
            var requires = new List<string>();
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            foreach (var step in this.Steps)
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
            foreach (var step in this.Steps)
=======
<<<<<<< HEAD
            foreach (var step in this.Steps)
=======
            foreach (var step in this._steps)
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
            {
                requires.AddRange(step.Requires);
            }

<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            foreach (var step in this.Steps)
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
            foreach (var step in this.Steps)
=======
<<<<<<< HEAD
            foreach (var step in this.Steps)
=======
            foreach (var step in this._steps)
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
            {
                requires.RemoveAll(r => step.Provides.Contains(r));
            }

            return requires;
        }
    }
}
