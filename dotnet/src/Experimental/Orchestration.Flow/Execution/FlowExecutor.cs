﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Experimental.Orchestration.Abstractions;
using Microsoft.SemanticKernel.Experimental.Orchestration.Extensions;

namespace Microsoft.SemanticKernel.Experimental.Orchestration.Execution;

/// <summary>
/// This is a flow executor which iterates over the flow steps and executes them one by one.
/// </summary>
/// <remarks>
/// For each step, it is executed in the ReAct (Reasoning-Act-Observe) style, which is similar as StepwisePlanner, with the following differences:
/// 1. It is implemented in a way so that the chat could be streamed for more effective reasoning, action and feedback loop.
/// 2. The user input would be part of observation for the engine to reason and determine next action.
/// 3. For each step, it is considered as complete by verifying all the outputs are provided in programmatic way, instead of LLM evaluation.
///
/// Further consolidation can happen in the future so that flow executor becomes a generalization of StepwisePlanner.
/// And both chatMode and completionMode could be supported.
/// </remarks>
internal partial class FlowExecutor : IFlowExecutor
{
    /// <summary>
    /// The kernel builder
    /// </summary>
    private readonly IKernelBuilder _kernelBuilder;

    /// <summary>
    /// The logger
    /// </summary>
    private readonly ILogger _logger;

    /// <summary>
    /// The global plugin collection
    /// </summary>
    private readonly Dictionary<object, string?> _globalPluginCollection;

    /// <summary>
    /// The flow planner config
    /// </summary>
    private readonly FlowOrchestratorConfig _config;

    /// <summary>
    /// The flow status provider
    /// </summary>
    private readonly IFlowStatusProvider _flowStatusProvider;

    /// <summary>
    /// System kernel for flow execution
    /// </summary>
    private readonly Kernel _systemKernel;

    /// <summary>
    /// Re-Act engine for flow execution
    /// </summary>
    private readonly ReActEngine _reActEngine;

    /// <summary>
    /// Restricted plugin name
    /// </summary>
    private const string RestrictedPluginName = "FlowExecutor_Excluded";

    /// <summary>
    /// The regex for parsing the final answer response
    /// </summary>
#if NET
    [GeneratedRegex(@"\[FINAL.+\](?<final_answer>.+)", RegexOptions.Singleline)]
    private static partial Regex FinalAnswerRegex();
#else
    private static Regex FinalAnswerRegex() => s_finalAnswerRegex;
    private static readonly Regex s_finalAnswerRegex = new(@"\[FINAL.+\](?<final_answer>.+)", RegexOptions.Singleline | RegexOptions.Compiled);
#endif

    /// <summary>
    /// The regex for parsing the question
    /// </summary>
#if NET
    [GeneratedRegex(@"\[QUESTION\](?<question>.+)", RegexOptions.Singleline)]
    private static partial Regex QuestionRegex();
#else
    private static Regex QuestionRegex() => s_questionRegex;
    private static readonly Regex s_questionRegex = new(@"\[QUESTION\](?<question>.+)", RegexOptions.Singleline | RegexOptions.Compiled);
#endif

    /// <summary>
    /// The regex for parsing the thought response
    /// </summary>
#if NET
    [GeneratedRegex(@"\[THOUGHT\](?<thought>.+)", RegexOptions.Singleline)]
    private static partial Regex ThoughtRegex();
#else
    private static Regex ThoughtRegex() => s_thoughtRegex;
    private static readonly Regex s_thoughtRegex = new(@"\[THOUGHT\](?<thought>.+)", RegexOptions.Singleline | RegexOptions.Compiled);
#endif

    /// <summary>
    /// Check repeat step function
    /// </summary>
    private readonly KernelFunction _checkRepeatStepFunction;

    /// <summary>
    /// Check start step function
    /// </summary>
    private readonly KernelFunction _checkStartStepFunction;

    /// <summary>
    /// ExecuteFlow function
    /// </summary>
    private readonly KernelFunction _executeFlowFunction;

    /// <summary>
    /// ExecuteStep function
    /// </summary>
    private readonly KernelFunction _executeStepFunction;

