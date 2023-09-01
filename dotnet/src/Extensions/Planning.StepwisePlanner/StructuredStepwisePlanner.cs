// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Planning.Stepwise;

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Globalization;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using AI.ChatCompletion;
using Azure.AI.OpenAI;
using Connectors.AI.OpenAI.AzureSdk.FunctionCalling;
using Diagnostics;
using Extensions.Logging;
using Orchestration;
using SemanticFunctions;
using SkillDefinition;
using TemplateEngine.Prompt;
using FunctionCall = Connectors.AI.OpenAI.AzureSdk.FunctionCalling.FunctionCall;


public class StructuredStepwisePlanner : IStepwisePlanner
{

    public StructuredStepwisePlanner(
        IKernel kernel,
        StepwisePlannerConfig? config = null,
        string? prompt = null,
        PromptTemplateConfig? promptUserConfig = null)
    {
        Verify.NotNull(kernel);
        _kernel = kernel;

        Config = config ?? new StepwisePlannerConfig();
        Config.ExcludedSkills.Add(RestrictedSkillName);

        var promptConfig = promptUserConfig ?? new PromptTemplateConfig();
        _promptTemplate = prompt ?? EmbeddedResource.Read("Skills.StructuredStep.skprompt.txt");

        if (promptUserConfig == null)
        {
            var promptConfigString = EmbeddedResource.Read("Skills.StructuredStep.config.json");

            if (!string.IsNullOrEmpty(promptConfigString))
            {
                promptConfig = PromptTemplateConfig.FromJson(promptConfigString);
            }
        }

        promptConfig.Completion.MaxTokens = Config.MaxTokens;

        // this._systemStepFunction = this.ImportSemanticFunction(this._kernel, "StepwiseStep", promptTemplate, promptConfig);
        _kernel.ImportSkill(this, RestrictedSkillName);

        _context = _kernel.CreateNewContext();
        _logger = _kernel.LoggerFactory.CreateLogger(nameof(StepwisePlanner));
    }


    /// <inheritdoc />
    public Plan CreatePlan(string goal)
    {
        if (string.IsNullOrEmpty(goal))
        {
            throw new SKException("The goal specified is empty");
        }

        var executeFunction = _kernel.Func(this, "ExecutePlan");
        Plan planStep = new(executeFunction);

        planStep.Parameters.Set("question", goal);

        planStep.Outputs.Add("agentScratchPad");
        planStep.Outputs.Add("stepCount");
        planStep.Outputs.Add("skillCount");
        planStep.Outputs.Add("stepsTaken");

        Plan plan = new(goal);

        plan.AddSteps(planStep);

        return plan;
    }


