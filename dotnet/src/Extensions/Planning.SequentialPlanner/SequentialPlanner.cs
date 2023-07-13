// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning.Sequential;
using Microsoft.SemanticKernel.SkillDefinition;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of Plan
namespace Microsoft.SemanticKernel.Planning;
#pragma warning restore IDE0130

/// <summary>
/// A planner that uses semantic function to create a sequential plan.
/// </summary>
public sealed class SequentialPlanner
{
    private const string StopSequence = "<!-- END -->";

    /// <summary>
    /// Initialize a new instance of the <see cref="SequentialPlanner"/> class.
    /// </summary>
    /// <param name="kernel">The semantic kernel instance.</param>
    /// <param name="config">The planner configuration.</param>
    /// <param name="prompt">Optional prompt override</param>
    public SequentialPlanner(
        IKernel kernel,
        SequentialPlannerConfig? config = null,
        string? prompt = null)
    {
        Verify.NotNull(kernel);
        this.Config = config ?? new();

        this.Config.ExcludedSkills.Add(RestrictedSkillName);

        string promptTemplate = prompt ?? EmbeddedResource.Read("skprompt.txt");

        this._functionFlowFunction = kernel.CreateSemanticFunction(
            promptTemplate: promptTemplate,
            skillName: RestrictedSkillName,
            description: "Given a request or command or goal generate a step by step plan to " +
                         "fulfill the request using functions. This ability is also known as decision making and function flow",
            maxTokens: this.Config.MaxTokens ?? 1024,
            temperature: 0.0,
            stopSequences: new[] { StopSequence });

        this._context = kernel.CreateNewContext();
    }

    /// <summary>
    /// Create a plan for a goal.
    /// </summary>
    /// <param name="goal">The goal to create a plan for.</param>
    /// <returns>The plan.</returns>
    /// <exception cref="PlanningException">Thrown when the plan cannot be created.</exception>
    public async Task<Plan> CreatePlanAsync(string goal)
    {
        if (string.IsNullOrEmpty(goal))
        {
            throw new PlanningException(PlanningException.ErrorCodes.InvalidGoal, "The goal specified is empty");
        }

        string relevantFunctionsManual = await this._context.GetFunctionsManualAsync(goal, this.Config).ConfigureAwait(false);
        this._context.Variables.Set("available_functions", relevantFunctionsManual);

        this._context.Variables.Update(goal);

        var planResult = await this._functionFlowFunction.InvokeAsync(this._context).ConfigureAwait(false);

        if (planResult.ErrorOccurred)
        {
            throw new PlanningException(PlanningException.ErrorCodes.CreatePlanError, $"Error creating plan for goal: {planResult.LastErrorDescription}", planResult.LastException);
        }

        string planResultString = planResult.Result.Trim();

        try
        {
            var getSkillFunction = this.Config.GetSkillFunction ?? SequentialPlanParser.GetSkillFunction(this._context);
            var plan = planResultString.ToPlanFromXml(goal, getSkillFunction, this.Config.AllowMissingFunctions);

            if (plan.Steps.Count == 0)
            {
                throw new PlanningException(PlanningException.ErrorCodes.CreatePlanError, $"Not possible to create plan for goal with available functions.\nGoal:{goal}\nFunctions:\n{relevantFunctionsManual}");
            }

            return plan;
        }
        catch (PlanningException planException) when (planException.ErrorCode == PlanningException.ErrorCodes.CreatePlanError)
        {
            throw;
        }
        catch (PlanningException planException) when (planException.ErrorCode == PlanningException.ErrorCodes.InvalidPlan ||
                                                      planException.ErrorCode == PlanningException.ErrorCodes.InvalidGoal)
        {
            throw new PlanningException(PlanningException.ErrorCodes.CreatePlanError, "Unable to create plan", planException);
        }
        catch (Exception e)
        {
            throw new PlanningException(PlanningException.ErrorCodes.UnknownError, "Unknown error creating plan", e);
        }
    }

    private SequentialPlannerConfig Config { get; }

    private readonly SKContext _context;

    /// <summary>
    /// the function flow semantic function, which takes a goal and creates an xml plan that can be executed
    /// </summary>
    private readonly ISKFunction _functionFlowFunction;

    /// <summary>
    /// The name to use when creating semantic functions that are restricted from plan creation
    /// </summary>
    private const string RestrictedSkillName = "SequentialPlanner_Excluded";
}
