// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Planning.Sequential;

/// <summary>
/// Interface for planner that uses semantic function to create a sequential plan.
/// </summary>
public interface ISequentialPlanner
{
    /// <summary>
    /// Create a plan for a goal.
    /// </summary>
    /// <param name="goal">The goal to create a plan for.</param>
    /// <returns>The plan.</returns>
    /// <exception cref="PlanningException">Thrown when the plan cannot be created.</exception>
    Task<Plan> CreatePlanAsync(string goal);
}
