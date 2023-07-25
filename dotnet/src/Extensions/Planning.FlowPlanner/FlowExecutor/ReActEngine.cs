// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0130 // Namespace does not match folder structure
// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticKernel.Planning.Flow;
#pragma warning restore IDE0130 // Namespace does not match folder structure

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.SkillDefinition;
using System.Text.RegularExpressions;
using Microsoft.SemanticKernel.SemanticFunctions;
using System.Linq;
using System.Text.Json;

/// <summary>
/// Chat ReAct Engine
/// </summary>
internal sealed class ReActEngine
{
    /// <summary>
    /// The logger
    /// </summary>
    private readonly ILogger _logger;

    /// <summary>
    /// Re-Act function for flow execution
    /// </summary>
    private readonly ISKFunction _reActFunction;

    /// <summary>
    /// The flow planner config
    /// </summary>
    private readonly FlowPlannerConfig _config;

    /// <summary>
    /// The goal to use when creating semantic functions that are restricted from flow creation
    /// </summary>
    private const string RestrictedSkillName = "ReActEngine_Excluded";

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

    /// <summary>
    /// The prefix used for the scratch pad
    /// </summary>
    private const string ScratchPadPrefix =
        "This was my previous work (but they haven't seen any of it! They only see what I return as final answer):";

    /// <summary>
    /// The regex for parsing the action response
    /// </summary>
    private static readonly Regex s_actionRegex =
        new(@"\[ACTION\][^{}]*({(?:[^{}]*{[^{}]*})*[^{}]*})", RegexOptions.Singleline);

    /// <summary>
    /// The regex for parsing the final action response
    /// </summary>
    private static readonly Regex s_finalActionRegex =
        new(@"\[FINAL.+\][^{}]*({(?:[^{}]*{[^{}]*})*[^{}]*})", RegexOptions.Singleline);

    /// <summary>
    /// The regex for parsing the thought response
    /// </summary>
    private static readonly Regex s_thoughtRegex =
        new(@"(\[THOUGHT\])?(?<thought>.+?)(?=\[ACTION\]|$)", RegexOptions.Singleline);

    /// <summary>
    /// The regex for parsing the final answer response
    /// </summary>
    private static readonly Regex s_finalAnswerRegex =
        new(@"\[FINAL.+\](?<final_answer>.+)", RegexOptions.Singleline);

    internal ReActEngine(IKernel systemKernel, ILogger logger, FlowPlannerConfig config)
    {
        this._logger = logger;

        this._config = config;
        this._config.ExcludedSkills.Add(RestrictedSkillName);

        var promptConfig = new PromptTemplateConfig();
        var promptTemplate = EmbeddedResource.Read("Skills.ReActEngine.skprompt.txt");
        string promptConfigString = EmbeddedResource.Read("Skills.ReActEngine.config.json");
        if (!string.IsNullOrEmpty(promptConfigString))
        {
            promptConfig = PromptTemplateConfig.FromJson(promptConfigString);
        }

        promptConfig.Completion.MaxTokens = config.MaxTokens;

        this._reActFunction = this.ImportSemanticFunction(systemKernel, "ReActFunction", promptTemplate, promptConfig);
    }

    internal async Task<ReActStep?> GetNextStepAsync(SKContext context, string question, List<ReActStep> previousSteps)
    {
        context.Variables.Set("question", question);
        var scratchPad = this.CreateScratchPad(question, previousSteps);
        context.Variables.Set("agentScratchPad", scratchPad);
        context.Variables.Set("functionDescriptions", this.GetFunctionDescriptions(context));
        this._logger?.LogDebug("Scratchpad: {ScratchPad}", scratchPad);

        var llmResponse = await this._reActFunction.InvokeAsync(context).ConfigureAwait(false);
        if (llmResponse.ErrorOccurred)
        {
            string message = $"Error occurred while executing action step: {llmResponse.LastErrorDescription}";
            var exception = new PlanningException(PlanningException.ErrorCodes.UnknownError, message, llmResponse.LastException);
            context.Fail(exception.Message, exception);
            return null;
        }

        string llmResponseText = llmResponse.Result.Trim();
        this._logger?.LogDebug("Response : {ActionText}", llmResponseText);

        var actionStep = this.ParseResult(llmResponseText);

        if (!string.IsNullOrEmpty(actionStep.Action) || previousSteps.Count == 0)
        {
            return actionStep;
        }

        actionStep.Observation = "Failed to parse valid action step, missing action or final answer.";
        this._logger?.LogWarning("Failed to parse valid action step from llm response={LLMResponseText}", llmResponseText);
        this._logger?.LogWarning("Scratchpad={ScratchPad}", scratchPad);

        return actionStep;
    }