    internal FlowExecutor(IKernelBuilder kernelBuilder, IFlowStatusProvider statusProvider, Dictionary<object, string?> globalPluginCollection, FlowOrchestratorConfig? config = null)
    {
        this._kernelBuilder = kernelBuilder;
        this._systemKernel = kernelBuilder.Build();

        this._logger = this._systemKernel.LoggerFactory.CreateLogger(typeof(FlowExecutor)) ?? NullLogger.Instance;
        this._config = config ?? new FlowOrchestratorConfig();

        this._flowStatusProvider = statusProvider;
        this._globalPluginCollection = globalPluginCollection;

        var checkRepeatStepConfig = this.ImportPromptTemplateConfig("CheckRepeatStep");
        this._checkRepeatStepFunction = KernelFunctionFactory.CreateFromPrompt(checkRepeatStepConfig);

        var checkStartStepConfig = this.ImportPromptTemplateConfig("CheckStartStep");
        this._checkStartStepFunction = KernelFunctionFactory.CreateFromPrompt(checkStartStepConfig);

        this._config.ExcludedPlugins.Add(RestrictedPluginName);
        this._reActEngine = new ReActEngine(this._systemKernel, this._logger, this._config);

        this._executeFlowFunction = KernelFunctionFactory.CreateFromMethod(this.ExecuteFlowAsync, "ExecuteFlow", "Execute a flow");
        this._executeStepFunction = KernelFunctionFactory.CreateFromMethod(this.ExecuteStepAsync, "ExecuteStep", "Execute a flow step");
    }

    private PromptTemplateConfig ImportPromptTemplateConfig(string functionName)
    {
        var config = KernelFunctionYaml.ToPromptTemplateConfig(EmbeddedResource.Read($"Plugins.{functionName}.yaml")!);

        // if AIServiceIds is specified, only include the relevant execution settings
        if (this._config.AIServiceIds.Count > 0)
        {
            var serviceIdsToRemove = config.ExecutionSettings.Keys.Except(this._config.AIServiceIds);
            foreach (var serviceId in serviceIdsToRemove)
            {
                config.ExecutionSettings.Remove(serviceId);
            }
        }

        return config;
    }

