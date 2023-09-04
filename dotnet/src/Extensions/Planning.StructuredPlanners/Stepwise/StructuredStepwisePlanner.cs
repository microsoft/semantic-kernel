// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Planning.Structured.Stepwise;

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Globalization;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Connectors.AI.OpenAI.FunctionCalling;
using Connectors.AI.OpenAI.FunctionCalling.Extensions;
using Diagnostics;
using Microsoft.Extensions.Logging;
using Orchestration;
using SemanticFunctions;
using SkillDefinition;


/// <summary>
///  Stepwise planner that uses the OpenAI chat completion function calling API to achieve a goal in a step by step manner. 
/// </summary>
public class StructuredStepwisePlanner : IStructuredPlanner
{

    /// <summary>
    ///  Create a new instance of the StepwisePlanner
    /// </summary>
    /// <param name="kernel"></param>
    /// <param name="config"></param>
    /// <param name="prompt"></param>
    /// <param name="promptUserConfig"></param>
    public StructuredStepwisePlanner(
        IKernel kernel,
        StructuredPlannerConfig? config = null,
        string? prompt = null,
        PromptTemplateConfig? promptUserConfig = null)
    {
        Verify.NotNull(kernel);
        _kernel = kernel;

        Config = config ?? new StructuredPlannerConfig();
        Config.ExcludedSkills.Add(RestrictedSkillName);

        var promptTemplate = prompt ?? EmbeddedResource.Read("Prompts.Stepwise.skprompt.txt");

        _systemStepFunction = _kernel.CreateFunctionCall(
            skillName: RestrictedSkillName,
            promptTemplate: promptTemplate,
            callFunctionsAutomatically: false,
            targetFunction: StepwisePlan,
            maxTokens: 1024, temperature: 1.0);

        _executeFunction = _kernel.ImportSkill(this, RestrictedSkillName);

        _context = _kernel.CreateNewContext();
        _logger = _kernel.LoggerFactory.CreateLogger(nameof(StructuredStepwisePlanner));

    }


    /// <inheritdoc />
    public Task<Plan> CreatePlanAsync(string goal, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrEmpty(goal))
        {
            throw new SKException("The goal specified is empty");
        }
        Plan planStep = new(_executeFunction["ExecutePlan"]);

        planStep.Parameters.Set("question", goal);

        planStep.Outputs.Add("agentScratchPad");
        planStep.Outputs.Add("stepCount");
        planStep.Outputs.Add("skillCount");
        planStep.Outputs.Add("stepsTaken");

        Plan plan = new(goal);

        plan.AddSteps(planStep);

