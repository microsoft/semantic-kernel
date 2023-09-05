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
using AI.ChatCompletion;
using Azure.AI.OpenAI;
using Connectors.AI.OpenAI.ChatCompletion;
using Connectors.AI.OpenAI.FunctionCalling;
using Connectors.AI.OpenAI.FunctionCalling.Extensions;
using Diagnostics;
using Microsoft.Extensions.Logging;
using Orchestration;
using SkillDefinition;
using TemplateEngine.Prompt;


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
    public StructuredStepwisePlanner(
        IKernel kernel,
        StructuredPlannerConfig? config = null,
        string? prompt = null)
    {
        Verify.NotNull(kernel);
        _kernel = kernel;

        Config = config ?? new StructuredPlannerConfig();
        Config.ExcludedSkills.Add(RestrictedSkillName);

        _promptTemplate = prompt ?? EmbeddedResource.Read("Prompts.Stepwise.skprompt.txt");

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

        planStep.Parameters.Set("problem", goal);

        planStep.Outputs.Add("stepCount");
        planStep.Outputs.Add("skillCount");
        planStep.Outputs.Add("stepsTaken");

        Plan plan = new(goal);

        plan.AddSteps(planStep);

        return Task.FromResult(plan);
    }


    [SKFunction] [SKName("ExecutePlan")] [Description("Execute a plan")]
    public async Task<SKContext> ExecutePlanAsync(
        [Description("The problem to solve")] string problem,
        SKContext context)
    {
        List<StepwiseFunctionCallResult> stepsTaken = new();
        var promptTemplateEngine = new PromptTemplateEngine();
        var prompt = await promptTemplateEngine.RenderAsync(_promptTemplate, context).ConfigureAwait(false);
        _chatHistory = new OpenAIChatHistory(prompt);

        if (!string.IsNullOrEmpty(problem))
        {
            for (var i = 0; i < Config.MaxIterations; i++)
            {

                context.Variables.Set("stepsTaken", string.Join("\n", stepsTaken.Select((result, step) => result.ToStepResult(step + 1))));

                var chatCompletion = _kernel.GetService<IChatCompletion>();
                var requestSettings = GetRequestSettings(context);
                var nextStep = await chatCompletion.GenerateResponseAsync<StepwiseFunctionCallResult>(
                        _chatHistory,
                        requestSettings,
                        Config.SerializerOptions)
                    .ConfigureAwait(false);

                if (nextStep == null)
                {
                    throw new InvalidOperationException("Failed to parse step from response text.");
                }

                if (!string.IsNullOrEmpty(nextStep.FinalAnswer))
                {
                    stepsTaken.Add(nextStep);
                    _logger?.LogTrace("Final Answer: {FinalAnswer}", nextStep.FinalAnswer);
                    context.Variables.Update(nextStep.FinalAnswer);

                    // Add additional results to the context
                    AddExecutionStatsToContext(stepsTaken, context);
                    return context;
                }

                // forces the model to acknowledge it's past steps - no need for scratch pad
                _chatHistory.AddAssistantMessage(nextStep.ToStepResult(i + 1));

                _logger?.LogTrace("Thought: {Thought}", nextStep.Thought);

                if (nextStep.FunctionCall != null)
                {
                    _logger?.LogInformation("Function: {Action}. Iteration: {Iteration}", nextStep.FunctionCall.Function, i + 1);
                    _logger?.LogTrace("Function: {Action}({ActionVariables}). Iteration: {Iteration}.", nextStep.FunctionCall.Function, JsonSerializer.Serialize(nextStep.FunctionCall.Parameters), i + 1);

                    try
                    {
                        await Task.Delay(Config.MinIterationTimeMs).ConfigureAwait(false);
                        var actionResult = await InvokeActionAsync(nextStep.FunctionCall).ConfigureAwait(false);
                        // forces the model to "observe" the action result
                        _chatHistory.AddUserMessage(actionResult);
                        nextStep.FunctionResult = actionResult;
                        stepsTaken.Add(nextStep);
                    }
                    catch (Exception ex) when (!ex.IsCriticalException())
                    {
                        nextStep.FunctionResult = $"Error invoking action {nextStep.FunctionCall.Function} : {ex.Message}";
                        _logger?.LogWarning(ex, "Error invoking action {Action}", nextStep.FunctionCall.Function);
                    }

                    _logger?.LogTrace("Observation: {Observation}", nextStep.Observation);
                }
                else
                {
                    _logger?.LogInformation("[Action]: No action to take");
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


    private async Task<string> InvokeActionAsync(FunctionCallResult functionCall)
    {
        _context.Skills.TryGetFunction(functionCall, out var targetFunction);

        if (targetFunction == null)
        {
            throw new SKException($"The function '{functionCall.Function}' was not found.");
        }

        try
        {
            var result = await targetFunction.InvokeAsync(functionCall.FunctionParameters()).ConfigureAwait(false);

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


    private static void AddExecutionStatsToContext(List<StepwiseFunctionCallResult> stepsTaken, SKContext context)
    {
        context.Variables.Set("stepCount", stepsTaken.Count.ToString(CultureInfo.InvariantCulture));
        context.Variables.Set("stepsTaken", string.Join("\n", stepsTaken.Select((result, step) => result.ToStepResult(step + 1))));

        Dictionary<string, int> functionCounts = new();

        foreach (var step in stepsTaken.Where(step => !string.IsNullOrEmpty(step.FunctionCall?.Function)))
        {
            if (!functionCounts.TryGetValue(step.FunctionCall!.Function, out var currentCount))
            {
                currentCount = 0;
            }
            functionCounts[step.Function] = currentCount + 1;
        }

        var functionCallListWithCounts = string.Join(", ", functionCounts.Keys.Select(func =>
            $"{func}({functionCounts[func]})"));

        var functionCallsStr = functionCounts.Values.Sum().ToString(CultureInfo.InvariantCulture);

        context.Variables.Set("functionCount", $"{functionCallsStr} ({functionCallListWithCounts})");
        Console.WriteLine(string.Join("\n", context.Variables.Select(v => $"{v.Key}: {v.Value}")));
    }


    private FunctionCallRequestSettings GetRequestSettings(SKContext context)
    {
        List<FunctionDefinition> callableFunctions = context.Skills.GetFunctionDefinitions(Config.ExcludedSkills, Config.ExcludedFunctions).ToList();
        callableFunctions.Add(StepwisePlan);
        return new FunctionCallRequestSettings
        {
            CallableFunctions = callableFunctions,
            FunctionCall = StepwisePlan,
            MaxTokens = 1024,
            Temperature = 0.0,
            StopSequences = new List<string>()
            {
                "\n Observation:",
                "\n Thought:"
            }
        };
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

    private OpenAIChatHistory _chatHistory = new();
    private readonly string _promptTemplate;

    /// <summary>
    /// The name to use when creating semantic functions that are restricted from plan creation
    /// </summary>
    private const string RestrictedSkillName = "StepwisePlanner_Excluded";

    private static FunctionDefinition StepwisePlan => new()
    {
        Name = "stepwise_function_call",
        Description = "Take the next step to solve the problem",
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
                            Function_Call = new
                            {
                                Type = "object",
                                Description = "the function call to make",
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
