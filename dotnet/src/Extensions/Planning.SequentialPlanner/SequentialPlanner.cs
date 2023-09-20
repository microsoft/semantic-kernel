// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
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
public sealed class SequentialPlanner : ISequentialPlanner
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

    /// <inheritdoc />
    public async Task<Plan> CreatePlanAsync(string goal, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrEmpty(goal))
        {
            throw new SKException("The goal specified is empty");
        }

        string relevantFunctionsManual = await this._context.GetFunctionsManualAsync(goal, this.Config, cancellationToken).ConfigureAwait(false);
        this._context.Variables.Set("available_functions", relevantFunctionsManual);

        this._context.Variables.Update(goal);

        FunctionResult planResult = await this._functionFlowFunction.InvokeAsync(this._context, cancellationToken: cancellationToken).ConfigureAwait(false);

        string? planResultString = planResult.GetValue<string>()?.Trim();

        if (string.IsNullOrWhiteSpace(planResultString))
        {
            throw new SKException(
                "Unable to create plan. No response from Function Flow function. " +
                $"\nGoal:{goal}\nFunctions:\n{relevantFunctionsManual}");
        }

        var getSkillFunction = this.Config.GetSkillFunction ?? SequentialPlanParser.GetSkillFunction(this._context);

        Plan plan;
        try
        {
            plan = planResultString!.ToPlanFromXml(goal, getSkillFunction, this.Config.AllowMissingFunctions);
        }
        catch (SKException e)
        {
            throw new SKException($"Unable to create plan for goal with available functions.\nGoal:{goal}\nFunctions:\n{relevantFunctionsManual}", e);
        }

        if (plan.Steps.Count == 0)
        {
            throw new SKException($"Not possible to create plan for goal with available functions.\nGoal:{goal}\nFunctions:\n{relevantFunctionsManual}");
        }

        return plan;
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