    internal async Task<string> InvokeActionAsync(ReActStep actionStep, string chatInput, ChatHistory chatHistory, IKernel kernel, SKContext context)
    {
        var variables = actionStep.ActionVariables ?? new Dictionary<string, string>();

        variables[Constants.ActionVariableNames.ChatInput] = chatInput;
        variables[Constants.ActionVariableNames.ChatHistory] = ChatHistorySerializer.Serialize(chatHistory);
        this._logger?.LogInformation("Action: {Action}({ActionVariables})", actionStep.Action, JsonSerializer.Serialize(variables));

        var availableFunctions = this.GetAvailableFunctions(context);
        var targetFunction = availableFunctions.FirstOrDefault(f => ToFullyQualifiedName(f) == actionStep.Action);
        if (targetFunction == null)
        {
            throw new MissingMethodException($"The function '{actionStep.Action}' was not found.");
        }

        try
        {
            var function = kernel.Func(targetFunction.SkillName, targetFunction.Name);
            var actionContext = this.CreateActionContext(variables, kernel);

            var result = await function.InvokeAsync(actionContext).ConfigureAwait(false);

            if (result.ErrorOccurred)
            {
                this._logger?.LogError("Error occurred: {Error}", result.LastException);
                return $"Error occurred: {result.LastException}";
            }

            foreach (var variable in actionContext.Variables)
            {
                context.Variables.Set(variable.Key, variable.Value);
            }

            this._logger?.LogDebug("Invoked {FunctionName}. Result: {Result}", targetFunction.Name, result.Result);

            return result.Result;
        }
        catch (Exception e) when (!e.IsCriticalException())
        {
            this._logger?.LogError(e, "Something went wrong in action step: {0}.{1}. Error: {2}", targetFunction.SkillName, targetFunction.Name, e.Message);
            return $"Something went wrong in action step: {targetFunction.SkillName}.{targetFunction.Name}. Error: {e.Message} {e.InnerException?.Message}";
        }
    }

    private SKContext CreateActionContext(Dictionary<string, string> actionVariables, IKernel kernel)
    {
        var actionContext = kernel.CreateNewContext();
        foreach (var kvp in actionVariables)
        {
            actionContext.Variables.Set(kvp.Key, kvp.Value);
        }

        return actionContext;
    }

    private ISKFunction ImportSemanticFunction(IKernel kernel, string functionName, string promptTemplate, PromptTemplateConfig config)
    {
        var template = new PromptTemplate(promptTemplate, config, kernel.PromptTemplateEngine);
        var functionConfig = new SemanticFunctionConfig(config, template);

        return kernel.RegisterSemanticFunction(RestrictedSkillName, functionName, functionConfig);
    }

    private string CreateScratchPad(string question, List<ReActStep> stepsTaken)
    {
        if (stepsTaken.Count == 0)
        {
            return string.Empty;
        }

        var scratchPadLines = new List<string>
        {
            // Add the original first thought
            ScratchPadPrefix,
            $"{Thought} {stepsTaken[0].Thought}"
        };

        // Keep track of where to insert the next step
        var insertPoint = scratchPadLines.Count;

        // Keep the most recent steps in the scratch pad.
        for (var i = stepsTaken.Count - 1; i >= 0; i--)
        {
            if (scratchPadLines.Count / 4.0 > (this._config.MaxTokens * 0.75))
            {
                this._logger.LogDebug("Scratchpad is too long, truncating. Skipping {CountSkipped} steps.", i + 1);
                break;
            }

            var s = stepsTaken[i];

            if (!string.IsNullOrEmpty(s.Observation))
            {
                scratchPadLines.Insert(insertPoint, $"{Observation} {s.Observation}");
            }

            if (!string.IsNullOrEmpty(s.Action))
            {
                // ignore the built-in context variables
                var variablesToPrint = s.ActionVariables?.Where(v => !Constants.ActionVariableNames.All.Contains(v.Key)).ToDictionary(_ => _.Key, _ => _.Value);
                scratchPadLines.Insert(insertPoint, $"{Action} {{\"action\": \"{s.Action}\",\"action_variables\": {JsonSerializer.Serialize(variablesToPrint)}}}");
            }

            if (i != 0)
            {
                scratchPadLines.Insert(insertPoint, $"{Thought} {s.Thought}");
            }
        }

        return string.Join("\n", scratchPadLines).Trim();
    }

