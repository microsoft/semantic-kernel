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
    public static ContextVariables UpdateWithPlanEntry(this ContextVariables vars, Plan plan)
    {
        vars.Update(plan.ToJson());
        vars.Set(Plan.IdKey, plan.Id);
        vars.Set(Plan.GoalKey, plan.Goal);
        vars.Set(Plan.PlanKey, plan.PlanString);
        vars.Set(Plan.IsCompleteKey, plan.IsComplete.ToString());
        vars.Set(Plan.IsSuccessfulKey, plan.IsSuccessful.ToString());
        vars.Set(Plan.ResultKey, plan.Result);

        return vars;
    }

    /// <summary>
    /// Simple extension method to clear the PlanCreation entries from a <see cref="ContextVariables"/> instance.
    /// </summary>
    /// <param name="vars">The <see cref="ContextVariables"/> to update</param>
    public static ContextVariables ClearPlan(this ContextVariables vars)
    {
        vars.Set(Plan.IdKey, null);
        vars.Set(Plan.GoalKey, null);
        vars.Set(Plan.PlanKey, null);
        vars.Set(Plan.IsCompleteKey, null);
        vars.Set(Plan.IsSuccessfulKey, null);
        vars.Set(Plan.ResultKey, null);
        return vars;
    }

    /// <summary>
    /// Simple extension method to parse a Plan instance from a <see cref="ContextVariables"/> instance.
    /// </summary>
    /// <param name="vars">The <see cref="ContextVariables"/> to read</param>
    /// <returns>An instance of Plan</returns>
    public static Plan ToPlan(this ContextVariables vars)
    {
        if (vars.Get(Plan.PlanKey, out string plan))
        {
            vars.Get(Plan.IdKey, out string id);
            vars.Get(Plan.GoalKey, out string goal);
            vars.Get(Plan.IsCompleteKey, out string isComplete);
            vars.Get(Plan.IsSuccessfulKey, out string isSuccessful);
            vars.Get(Plan.ResultKey, out string result);

            return new Plan()
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
            return Plan.FromJson(vars.ToString());
        }
        catch (ArgumentNullException)
        {
        }
        catch (JsonException)
        {
        }

        // If Plan.FromJson fails, return a Plan with the current <see cref="ContextVariables"/> as the plan.
        // Validation of that `plan` will be done separately.
        return new Plan() { PlanString = vars.ToString() };
    }
}
