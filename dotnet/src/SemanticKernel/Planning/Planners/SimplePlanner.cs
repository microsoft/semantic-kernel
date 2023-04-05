// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Planning.Planners;

/// <summary>
/// A simple Planner that creates a plan with the given goal as description.
/// </summary>
public class SimplePlanner : IPlanner
{
    /// <summary>
    /// Initializes a new instance of the <see cref="SimplePlanner"/> class.
    /// </summary>
    public SimplePlanner()
    {
    }

    /// <inheritdoc/>
    public Task<Plan> CreatePlanAsync(string goal)
    {
        var plan = new Plan(goal);
        return Task.FromResult<Plan>(plan);
    }
}