    private ReActStep ParseResult(string input)
    {
        var result = new ReActStep
        {
            OriginalResponse = input
        };

        // Extract final answer
        Match finalAnswerMatch = s_finalAnswerRegex.Match(input);

        if (finalAnswerMatch.Success)
        {
            result.FinalAnswer = finalAnswerMatch.Groups[1].Value.Trim();
        }

        // Extract thought
        Match thoughtMatch = s_thoughtRegex.Match(input);

        if (thoughtMatch.Success)
        {
            result.Thought = thoughtMatch.Value.Trim();
        }
        else if (!input.Contains(Action))
        {
            result.Thought = input;
        }
        else
        {
            throw new InvalidOperationException("Unexpected input format");
        }

        result.Thought = result.Thought.Replace(Thought, string.Empty).Trim();

        // Extract action
        string actionStepJson = input;
        Match actionMatch = s_actionRegex.Match(input);
        if (actionMatch.Success)
        {
            actionStepJson = actionMatch.Groups[1].Value.Trim();
        }
        else
        {
            Match finalActionMatch = s_finalActionRegex.Match(input);
            if (finalActionMatch.Success)
            {
                actionStepJson = finalActionMatch.Groups[1].Value.Trim();
            }
        }

        try
        {
            var reActStep = JsonSerializer.Deserialize<ReActStep>(actionStepJson);
            if (reActStep == null)
            {
                result.Observation = $"Action step parsing error, empty JSON: {actionStepJson}";
            }
            else
            {
                result.Action = reActStep.Action;
                result.ActionVariables = reActStep.ActionVariables;
            }
        }
        catch (JsonException)
        {
            result.Observation = $"Action step parsing error, invalid JSON: {actionStepJson}";
        }

        if (string.IsNullOrEmpty(result.Thought) && string.IsNullOrEmpty(result.Action))
        {
            result.Observation = "Action step error, no thought or action found. Please give a valid thought and/or action.";
        }

        return result;
    }

    private string GetFunctionDescriptions(SKContext context)
    {
        var availableFunctions = this.GetAvailableFunctions(context);

        string functionDescriptions = string.Join("\n", availableFunctions.Select(ToManualString));
        return functionDescriptions;
    }

    private IEnumerable<FunctionView> GetAvailableFunctions(SKContext context)
    {
        FunctionsView functionsView = context.Skills!.GetFunctionsView();

        var excludedSkills = this._config.ExcludedSkills ?? new HashSet<string>();
        var excludedFunctions = this._config.ExcludedFunctions ?? new HashSet<string>();

        var availableFunctions =
            functionsView.NativeFunctions
                .Concat(functionsView.SemanticFunctions)
                .SelectMany(x => x.Value)
                .Where(s => !excludedSkills.Contains(s.SkillName) && !excludedFunctions.Contains(s.Name))
                .OrderBy(x => x.SkillName)
                .ThenBy(x => x.Name);
        return availableFunctions;
    }

    private static string ToManualString(FunctionView function)
    {
        var inputs = string.Join("\n", function.Parameters.Select(parameter =>
        {
            var defaultValueString = string.IsNullOrEmpty(parameter.DefaultValue) ? string.Empty : $"(default='{parameter.DefaultValue}')";
            return $"  - {parameter.Name}: {parameter.Description} {defaultValueString}";
        }));

        var functionDescription = function.Description.Trim();

        if (string.IsNullOrEmpty(inputs))
        {
            return $"{ToFullyQualifiedName(function)}: {functionDescription}\n";
        }

        return $"{ToFullyQualifiedName(function)}: {functionDescription}\n{inputs}\n";
    }

    private static string ToFullyQualifiedName(FunctionView function)
    {
        return $"{function.SkillName}.{function.Name}";
    }
}
