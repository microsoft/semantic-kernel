// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planners.Sequential;
using Microsoft.SemanticKernel.Planning;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of Plan
namespace Microsoft.SemanticKernel.Planners;
#pragma warning restore IDE0130

/// <summary>
/// A planner that uses semantic function to create a sequential plan.
/// </summary>
public sealed class SequentialPlanner : ISequentialPlanner
{
    private const string StopSequence = "<!-- END -->";
    private const string AvailableFunctionsKey = "available_functions";

    /// <summary>
    /// Initialize a new instance of the <see cref="SequentialPlanner"/> class.
    /// </summary>
    /// <param name="kernel">The semantic kernel instance.</param>
    /// <param name="config">The planner configuration.</param>
    public SequentialPlanner(
        IKernel kernel,
        SequentialPlannerConfig? config = null)
    {
        Verify.NotNull(kernel);

        // Set up config with default value and excluded plugins
        this.Config = config ?? new();
        this.Config.ExcludedPlugins.Add(RestrictedPluginName);

        // Set up prompt template
        string promptTemplate = this.Config.GetPromptTemplate?.Invoke() ?? EmbeddedResource.Read("skprompt.txt");

        this._functionFlowFunction = kernel.CreateSemanticFunction(
            promptTemplate: promptTemplate,
            pluginName: RestrictedPluginName,
            description: "Given a request or command or goal generate a step by step plan to " +
                         "fulfill the request using functions. This ability is also known as decision making and function flow",
            requestSettings: new AIRequestSettings()
            {
                ExtensionData = new Dictionary<string, object>()
                {
                    { "Temperature", 0.0 },
                    { "StopSequences", new[] { StopSequence } },
                    { "MaxTokens", this.Config.MaxTokens },
                }
            });

        this._kernel = kernel;
    }

    /// <inheritdoc />
    public async Task<Plan> CreatePlanAsync(string goal, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrEmpty(goal))
        {
            throw new SKException("The goal specified is empty");
        }

        string relevantFunctionsManual = await this._kernel.Functions.GetFunctionsManualAsync(this.Config, goal, null, cancellationToken).ConfigureAwait(false);

        ContextVariables vars = new(goal)
        {
            [AvailableFunctionsKey] = relevantFunctionsManual
        };

        KernelResult planResult = await this._kernel.RunAsync(this._functionFlowFunction, vars, cancellationToken).ConfigureAwait(false);

        string? planResultString = planResult.GetValue<string>()?.Trim();

        if (string.IsNullOrWhiteSpace(planResultString))
        {
            throw new SKException(
                "Unable to create plan. No response from Function Flow function. " +
                $"\nGoal:{goal}\nFunctions:\n{relevantFunctionsManual}");
        }

        var getFunctionCallback = this.Config.GetFunctionCallback ?? this._kernel.Functions.GetFunctionCallback();

        Plan plan;
        try
        {
            plan = planResultString!.ToPlanFromXml(goal, getFunctionCallback, this.Config.AllowMissingFunctions);
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

    private readonly IKernel _kernel;

    /// <summary>
    /// the function flow semantic function, which takes a goal and creates an xml plan that can be executed
    /// </summary>
    private readonly ISKFunction _functionFlowFunction;

    /// <summary>
    /// The name to use when creating semantic functions that are restricted from plan creation
    /// </summary>
    private const string RestrictedPluginName = "SequentialPlanner_Excluded";
}
