// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using Microsoft.SemanticKernel.Planning;

// ReSharper disable once CheckNamespace // Extension methods
namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Class that holds extension methods for ContextVariables.
/// </summary>
public static class ContextVariablesExtensions
{
    /// <summary>
    /// Simple extension method to turn a string into a <see cref="ContextVariables"/> instance.
    /// </summary>
    /// <param name="text">The text to transform</param>
    /// <returns>An instance of <see cref="ContextVariables"/></returns>
    public static ContextVariables ToContextVariables(this string text)
    {
        return new ContextVariables(text);
    }

    /// <summary>
    /// Simple extension method to update a <see cref="ContextVariables"/> instance with a Plan instance.
    /// </summary>
    /// <param name="vars">The variables to update</param>
    /// <param name="plan">The Plan to update the <see cref="ContextVariables"/> with</param>
    /// <returns>The updated <see cref="ContextVariables"/></returns>
    public static ContextVariables UpdateWithPlanEntry(this ContextVariables vars, SkillPlan plan)
    {
        vars.Update(plan.ToJson());
        vars.Set(SkillPlan.IdKey, plan.Id);
        vars.Set(SkillPlan.GoalKey, plan.Goal);
        vars.Set(SkillPlan.PlanKey, plan.PlanString);
        vars.Set(SkillPlan.IsCompleteKey, plan.IsComplete.ToString());
        vars.Set(SkillPlan.IsSuccessfulKey, plan.IsSuccessful.ToString());
        vars.Set(SkillPlan.ResultKey, plan.Result);

        return vars;
    }

    /// <summary>
    /// Simple extension method to clear the PlanCreation entries from a <see cref="ContextVariables"/> instance.
    /// </summary>
    /// <param name="vars">The <see cref="ContextVariables"/> to update</param>
    public static ContextVariables ClearPlan(this ContextVariables vars)
    {
        vars.Set(SkillPlan.IdKey, null);
        vars.Set(SkillPlan.GoalKey, null);
        vars.Set(SkillPlan.PlanKey, null);
        vars.Set(SkillPlan.IsCompleteKey, null);
        vars.Set(SkillPlan.IsSuccessfulKey, null);
        vars.Set(SkillPlan.ResultKey, null);
        return vars;
    }

    /// <summary>
    /// Simple extension method to parse a Plan instance from a <see cref="ContextVariables"/> instance.
    /// </summary>
    /// <param name="vars">The <see cref="ContextVariables"/> to read</param>
    /// <returns>An instance of Plan</returns>
    public static SkillPlan ToPlan(this ContextVariables vars)
    {
        if (vars.Get(SkillPlan.PlanKey, out string plan))
        {
            vars.Get(SkillPlan.IdKey, out string id);
            vars.Get(SkillPlan.GoalKey, out string goal);
            vars.Get(SkillPlan.IsCompleteKey, out string isComplete);
            vars.Get(SkillPlan.IsSuccessfulKey, out string isSuccessful);
            vars.Get(SkillPlan.ResultKey, out string result);

            return new SkillPlan()
            {
                Id = id,
                Goal = goal,
                PlanString = plan,
                IsComplete = !string.IsNullOrEmpty(isComplete) && bool.Parse(isComplete),
                IsSuccessful = !string.IsNullOrEmpty(isSuccessful) && bool.Parse(isSuccessful),
                Result = result
            };
        }

        try
        {
            return SkillPlan.FromJson(vars.ToString());
        }
        catch (ArgumentNullException)
        {
        }
        catch (JsonException)
        {
        }

        // If SkillPlan.FromJson fails, return a Plan with the current <see cref="ContextVariables"/> as the plan.
        // Validation of that `plan` will be done separately.
        return new SkillPlan() { PlanString = vars.ToString() };
    }
}