    [SKFunction] [SKName("ExecutePlan")] [Description("Execute a plan")]
    public async Task<SKContext> ExecutePlanAsync(
        [Description("The question to answer")]
        string question,
        SKContext context)
    {
        List<StructuredStep> stepsTaken = new();

        var chatCompletion = (IOpenAIChatCompletion)_kernel.GetService<IChatCompletion>();
        List<FunctionDefinition> functionDefinitions = GetAvailableFunctions().ToList();

        if (!string.IsNullOrEmpty(question))
        {
            for (var i = 0; i < Config.MaxIterations; i++)
            {
                var scratchPad = CreateScratchPad(question, stepsTaken);

                context.Variables.Set("agentScratchPad", scratchPad);

                var templateEngine = new PromptTemplateEngine();
                var prompt = await templateEngine.RenderAsync(_promptTemplate, _context).ConfigureAwait(false);
                var chatHistory = chatCompletion.CreateNewChat(prompt);

                var nextStep = await chatCompletion.GenerateResponseAsync<StructuredStep>(
                    chatHistory,
                    new ChatRequestSettings()
                        { Temperature = 0.0, MaxTokens = Config.MaxTokens },
                    StepwisePlan, functionDefinitions.ToArray()).ConfigureAwait(false);

                // var llmResponse = await _systemStepFunction.InvokeAsync(context).ConfigureAwait(false);

                // if (llmResponse.ErrorOccurred)
                // {
                //     throw new SKException($"Error occurred while executing stepwise plan: {llmResponse.LastException?.Message}", llmResponse.LastException);
                // }

                // Attempt to deserialize the response
                // var actionText = llmResponse.Result.Trim();
                // var nextStep = JsonSerializer.Deserialize<StructuredStep>(actionText);

                if (nextStep == null)
                {
                    throw new InvalidOperationException("Failed to parse step from response text.");
                }

                stepsTaken.Add(nextStep);

                if (!string.IsNullOrEmpty(nextStep.FinalAnswer))
                {
                    _logger?.LogTrace("Final Answer: {FinalAnswer}", nextStep.FinalAnswer);

                    context.Variables.Update(nextStep.FinalAnswer);
                    var updatedScratchPlan = CreateScratchPad(question, stepsTaken);
                    context.Variables.Set("agentScratchPad", updatedScratchPlan);

                    // Add additional results to the context
                    AddExecutionStatsToContext(stepsTaken, context);

                    return context;
                }

                _logger?.LogTrace("Thought: {Thought}", nextStep.Thought);

                if (!string.IsNullOrEmpty(nextStep!.Function!))
                {
                    _logger?.LogInformation("Action: {Action}. Iteration: {Iteration}.", nextStep.Function, i + 1);
                    _logger?.LogTrace("Action: {Action}({ActionVariables}). Iteration: {Iteration}.",
                        nextStep.Function, JsonSerializer.Serialize(nextStep.Parameters), i + 1);

                    try
                    {
                        await Task.Delay(Config.MinIterationTimeMs).ConfigureAwait(false);
                        var result = await InvokeActionAsync(nextStep).ConfigureAwait(false);

                        if (string.IsNullOrEmpty(result))
                        {
                            nextStep.Observation = "Got no result from action";
                        }
                        else
                        {
                            nextStep.Observation = result;
                        }
                    }
                    catch (Exception ex) when (!ex.IsCriticalException())
                    {
                        nextStep.Observation = $"Error invoking action {nextStep.Function} : {ex.Message}";
                        _logger?.LogWarning(ex, "Error invoking action {Action}", nextStep.Function);
                    }

                    _logger?.LogTrace("Observation: {Observation}", nextStep.Observation);
                }
                else
                {
                    _logger?.LogInformation("{Action}: No action to take");
                }

                // sleep 3 seconds
                await Task.Delay(Config.MinIterationTimeMs).ConfigureAwait(false);
            }

            context.Variables.Update($"Result not found, review _stepsTaken to see what happened.\n{JsonSerializer.Serialize(stepsTaken)}");
        }
        else
        {
            context.Variables.Update("Question not found.");
        }

        return context;
    }


    private string CreateScratchPad(string question, IReadOnlyList<StructuredStep> stepsTaken)
    {
        if (stepsTaken.Count == 0)
        {
            return string.Empty;
        }

        List<string> scratchPadLines = new()
        {
            ScratchPadPrefix,
            $"{Thought}: {stepsTaken[0].Thought}"
        };

        var insertPoint = scratchPadLines.Count;

        for (var i = stepsTaken.Count - 1; i >= 0; i--)
        {
            if (scratchPadLines.Count / 4.0 > Config.MaxTokens * 0.75)
            {
                _logger.LogDebug("Scratchpad is too long, truncating. Skipping {CountSkipped} steps.", i + 1);
                break;
            }

            var s = stepsTaken[i];

            if (!string.IsNullOrEmpty(s.Observation))
            {
                scratchPadLines.Insert(insertPoint, $"{Observation}: {s.Observation}");
            }

            if (!string.IsNullOrEmpty(s.Function))
            {
                scratchPadLines.Insert(insertPoint, $"{Action}: {JsonSerializer.Serialize(new { action = s.Function, action_variables = s.Parameters })}");
            }

            if (i != 0 && s.Thought != null)
            {
                scratchPadLines.Insert(insertPoint, $"{Thought}: {s.Thought}");
            }
        }

        var scratchPad = string.Join("\n", scratchPadLines).Trim();

        if (!string.IsNullOrWhiteSpace(scratchPad))
        {
            _logger.LogTrace("Scratchpad: {ScratchPad}", scratchPad);
        }

        return scratchPad;
    }