        return Task.FromResult(plan);
    }


    [SKFunction] [SKName("ExecutePlan")] [Description("Execute a plan")]
    public async Task<SKContext> ExecutePlanAsync(
        [Description("The question to answer")]
        string question,
        SKContext context)
    {
        List<StepFunctionCall> stepsTaken = new();

        if (!string.IsNullOrEmpty(question))
        {
            for (int i = 0; i < Config.MaxIterations; i++)
            {
                string scratchPad = CreateScratchPad(question, stepsTaken);
                context.Variables.Set("agentScratchPad", scratchPad);

                SKContext? result = await _systemStepFunction.InvokeAsync(context).ConfigureAwait(false);

                if (result.ErrorOccurred)
                {
                    throw new SKException($"Error occurred while executing stepwise plan: {result.LastException?.Message}", result.LastException);
                }
                StepFunctionCall? nextStep = result.ToFunctionCallResult<StepFunctionCall>();

                if (nextStep == null)
                {
                    throw new InvalidOperationException("Failed to parse step from response text.");
                }

                if (!string.IsNullOrEmpty(nextStep.FinalAnswer))
                {
                    stepsTaken.Add(nextStep);
                    _logger?.LogTrace("Final Answer: {FinalAnswer}", nextStep.FinalAnswer);
                    context.Variables.Update(nextStep.FinalAnswer);
                    string updatedScratchPlan = CreateScratchPad(question, stepsTaken);
                    context.Variables.Set("agentScratchPad", updatedScratchPlan);

                    // Add additional results to the context
                    AddExecutionStatsToContext(stepsTaken, context);
                    return context;
                }

                stepsTaken.Add(nextStep);

                _logger?.LogTrace("Thought: {Thought}", nextStep.Thought);

                if (nextStep.Action != null)
                {
                    _logger?.LogInformation("Action: {Action}. Iteration: {Iteration}.", nextStep.Action.Function, i + 1);
                    _logger?.LogTrace("Action: {Action}({ActionVariables}). Iteration: {Iteration}.", nextStep.Action.Function, JsonSerializer.Serialize(nextStep.Action.Parameters), i + 1);

                    try
                    {
                        await Task.Delay(Config.MinIterationTimeMs).ConfigureAwait(false);
                        string? actionResult = await InvokeActionAsync(nextStep.Action).ConfigureAwait(false);
                        nextStep.ActionResult = string.IsNullOrEmpty(actionResult) ? "Got no result from action" : actionResult;
                    }
                    catch (Exception ex) when (!ex.IsCriticalException())
                    {
                        nextStep.ActionResult = $"Error invoking action {nextStep.Action.Function} : {ex.Message}";
                        _logger?.LogWarning(ex, "Error invoking action {Action}", nextStep.Action.Function);
                    }

                    _logger?.LogTrace("Observation: {Observation}", nextStep.Observation);
                }
                else
                {
                    _logger?.LogInformation($"[Action]: No action to take");
                }
                // sleep 3 seconds
                await Task.Delay(TimeSpan.FromMilliseconds(Config.MinIterationTimeMs)).ConfigureAwait(false);
            }

            context.Variables.Update($"Result not found, review _stepsTaken to see what happened.\n{JsonSerializer.Serialize(stepsTaken)}");
        }
        else
        {
            context.Variables.Update("Question not found.");
        }

        return context;
    }


    private string CreateScratchPad(string question, IReadOnlyList<StepFunctionCall> stepsTaken)
    {
        if (stepsTaken.Count == 0)
        {
            return string.Empty;
        }

        List<string> scratchPadLines = new()
        {
            ScratchPadPrefix,
        };

        var insertPoint = scratchPadLines.Count;

        for (var i = stepsTaken.Count - 1; i >= 0; i--)
        {
            if (scratchPadLines.Count / 4.0 > Config.MaxTokens * 0.75)
            {
                _logger.LogDebug("Scratchpad is too long, truncating. Skipping {CountSkipped} steps.", i + 1);
                break;
            }

            StepFunctionCall s = stepsTaken[i];
            var formattedString = s.ToFormattedString();

            if (!string.IsNullOrEmpty(formattedString))
            {
                scratchPadLines.Insert(insertPoint, formattedString);
            }
        }

        var scratchPad = string.Join("\n", scratchPadLines).Trim();

        if (!string.IsNullOrWhiteSpace(scratchPad))
        {
            _logger.LogTrace("Scratchpad: {ScratchPad}", scratchPad);
        }

        return scratchPad;
    }


    private async Task<string> InvokeActionAsync(FunctionCallResult functionCall)
    {
        _context.Skills.TryGetFunction(functionCall, out ISKFunction? targetFunction);

        if (targetFunction == null)
        {
            throw new SKException($"The function '{functionCall.Function}' was not found.");
        }

        try
        {
            SKContext? result = await targetFunction.InvokeAsync(functionCall.FunctionParameters()).ConfigureAwait(false);

            if (result.ErrorOccurred)
            {
                _logger.LogError("Error occurred: {Error}", result.LastException);
                return $"Error occurred: {result.LastException}";
            }

            _logger.LogTrace("Invoked {FunctionName}. Result: {Result}", targetFunction.Name, result.Result);

            return result.Result;
        }
        catch (Exception e) when (!e.IsCriticalException())
        {
            _logger?.LogError(e, "Something went wrong in system step: {0}.{1}. Error: {2}", targetFunction.SkillName, targetFunction.Name, e.Message);
            return $"Something went wrong in system step: {targetFunction.SkillName}.{targetFunction.Name}. Error: {e.Message} {e.InnerException.Message}";
        }
    }


    private static void AddExecutionStatsToContext(List<StepFunctionCall> stepsTaken, SKContext context)
    {
        context.Variables.Set("stepCount", stepsTaken.Count.ToString(CultureInfo.InvariantCulture));
        context.Variables.Set("stepsTaken", JsonSerializer.Serialize(stepsTaken));

        Dictionary<string, int> functionCounts = new();

        foreach (StepFunctionCall? step in stepsTaken.Where(step => !string.IsNullOrEmpty(step.Function)))
        {
            if (!functionCounts.TryGetValue(step.Function, out int currentCount))
            {
                currentCount = 0;
            }
            functionCounts[step.Function] = currentCount + 1;
        }

        string functionCallListWithCounts = string.Join(", ", functionCounts.Keys.Select(func =>
            $"{func}({functionCounts[func]})"));

        string functionCallsStr = functionCounts.Values.Sum().ToString(CultureInfo.InvariantCulture);

        context.Variables.Set("functionCount", $"{functionCallsStr} ({functionCallListWithCounts})");
        Console.WriteLine(string.Join("\n", context.Variables.Select(v => $"{v.Key}: {v.Value}")));
    }


    /// <summary>
    /// The configuration for the StepwisePlanner
    /// </summary>
    private StructuredPlannerConfig Config { get; }

    // Context used to access the list of functions in the kernel
    private readonly SKContext _context;
    private readonly IKernel _kernel;
    private readonly ILogger _logger;
    private readonly IDictionary<string, ISKFunction> _executeFunction;

    private readonly ISKFunction _systemStepFunction;

    /// <summary>
    /// The name to use when creating semantic functions that are restricted from plan creation
    /// </summary>
    private const string RestrictedSkillName = "StepwisePlanner_Excluded";

    /// <summary>
    /// The prefix used for the scratch pad
    /// </summary>
    private const string ScratchPadPrefix = "This was my previous work (but they haven't seen any of it! They only see what I return as final answer):";

    private static FunctionDefinition StepwisePlan => new()
    {
        Name = "stepwiseAction",
        Description = "Decide the best stepwise action to take to answer the given question",
        Parameters = BinaryData.FromObjectAsJson(
            new
            {
                Type = "object",
                Properties = new
                {
                    Step = new
                    {
                        Type = "object",
                        Description = "Step data structure",
                        Properties = new
                        {
                            Action = new
                            {
                                Type = "object",
                                Description = "Action data structure",
                                Properties = new
                                {
                                    Function = new
                                    {
                                        Type = "string",
                                        Description = "Name of the function chosen"
                                    },
                                    Parameters = new
                                    {
                                        Type = "array",
                                        Description = "Parameter values",
                                        Items = new
                                        {
                                            Type = "object",
                                            Description = "Parameter value",
                                            Properties = new
                                            {
                                                Name = new
                                                {
                                                    Type = "string",
                                                    Description = "Parameter name"
                                                },
                                                Value = new
                                                {
                                                    Type = "string",
                                                    Description = "Parameter value"
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            Thought = new
                            {
                                Type = "string",
                                Description = "Current thought context"
                            },
                            Observation = new
                            {
                                Type = "string",
                                Description = "Observation from the action result"
                            },
                            Final_Answer = new
                            {
                                Type = "string",
                                Description = "Final answer if found"
                            }
                        }
                    }
                }
            },
            new JsonSerializerOptions() { PropertyNamingPolicy = JsonNamingPolicy.CamelCase })
    };
}