    public async Task<FunctionResult> ExecuteFlowAsync(Flow flow, string sessionId, string input, KernelArguments kernelArguments)
    {
        Verify.NotNull(flow, nameof(flow));

        if (this._logger.IsEnabled(LogLevel.Information))
        {
            this._logger.LogInformation("Executing flow {FlowName} with sessionId={SessionId}.", flow.Name, sessionId);
        }

        var sortedSteps = flow.SortSteps();

        var rootContext = new KernelArguments(kernelArguments);

        // populate persisted state arguments
        ExecutionState executionState = await this._flowStatusProvider.GetExecutionStateAsync(sessionId).ConfigureAwait(false);
        List<string> outputs = [];

        while (executionState.CurrentStepIndex < sortedSteps.Count)
        {
            int stepIndex = executionState.CurrentStepIndex;
            FlowStep step = sortedSteps[stepIndex];

            foreach (var kv in executionState.Variables)
            {
                rootContext[kv.Key] = kv.Value;
            }

            this.ValidateStep(step, rootContext);

            // init step execution state
            string stepKey = $"{stepIndex}_{step.Goal}";
            if (!executionState.StepStates.TryGetValue(stepKey, out ExecutionState.StepExecutionState? stepState))
            {
                stepState = new ExecutionState.StepExecutionState();
                executionState.StepStates.Add(stepKey, stepState);
            }

            var stepId = $"{stepKey}_{stepState.ExecutionCount}";

            var continueLoop = false;
            var completed = step.Provides.All(executionState.Variables.ContainsKey);
            if (!completed)
            {
                // On the first iteration of an Optional or ZeroOrMore step, we need to check whether the user wants to start the step
                if (step.CompletionType is CompletionType.Optional or CompletionType.ZeroOrMore && stepState.Status == ExecutionState.Status.NotStarted)
                {
                    RepeatOrStartStepResult? startStep = await this.CheckStartStepAsync(rootContext, step, sessionId, stepId, input).ConfigureAwait(false);
                    if (startStep is null)
                    {
                        // Unknown error, try again
                        this._logger?.LogWarning("Unexpected error when checking whether to start the step, try again");
                        continue;
                    }
                    else if (startStep.Execute is null)
                    {
                        // Unconfirmed, prompt user
                        outputs.Add(startStep.Prompt!);
                        await this._flowStatusProvider.SaveExecutionStateAsync(sessionId, executionState).ConfigureAwait(false);
                        break;
                    }
                    else if (startStep.Execute.Value)
                    {
                        stepState.Status = ExecutionState.Status.InProgress;
                        await this._flowStatusProvider.SaveExecutionStateAsync(sessionId, executionState).ConfigureAwait(false);

                        if (this._logger?.IsEnabled(LogLevel.Information) ?? false)
                        {
                            this._logger.LogInformation("Need to start step {StepIndex} for iteration={Iteration}, goal={StepGoal}.", stepIndex, stepState.ExecutionCount, step.Goal);
                        }
                    }
                    else
                    {
                        // User doesn't want to run the step
                        foreach (var variable in step.Provides)
                        {
                            executionState.Variables[variable] = "[]";
                        }

                        await this.CompleteStepAsync(rootContext, sessionId, executionState, step, stepState).ConfigureAwait(false);

                        if (this._logger?.IsEnabled(LogLevel.Information) ?? false)
                        {
                            this._logger.LogInformation("Completed step {StepIndex} with iteration={Iteration}, goal={StepGoal}.", stepIndex, stepState.ExecutionCount, step.Goal);
                        }

                        continue;
                    }
                }

                // execute step
                if (this._logger?.IsEnabled(LogLevel.Information) ?? false)
                {
                    this._logger.LogInformation(
                        "Executing step {StepIndex} for iteration={Iteration}, goal={StepGoal}, input={Input}.", stepIndex,
                        stepState.ExecutionCount, step.Goal, input);
                }

                Kernel stepKernel = this._kernelBuilder.Build();
                var stepArguments = new KernelArguments();
                foreach (var key in step.Requires)
                {
                    stepArguments[key] = rootContext[key];
                }

                foreach (var key in step.Passthrough)
                {
                    if (rootContext.TryGetValue(key, out var val))
                    {
                        stepArguments[key] = val;
                    }
                }

                FunctionResult? stepResult;
                if (step is Flow flowStep)
                {
                    stepResult = await this.ExecuteFlowAsync(flowStep, $"{sessionId}_{stepId}", input, stepArguments).ConfigureAwait(false);
                }
                else
                {
                    var stepPlugins = step.LoadPlugins(stepKernel, this._globalPluginCollection);
                    foreach (var plugin in stepPlugins)
                    {
                        stepKernel.ImportPluginFromObject(plugin, plugin.GetType().Name);
                    }

                    stepResult = await this.ExecuteStepAsync(step, sessionId, stepId, input, stepKernel, stepArguments).ConfigureAwait(false);
                }

                if (!string.IsNullOrEmpty(stepResult.ToString()) && (stepResult.IsPromptInput() || stepResult.IsTerminateFlow()))
                {
                    if (stepResult.ValueType == typeof(List<string>))
                    {
                        outputs.AddRange(stepResult.GetValue<List<string>>()!);
                    }
                    else
                    {
                        outputs.Add(stepResult.ToString());
                    }
                }
                else if (stepResult.TryGetExitLoopResponse(out string? exitResponse))
                {
                    stepState.Status = ExecutionState.Status.Completed;

                    var metadata = stepResult.Metadata!.ToDictionary(kvp => kvp.Key, kvp => kvp.Value);
                    foreach (var variable in step.Provides)
                    {
                        if (!metadata.ContainsKey(variable))
                        {
                            metadata[variable] = string.Empty;
                        }
                    }

                    stepResult = new FunctionResult(stepResult.Function, stepResult.GetValue<object>(), metadata: metadata);

                    if (!string.IsNullOrWhiteSpace(exitResponse))
                    {
                        outputs.Add(exitResponse!);
                    }

                    if (this._logger?.IsEnabled(LogLevel.Information) ?? false)
                    {
                        this._logger.LogInformation("Exiting loop for step {StepIndex} with iteration={Iteration}, goal={StepGoal}.", stepIndex, stepState.ExecutionCount, step.Goal);
                    }
                }
                else if (stepResult.IsContinueLoop())
                {
                    continueLoop = true;

                    if (this._logger?.IsEnabled(LogLevel.Information) ?? false)
                    {
                        this._logger.LogInformation("Continuing to the next loop iteration for step {StepIndex} with iteration={Iteration}, goal={StepGoal}.", stepIndex, stepState.ExecutionCount, step.Goal);
                    }
                }

                // check if current execution is complete by checking whether all arguments are already provided
                completed = true;
                foreach (var variable in step.Provides)
                {
                    if (!stepResult.Metadata!.ContainsKey(variable))
                    {
                        completed = false;
                    }
                    else
                    {
                        executionState.Variables[variable] = (string)stepResult.Metadata[variable]!;
                        stepState.AddOrUpdateVariable(stepState.ExecutionCount, variable, (string)stepResult.Metadata[variable]!);
                    }
                }

                foreach (var variable in step.Passthrough)
                {
                    if (stepResult.Metadata!.TryGetValue(variable, out object? variableValue))
                    {
                        executionState.Variables[variable] = (string)variableValue!;
                        stepState.AddOrUpdateVariable(stepState.ExecutionCount, variable, (string)variableValue!);

                        // propagate arguments to root context, needed if Flow itself is a step
                        this.PropagateVariable(rootContext, stepResult, variable);
                    }
                }

                // propagate arguments to root context, needed if Flow itself is a step
                foreach (var variable in Constants.ChatPluginVariables.ControlVariables)
                {
                    this.PropagateVariable(rootContext, stepResult, variable);
                }
            }

            if (completed)
            {
                if (this._logger?.IsEnabled(LogLevel.Information) ?? false)
                {
                    this._logger.LogInformation("Completed step {StepIndex} for iteration={Iteration}, goal={StepGoal}.", stepIndex, stepState.ExecutionCount, step.Goal);
                }

                if (step.CompletionType is CompletionType.AtLeastOnce or CompletionType.ZeroOrMore && stepState.Status != ExecutionState.Status.Completed)
                {
                    var nextStepId = $"{stepKey}_{stepState.ExecutionCount + 1}";
                    var repeatStep = continueLoop
                        ? new RepeatOrStartStepResult(true, null)
                        : await this.CheckRepeatStepAsync(rootContext, step, sessionId, nextStepId, input).ConfigureAwait(false);

                    if (repeatStep is null)
                    {
                        // unknown error, try again
                        this._logger?.LogWarning("Unexpected error when checking whether to repeat the step, try again");
                    }
                    else if (repeatStep.Execute is null)
                    {
                        // unconfirmed, prompt user
                        outputs.Add(repeatStep.Prompt!);

                        if (this._logger?.IsEnabled(LogLevel.Information) ?? false)
                        {
                            this._logger.LogInformation("Unclear intention, need follow up to check whether to repeat the step");
                        }

                        await this._flowStatusProvider.SaveExecutionStateAsync(sessionId, executionState).ConfigureAwait(false);
                        break;
                    }
                    else if (repeatStep.Execute.Value)
                    {
                        // need repeat the step again
                        foreach (var variable in step.Provides)
                        {
                            executionState.Variables.Remove(variable);
                        }

                        stepState.ExecutionCount++;
                        await this._flowStatusProvider.SaveExecutionStateAsync(sessionId, executionState).ConfigureAwait(false);

                        if (this._logger?.IsEnabled(LogLevel.Information) ?? false)
                        {
                            this._logger.LogInformation("Need repeat step {StepIndex} for iteration={Iteration}, goal={StepGoal}.", stepIndex, stepState.ExecutionCount, step.Goal);
                        }
                    }
                    else
                    {
                        // completed
                        await this.CompleteStepAsync(rootContext, sessionId, executionState, step, stepState).ConfigureAwait(false);

                        if (this._logger?.IsEnabled(LogLevel.Information) ?? false)
                        {
                            this._logger.LogInformation("Completed step {StepIndex} with iteration={Iteration}, goal={StepGoal}.", stepIndex, stepState.ExecutionCount, step.Goal);
                        }
                    }
                }
                else
                {
                    await this.CompleteStepAsync(rootContext, sessionId, executionState, step, stepState).ConfigureAwait(false);
                }
            }
            else
            {
                await this._flowStatusProvider.SaveExecutionStateAsync(sessionId, executionState).ConfigureAwait(false);
                break;
            }
        }

        if (this._logger?.IsEnabled(LogLevel.Information) ?? false)
        {
            foreach (var output in outputs)
            {
                this._logger?.LogInformation("[Output] {Output}", output);
            }
        }

        return new FunctionResult(this._executeFlowFunction, outputs, metadata: rootContext);
    }

