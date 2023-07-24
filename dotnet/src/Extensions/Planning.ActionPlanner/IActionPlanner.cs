// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Planning.Action;

/// <summary>
/// Interface for planner that uses set of semantic functions to select one function out of many and create a plan.
/// </summary>
public interface IActionPlanner
{
    /// <summary>
    /// Create a plan for a goal.
    /// </summary>
    /// <param name="goal">The goal to create a plan for.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The plan.</returns>
    /// <exception cref="PlanningException">Thrown when the plan cannot be created.</exception>
    Task<Plan> CreatePlanAsync(string goal, CancellationToken cancellationToken = default);
}
