// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Planning.Planners;

/// <summary>
/// A planner utility class that creates a plan for a given goal
/// with the help of a specific planner implementation(mode).
/// </summary>
public class Planner : IPlanner
{
    /// <summary>
    /// The planner mode.used when creating plans
    /// </summary>
    public enum Mode
    {
        Simple,
        // FunctionFlow,
        // GoalRelevant,
        // Stepwise,
        // Recursive,
        // Progressive,
        // GoalOriented,
    }

    /// <summary>
    /// Creates a planner with the given mode.
    /// </summary>
    /// <param name="mode">The mode to use when creating plans.</param>
    public Planner(Mode mode = Mode.Simple)
    {
        this._planner = this.GetPlannerForMode(mode);
    }

    /// <inheritdoc/>
    public Task<Plan> CreatePlanAsync(string goal)
    {
        return this._planner.CreatePlanAsync(goal);
    }

    private SimplePlanner GetPlannerForMode(Mode mode)
    {
        return mode switch
        {
            Mode.Simple => new SimplePlanner(),
            _ => throw new NotImplementedException(),
        };
    }

    private readonly IPlanner _planner;
}
