// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.SkillDefinition;
using SemanticKernel.Service.CopilotChat.Models;
using SemanticKernel.Service.CopilotChat.Options;

namespace SemanticKernel.Service.CopilotChat.Skills.ChatSkills;

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
    /// Options for the planner.
    /// </summary>
    private readonly PlannerOptions? _plannerOptions;

    /// <summary>
    /// Gets the pptions for the planner.
    /// </summary>
    public PlannerOptions? PlannerOptions => this._plannerOptions;

    /// <summary>
    /// Initializes a new instance of the <see cref="CopilotChatPlanner"/> class.
    /// </summary>
    /// <param name="plannerKernel">The planner's kernel.</param>
    public CopilotChatPlanner(IKernel plannerKernel, PlannerOptions? plannerOptions)
    {
        this.Kernel = plannerKernel;
        this._plannerOptions = plannerOptions;
    }

    /// <summary>
    /// Create a plan for a goal.
    /// </summary>
    /// <param name="goal">The goal to create a plan for.</param>
    /// <param name="availableFunctionsOnly">Optional override to allow developers to keep functions regardless of whether they're available in the planner's context or not.</param>
    /// <returns>The plan.</returns>
    public async Task<Plan> CreatePlanAsync(string goal, bool availableFunctionsOnly = true)
    {
        FunctionsView plannerFunctionsView = this.Kernel.Skills.GetFunctionsView(true, true);
        if (plannerFunctionsView.NativeFunctions.IsEmpty && plannerFunctionsView.SemanticFunctions.IsEmpty)
        {
            // No functions are available - return an empty plan.
            return new Plan(goal);
        }

        Plan plan = this._plannerOptions?.Type == PlanType.Sequential
                ? await new SequentialPlanner(this.Kernel).CreatePlanAsync(goal)
                : await new ActionPlanner(this.Kernel).CreatePlanAsync(goal);

        return availableFunctionsOnly ? this.SanitizePlan(plan, plannerFunctionsView) : plan;
    }

    #region Private

    /// <summary>
    /// Scrubs plan of functions not available in Planner's kernel.
    /// </summary>
    private Plan SanitizePlan(Plan plan, FunctionsView availableFunctions)
    {
        List<Plan> sanitizedSteps = new();
        foreach (var step in plan.Steps)
        {
            if (this.Kernel.Skills.TryGetFunction(step.SkillName, step.Name, out var function))
            {
                sanitizedSteps.Add(step);
            }
        }

        Plan sanitizedPlan = new Plan(plan.Description, sanitizedSteps.ToArray<Plan>());

        // Merge any state back into new plan object
        sanitizedPlan.State.Update(plan.State);

        return sanitizedPlan;
    }

    #endregion
}
