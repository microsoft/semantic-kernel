// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Options;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.SkillDefinition;
using SemanticKernel.Service.Config;

namespace SemanticKernel.Service.Skills;

/// <summary>
/// A lightweight wrapper around a planner to allow for curating which skills are available to it.
/// </summary>
public class CopilotChatPlanner
{
    /// <summary>
    /// The planner's kernel.
    /// </summary>
    public IKernel Kernel { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="CopilotChatPlanner"/> class.
    /// </summary>
    /// <param name="plannerKernel">The planner's kernel.</param>
    public CopilotChatPlanner(IKernel plannerKernel)
    {
        this.Kernel = plannerKernel;
    }

    /// <summary>
    /// Create a plan for a goal.
    /// </summary>
    /// <param name="goal">The goal to create a plan for.</param>
    /// <returns>The plan.</returns>
    public Task<Plan> CreatePlanAsync(string goal)
    {
        FunctionsView plannerFunctionsView = this.Kernel.Skills.GetFunctionsView(true, true);
        if (plannerFunctionsView.NativeFunctions.IsEmpty && plannerFunctionsView.SemanticFunctions.IsEmpty)
        {
            // No functions are available - return an empty plan.
            return Task.FromResult(new Plan(goal));
        }

        return new ActionPlanner(this.Kernel).CreatePlanAsync(goal);
    }
}