    private async Task<string> InvokeActionAsync(FunctionCall functionCall)
    {
        _context.Skills.TryGetFunction(functionCall.Function, out var targetFunction);

        if (targetFunction == null)
        {
            throw new SKException($"The function '{functionCall.Function}' was not found.");
        }

        try
        {
            var function = _kernel.Func(targetFunction.SkillName, targetFunction.Name);

            var result = await function.InvokeAsync(functionCall.FunctionParameters()).ConfigureAwait(false);

            if (result.ErrorOccurred)
            {
                _logger?.LogError("Error occurred: {Error}", result.LastException);
                return $"Error occurred: {result.LastException}";
            }

            _logger?.LogTrace("Invoked {FunctionName}. Result: {Result}", targetFunction.Name, result.Result);

            return result.Result;
        }
        catch (Exception e) when (!e.IsCriticalException())
        {
            _logger?.LogError(e, "Something went wrong in system step: {0}.{1}. Error: {2}", targetFunction.SkillName, targetFunction.Name, e.Message);
            return $"Something went wrong in system step: {targetFunction.SkillName}.{targetFunction.Name}. Error: {e.Message} {e.InnerException.Message}";
        }
    }


    private static void AddExecutionStatsToContext(List<StructuredStep> stepsTaken, SKContext context)
    {
        context.Variables.Set("stepCount", stepsTaken.Count.ToString(CultureInfo.InvariantCulture));
        context.Variables.Set("stepsTaken", JsonSerializer.Serialize(stepsTaken));

        Dictionary<string, int> functionCounts = new();

        foreach (var step in stepsTaken.Where(step => !string.IsNullOrEmpty(step.Function)))
        {
            if (!functionCounts.TryGetValue(step.Function, out var currentCount))
            {
                currentCount = 0;
            }
            functionCounts[step.Function] = currentCount + 1;
        }

        var functionCallListWithCounts = string.Join(", ", functionCounts.Keys.Select(func =>
            $"{func}({functionCounts[func]})"));

        var functionCallsStr = functionCounts.Values.Sum().ToString(CultureInfo.InvariantCulture);

        context.Variables.Set("functionCount", $"{functionCallsStr} ({functionCallListWithCounts})");
    }


    private IEnumerable<FunctionDefinition> GetAvailableFunctions()
    {

        HashSet<string> excludedSkills = Config.ExcludedSkills;
        HashSet<string> excludedFunctions = Config.ExcludedFunctions;

        return _context.Skills!.GetFunctionDefinitions(excludedSkills, excludedFunctions);
    }


    /// <summary>
    /// The configuration for the StepwisePlanner
    /// </summary>
    private StepwisePlannerConfig Config { get; }

    // Context used to access the list of functions in the kernel
    private readonly SKContext _context;
    private readonly IKernel _kernel;
    private readonly ILogger _logger;

    private readonly ISKFunction _systemStepFunction;

    private readonly string _promptTemplate;

    /// <summary>
    /// The name to use when creating semantic functions that are restricted from plan creation
    /// </summary>
    private const string RestrictedSkillName = "StepwisePlanner_Excluded";

    /// <summary>
    /// The prefix used for the scratch pad
    /// </summary>
    private const string ScratchPadPrefix = "This was my previous work (but they haven't seen any of it! They only see what I return as final answer):";

    /// <summary>
    /// The Action tag
    /// </summary>
    private const string Action = "[ACTION]";

    /// <summary>
    /// The Thought tag
    /// </summary>
    private const string Thought = "[THOUGHT]";

    /// <summary>
    /// The Observation tag
    /// </summary>
    private const string Observation = "[OBSERVATION]";

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
                            FinalAnswer = new
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