    private void PropagateVariable(KernelArguments rootContext, FunctionResult stepResult, string variableName)
    {
        if (stepResult.Metadata!.ContainsKey(variableName))
        {
            rootContext[variableName] = stepResult.Metadata[variableName];
        }
    }

    private async Task CompleteStepAsync(KernelArguments context, string sessionId, ExecutionState state, FlowStep step, ExecutionState.StepExecutionState stepState)
    {
        stepState.Status = ExecutionState.Status.Completed;
        state.CurrentStepIndex++;

        foreach (var kvp in stepState.Output)
        {
            if (step.CompletionType == CompletionType.Once)
            {
                state.Variables[kvp.Key] = kvp.Value.Single();
            }
            else
            {
                // kvp.Value may contain empty strings when the loop was exited and the arguments the step provides weren't set
                state.Variables[kvp.Key] = JsonSerializer.Serialize(kvp.Value.Where(x => !string.IsNullOrWhiteSpace(x)).ToList());
            }
        }

        foreach (var variable in step.Provides)
        {
            context[variable] = state.Variables[variable];
        }

        await this._flowStatusProvider.SaveExecutionStateAsync(sessionId, state).ConfigureAwait(false);
    }

    private void ValidateStep(FlowStep step, KernelArguments context)
    {
        if (step.Requires.Any(p => !context.ContainsName(p)))
        {
            throw new KernelException($"Step {step.Goal} requires arguments {string.Join(",", step.Requires.Where(p => !context.ContainsName(p)))} that are not provided. ");
        }
    }

