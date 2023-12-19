// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI;

namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// A planner that uses semantic function to create a sequential plan.
/// </summary>
public sealed class SequentialPlanner
{
    private const string StopSequence = "<!-- END -->";
    private const string AvailableFunctionsKey = "available_functions";

    /// <summary>
    /// Initialize a new instance of the <see cref="SequentialPlanner"/> class.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="config">The planner configuration.</param>
    public SequentialPlanner(
        Kernel kernel,
        SequentialPlannerConfig? config = null)
    {
        Verify.NotNull(kernel);

        // Set up config with default value and excluded plugins
        this.Config = config ?? new();
        this.Config.ExcludedPlugins.Add(RestrictedPluginName);

        // Set up prompt template
        string promptTemplate = this.Config.GetPromptTemplate?.Invoke() ?? EmbeddedResource.Read("Sequential.skprompt.txt");

        this._functionFlowFunction = kernel.CreateFunctionFromPrompt(
            promptTemplate: promptTemplate,
            description: "Given a request or command or goal generate a step by step plan to " +
                         "fulfill the request using functions. This ability is also known as decision making and function flow",
            executionSettings: new PromptExecutionSettings()
            {
                ExtensionData = new()
                {
                    { "Temperature", 0.0 },
                    { "StopSequences", new[] { StopSequence } },
                    { "MaxTokens", this.Config.MaxTokens },
                }
            });

        this._kernel = kernel;
        this._logger = kernel.LoggerFactory.CreateLogger(this.GetType()) ?? NullLogger.Instance;
    }

    /// <summary>Creates a plan for the specified goal.</summary>
    /// <param name="goal">The goal for which a plan should be created.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The created plan.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="goal"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="goal"/> is empty or entirely composed of whitespace.</exception>
    /// <exception cref="KernelException">A plan could not be created.</exception>
    public Task<Plan> CreatePlanAsync(string goal, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(goal);

        return PlannerInstrumentation.CreatePlanAsync(
            createPlanAsync: static (SequentialPlanner planner, string goal, CancellationToken cancellationToken) => planner.CreatePlanCoreAsync(goal, cancellationToken),
            planToString: static (Plan plan) => plan.ToSafePlanString(),
            this, goal, this._logger, cancellationToken);
    }

    private async Task<Plan> CreatePlanCoreAsync(string goal, CancellationToken cancellationToken)
    {
        string relevantFunctionsManual = await this._kernel.Plugins.GetFunctionsManualAsync(this.Config, goal, null, cancellationToken).ConfigureAwait(false);

        ContextVariables vars = new(goal)
        {
            [AvailableFunctionsKey] = relevantFunctionsManual
        };

        FunctionResult planResult = await this._kernel.InvokeAsync(this._functionFlowFunction, vars, cancellationToken).ConfigureAwait(false);

        string? planResultString = planResult.GetValue<string>()?.Trim();

        if (string.IsNullOrWhiteSpace(planResultString))
        {
            throw new KernelException(
                "Unable to create plan. No response from Function Flow function. " +
                $"\nGoal:{goal}\nFunctions:\n{relevantFunctionsManual}");
        }

        var getFunctionCallback = this.Config.GetFunctionCallback ?? this._kernel.Plugins.GetFunctionCallback();

        Plan plan;
        try
        {
            plan = planResultString!.ToPlanFromXml(goal, getFunctionCallback, this.Config.AllowMissingFunctions);
        }
        catch (KernelException e)
        {
            throw new KernelException($"Unable to create plan for goal with available functions.\nGoal:{goal}\nFunctions:\n{relevantFunctionsManual}", e);
        }

        if (plan.Steps.Count == 0)
        {
            throw new KernelException($"Not possible to create plan for goal with available functions.\nGoal:{goal}\nFunctions:\n{relevantFunctionsManual}");
        }

        return plan;
    }

    private SequentialPlannerConfig Config { get; }

    private readonly Kernel _kernel;
    private readonly ILogger _logger;

    /// <summary>
    /// the function flow semantic function, which takes a goal and creates an xml plan that can be executed
    /// </summary>
    private readonly KernelFunction _functionFlowFunction;

    /// <summary>
    /// The name to use when creating semantic functions that are restricted from plan creation
    /// </summary>
    private const string RestrictedPluginName = "SequentialPlanner_Excluded";
}
