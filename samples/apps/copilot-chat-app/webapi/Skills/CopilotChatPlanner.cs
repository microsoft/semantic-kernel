// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Options;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planning;
using SemanticKernel.Service.Config;

namespace SemanticKernel.Service.Skills;

/// <summary>
/// A lightweight wrapper around the SequentialPlanner to allow for curating exactly which skills are available to it.
/// </summary>
public class CopilotChatPlanner
{
    /// <summary>
    /// The planner's kernel.
    /// </summary>
    public IKernel Kernel { get; }

    /// <summary>
    /// The planner's options.
    /// </summary>
    private readonly PlannerOptions _options;

    /// <summary>
    /// Initializes a new instance of the <see cref="CopilotChatPlanner"/> class.
    /// </summary>
    /// <param name="plannerKernel">The planner's kernel.</param>
    /// <param name="options">The planner's options.</param>
    public CopilotChatPlanner(IKernel plannerKernel, IOptions<PlannerOptions> options)
    {
        this.Kernel = plannerKernel;
        this._options = options.Value;
    }

    /// <summary>
    /// Create a plan for a goal.
    /// </summary>
    /// <param name="goal">The goal to create a plan for.</param>
    /// <returns>The plan.</returns>
    public Task<Plan> CreatePlanAsync(string goal)
        => new SequentialPlanner(this.Kernel, this._options.ToSequentialPlannerConfig())
            .CreatePlanAsync(goal);
}