    private async Task<RepeatOrStartStepResult?> CheckStartStepAsync(KernelArguments context, FlowStep step, string sessionId, string stepId, string input)
    {
        context = new KernelArguments(context)
        {
            ["goal"] = step.Goal,
            ["message"] = step.StartingMessage
        };
        return await this.CheckRepeatOrStartStepAsync(context, this._checkStartStepFunction, sessionId, $"{stepId}_CheckStartStep", input).ConfigureAwait(false);
    }

    private async Task<RepeatOrStartStepResult?> CheckRepeatStepAsync(KernelArguments context, FlowStep step, string sessionId, string nextStepId, string input)
    {
        context = new KernelArguments(context)
        {
            ["goal"] = step.Goal,
            ["transitionMessage"] = step.TransitionMessage
        };
        return await this.CheckRepeatOrStartStepAsync(context, this._checkRepeatStepFunction, sessionId, $"{nextStepId}_CheckRepeatStep", input).ConfigureAwait(false);
    }

    private async Task<RepeatOrStartStepResult?> CheckRepeatOrStartStepAsync(KernelArguments context, KernelFunction function, string sessionId, string checkRepeatOrStartStepId, string input)
    {
        var chatHistory = await this._flowStatusProvider.GetChatHistoryAsync(sessionId, checkRepeatOrStartStepId).ConfigureAwait(false);
        if (chatHistory is not null)
        {
            chatHistory.AddUserMessage(input);
        }
        else
        {
            chatHistory = [];
        }

        var scratchPad = this.CreateRepeatOrStartStepScratchPad(chatHistory);
        context["agentScratchPad"] = scratchPad;

        if (this._logger.IsEnabled(LogLevel.Information))
        {
            this._logger.LogInformation("Scratchpad: {ScratchPad}", scratchPad);
        }

        var llmResponse = await this._systemKernel.InvokeAsync(function, context).ConfigureAwait(false);

        string llmResponseText = llmResponse.GetValue<string>()?.Trim() ?? string.Empty;

        if (this._logger.IsEnabled(LogLevel.Information))
        {
            this._logger.LogInformation("Response from {Function} : {ActionText}", "CheckRepeatOrStartStep", llmResponseText);
        }

        Match finalAnswerMatch = FinalAnswerRegex().Match(llmResponseText);
        if (finalAnswerMatch.Success)
        {
            string resultString = finalAnswerMatch.Groups[1].Value.Trim();
            if (bool.TryParse(resultString, out bool result))
            {
                await this._flowStatusProvider.SaveChatHistoryAsync(sessionId, checkRepeatOrStartStepId, chatHistory).ConfigureAwait(false);
                return new RepeatOrStartStepResult(result);
            }
        }

        // Extract thought
        Match thoughtMatch = ThoughtRegex().Match(llmResponseText);
        if (thoughtMatch.Success)
        {
            string thoughtString = thoughtMatch.Groups[1].Value.Trim();
            chatHistory.AddSystemMessage(thoughtString);
        }

        Match questionMatch = QuestionRegex().Match(llmResponseText);
        if (questionMatch.Success)
        {
            string prompt = questionMatch.Groups[1].Value.Trim();
            chatHistory.AddAssistantMessage(prompt);
            await this._flowStatusProvider.SaveChatHistoryAsync(sessionId, checkRepeatOrStartStepId, chatHistory).ConfigureAwait(false);

            return new RepeatOrStartStepResult(null, prompt);
        }

        this._logger.LogWarning("Missing result tag from {Function} : {ActionText}", "CheckRepeatOrStartStep", llmResponseText);
        chatHistory.AddSystemMessage(llmResponseText + "\nI should provide either [QUESTION] or [FINAL_ANSWER].");
        await this._flowStatusProvider.SaveChatHistoryAsync(sessionId, checkRepeatOrStartStepId, chatHistory).ConfigureAwait(false);
        return null;
    }

    private string CreateRepeatOrStartStepScratchPad(ChatHistory chatHistory)
    {
        var scratchPadLines = new List<string>();
        foreach (var message in chatHistory)
        {
            if (message.Role == AuthorRole.Assistant)
            {
                scratchPadLines.Add("[QUESTION]");
            }
            else if (message.Role == AuthorRole.User)
            {
                scratchPadLines.Add("[RESPONSE]");
            }
            else if (message.Role == AuthorRole.System)
            {
                scratchPadLines.Add("[THOUGHT]");
            }

            scratchPadLines.Add(message.Content!);
        }

        return string.Join("\n", scratchPadLines).Trim();
    }

    private async Task<FunctionResult> ExecuteStepAsync(FlowStep step, string sessionId, string stepId, string input, Kernel kernel, KernelArguments arguments)
    {
        var stepsTaken = await this._flowStatusProvider.GetReActStepsAsync(sessionId, stepId).ConfigureAwait(false);
        var lastStep = stepsTaken.LastOrDefault();
        if (lastStep is not null)
        {
            lastStep.Observation += $"{AuthorRole.User.Label}: {input}\n";
            await this._flowStatusProvider.SaveReActStepsAsync(sessionId, stepId, stepsTaken).ConfigureAwait(false);
        }

        var question = step.Goal;
        foreach (var variable in step.Requires)
        {
            if (!variable.StartsWith("_", StringComparison.InvariantCulture) && ((string)arguments[variable]!).Length <= this._config.MaxVariableLength)
            {
                question += $"\n - {variable}: {JsonSerializer.Serialize(arguments[variable])}";
            }
        }

        for (int i = stepsTaken.Count; i < this._config.MaxStepIterations; i++)
        {
            var actionStep = await this._reActEngine.GetNextStepAsync(kernel, arguments, question, stepsTaken).ConfigureAwait(false);

            if (actionStep is null)
            {
                this._logger?.LogWarning("Failed to get action step given input=\"{Input}\"", input);
                continue;
            }

            stepsTaken.Add(actionStep);

            if (this._logger?.IsEnabled(LogLevel.Information) ?? false)
            {
                this._logger.LogInformation("Thought: {Thought}", actionStep.Thought);
            }

            if (!string.IsNullOrEmpty(actionStep.FinalAnswer))
            {
                if (step.Provides.Count() == 1)
                {
                    arguments[step.Provides.Single()] = actionStep.FinalAnswer;
                    return new FunctionResult(this._executeStepFunction, actionStep.FinalAnswer, metadata: arguments);
                }
            }
            else if (!string.IsNullOrEmpty(actionStep.Action!))
            {
                if (actionStep.Action!.Contains(Constants.StopAndPromptFunctionName))
                {
                    string prompt = actionStep.ActionVariables![Constants.StopAndPromptParameterName];
                    arguments.TerminateFlow();

                    return new FunctionResult(this._executeStepFunction, prompt, metadata: arguments);
                }

                var actionContextVariables = new KernelArguments();
                foreach (var kvp in arguments)
                {
                    if (step.Requires.Contains(kvp.Key) || step.Passthrough.Contains(kvp.Key))
                    {
                        actionContextVariables[kvp.Key] = kvp.Value;
                    }
                }

                // get chat history
                var chatHistory = await this._flowStatusProvider.GetChatHistoryAsync(sessionId, stepId).ConfigureAwait(false);
                if (chatHistory is null)
                {
                    chatHistory = [];
                }
                else
                {
                    chatHistory.AddUserMessage(input);
                }

                string? actionResult;
                try
                {
                    if (this._config.MinIterationTimeMs > 0)
                    {
                        await Task.Delay(this._config.MinIterationTimeMs).ConfigureAwait(false);
                    }
                    actionResult = await this._reActEngine.InvokeActionAsync(actionStep, input, chatHistory, kernel, actionContextVariables).ConfigureAwait(false);

                    if (string.IsNullOrEmpty(actionResult))
                    {
                        actionStep.Observation = "Got no result from action";
                    }
                    else
                    {
                        actionStep.Observation = $"{AuthorRole.Assistant.Label}: {actionResult}\n";
                        chatHistory.AddAssistantMessage(actionResult);
                        await this._flowStatusProvider.SaveChatHistoryAsync(sessionId, stepId, chatHistory).ConfigureAwait(false);

                        foreach (var passthroughParam in step.Passthrough)
                        {
                            if (actionContextVariables.TryGetValue(passthroughParam, out object? paramValue) && paramValue is string paramStringValue && !string.IsNullOrEmpty(paramStringValue))
                            {
                                arguments[passthroughParam] = actionContextVariables[passthroughParam];
                            }
                        }

                        foreach (var providedParam in step.Provides)
                        {
                            if (actionContextVariables.TryGetValue(providedParam, out object? paramValue) && paramValue is string paramStringValue && !string.IsNullOrEmpty(paramStringValue))
                            {
                                arguments[providedParam] = actionContextVariables[providedParam];
                            }
                        }

                        foreach (var variable in Constants.ChatPluginVariables.ControlVariables)
                        {
                            if (actionContextVariables.TryGetValue(variable, out object? variableValue))
                            {
                                arguments[variable] = variableValue;
                            }
                        }
                    }
                }
                catch (MissingMethodException ex)
                {
                    actionStep.Observation = $"Error invoking action {actionStep.Action} : {ex.Message}. " +
                                             "Use only the available functions listed in the [AVAILABLE FUNCTIONS] section. " +
                                             "Do not attempt to use any other functions that are not specified.\n";

                    continue;
                }
                catch (Exception ex) when (!ex.IsNonRetryable())
                {
                    actionStep.Observation = $"Error invoking action {actionStep.Action} : {ex.Message}";
                    this._logger?.LogWarning(ex, "Error invoking action {Action}", actionStep.Action);

                    continue;
                }

                if (this._logger?.IsEnabled(LogLevel.Information) ?? false)
                {
                    this._logger.LogInformation("Observation: {Observation}", actionStep.Observation);
                }

                await this._flowStatusProvider.SaveReActStepsAsync(sessionId, stepId, stepsTaken).ConfigureAwait(false);

                if (!string.IsNullOrEmpty(actionResult))
                {
                    if (arguments.IsTerminateFlow())
                    {
                        // Terminate the flow without another round of reasoning, to save the LLM reasoning calls.
                        // This is not suggested unless plugin has performance requirement and has explicitly set the control variable.
                        return new FunctionResult(this._executeStepFunction, actionResult, metadata: arguments);
                    }

                    foreach (var variable in Constants.ChatPluginVariables.ControlVariables)
                    {
                        if (arguments.ContainsName(variable))
                        {
                            // redirect control to client
                            return new FunctionResult(this._executeStepFunction, actionResult, metadata: arguments);
                        }
                    }

                    if (!step.Provides.Except(arguments.Where(v => !string.IsNullOrEmpty((string)v.Value!)).Select(_ => _.Key)).Any())
                    {
                        // step is complete
                        return new FunctionResult(this._executeStepFunction, actionResult, metadata: arguments);
                    }

                    // continue to next iteration
                    continue;
                }

                this._logger?.LogWarning("Action: No result from action");
            }
            else
            {
                actionStep.Observation = "ACTION $JSON_BLOB must be provided as part of thought process.";
                this._logger?.LogWarning("Action: No action to take");
            }

            if (this._config.MinIterationTimeMs > 0)
            {
                // continue to next iteration
                await Task.Delay(this._config.MinIterationTimeMs).ConfigureAwait(false);
            }
        }

        throw new KernelException($"Failed to complete step {stepId} for session {sessionId}.");
    }

    private sealed class RepeatOrStartStepResult(bool? execute, string? prompt = null)
    {
        public bool? Execute { get; } = execute;

        public string? Prompt { get; } = prompt;
    }
}
