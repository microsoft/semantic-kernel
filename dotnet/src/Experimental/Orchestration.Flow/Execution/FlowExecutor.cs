// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Experimental.Orchestration.Abstractions;

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
internal class FlowExecutor : IFlowExecutor
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
    private static readonly Regex s_finalAnswerRegex =
        new(@"\[FINAL.+\](?<final_answer>.+)", RegexOptions.Singleline);

    /// <summary>
    /// The regex for parsing the question
    /// </summary>
    private static readonly Regex s_questionRegex =
        new(@"\[QUESTION\](?<question>.+)", RegexOptions.Singleline);

    /// <summary>
    /// The regex for parsing the thought response
    /// </summary>
    private static readonly Regex s_thoughtRegex =
        new(@"\[THOUGHT\](?<thought>.+)", RegexOptions.Singleline);

    /// <summary>
    /// Check repeat step function
    /// </summary>
    private readonly KernelFunction _checkRepeatStepFunction;

    /// <summary>
    /// Check start step function
    /// </summary>
    private readonly KernelFunction _checkStartStepFunction;

    internal FlowExecutor(IKernelBuilder kernelBuilder, IFlowStatusProvider statusProvider, Dictionary<object, string?> globalPluginCollection, FlowOrchestratorConfig? config = null)
    {
        this._kernelBuilder = kernelBuilder;
        this._systemKernel = kernelBuilder.Build();

        this._logger = this._systemKernel.LoggerFactory.CreateLogger(typeof(FlowExecutor));
        this._config = config ?? new FlowOrchestratorConfig();

        this._flowStatusProvider = statusProvider;
        this._globalPluginCollection = globalPluginCollection;

        var checkRepeatStepPrompt = EmbeddedResource.Read("Plugins.CheckRepeatStep.skprompt.txt")!;
        var checkRepeatStepConfig = PromptTemplateConfig.FromJson(EmbeddedResource.Read("Plugins.CheckRepeatStep.config.json")!);
        this._checkRepeatStepFunction = CreateSemanticFunction(this._systemKernel, "CheckRepeatStep", checkRepeatStepPrompt, checkRepeatStepConfig);

        var checkStartStepPrompt = EmbeddedResource.Read("Plugins.CheckStartStep.skprompt.txt")!;
        var checkStartStepConfig = PromptTemplateConfig.FromJson(EmbeddedResource.Read("Plugins.CheckStartStep.config.json")!);
        this._checkStartStepFunction = CreateSemanticFunction(this._systemKernel, "CheckStartStep", checkStartStepPrompt, checkStartStepConfig);

        this._systemKernel.Plugins.Add(new KernelPlugin(RestrictedPluginName, new[]
        {
            this._checkRepeatStepFunction,
            this._checkStartStepFunction,
        }));

        this._config.ExcludedPlugins.Add(RestrictedPluginName);
        this._reActEngine = new ReActEngine(this._systemKernel, this._logger, this._config);
    }

    public async Task<ContextVariables> ExecuteAsync(Flow flow, string sessionId, string input, ContextVariables contextVariables)
    {
        Verify.NotNull(flow, nameof(flow));

        this._logger?.LogInformation("Executing flow {FlowName} with sessionId={SessionId}.", flow.Name, sessionId);
        var sortedSteps = flow.SortSteps();

        var rootContext = contextVariables.Clone();

        // populate persisted state variables
        ExecutionState executionState = await this._flowStatusProvider.GetExecutionStateAsync(sessionId).ConfigureAwait(false);
        List<string> outputs = new();

        while (executionState.CurrentStepIndex < sortedSteps.Count)
        {
            int stepIndex = executionState.CurrentStepIndex;
            FlowStep step = sortedSteps[stepIndex];

            foreach (var kv in executionState.Variables)
            {
                rootContext.Set(kv.Key, kv.Value);
            }

            this.ValidateStep(step, rootContext);

            // init step execution state
            string stepKey = $"{stepIndex}_{step.Goal}";
            if (!executionState.StepStates.ContainsKey(stepKey))
            {
                executionState.StepStates.Add(stepKey, new ExecutionState.StepExecutionState());
            }

            ExecutionState.StepExecutionState stepState = executionState.StepStates[stepKey];
            var stepId = $"{stepKey}_{stepState.ExecutionCount}";

            var continueLoop = false;
            var completed = step.Provides.All(_ => executionState.Variables.ContainsKey(_));
            if (!completed)
            {
                // On the first iteration of an Optional or ZeroOrMore step, we need to check whether the user wants to start the stepstep
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
                        this._logger?.LogInformation("Need to start step {StepIndex} for iteration={Iteration}, goal={StepGoal}.", stepIndex, stepState.ExecutionCount, step.Goal);
                    }
                    else
                    {
                        // User doesn't want to run the step
                        foreach (var variable in step.Provides)
                        {
                            executionState.Variables[variable] = "[]";
                        }

                        await this.CompleteStepAsync(rootContext, sessionId, executionState, step, stepState).ConfigureAwait(false);
                        this._logger?.LogInformation("Completed step {StepIndex} with iteration={Iteration}, goal={StepGoal}.", stepIndex, stepState.ExecutionCount, step.Goal);
                        continue;
                    }
                }

                // execute step
                this._logger?.LogInformation(
                    "Executing step {StepIndex} for iteration={Iteration}, goal={StepGoal}, input={Input}.", stepIndex,
                    stepState.ExecutionCount, step.Goal, input);

                Kernel stepKernel = this._kernelBuilder.Build();
                var stepVariables = new ContextVariables();
                foreach (var key in step.Requires)
                {
                    stepVariables.Set(key, rootContext[key]);
                }

                foreach (var key in step.Passthrough)
                {
                    if (rootContext.TryGetValue(key, out var val))
                    {
                        stepVariables.Set(key, val);
                    }
                }

                ContextVariables? stepResult;
                if (step is Flow flowStep)
                {
                    stepResult = await this.ExecuteAsync(flowStep, $"{sessionId}_{stepId}", input, stepVariables).ConfigureAwait(false);
                }
                else
                {
                    var stepPlugins = step.LoadPlugins(stepKernel, this._globalPluginCollection);
                    foreach (var plugin in stepPlugins)
                    {
                        stepKernel.ImportPluginFromObject(plugin, plugin.GetType().Name);
                    }

                    stepResult = await this.ExecuteStepAsync(step, sessionId, stepId, input, stepKernel, stepVariables).ConfigureAwait(false);
                }

                if (!string.IsNullOrEmpty(stepResult.ToString()) && (stepResult.IsPromptInput() || stepResult.IsTerminateFlow()))
                {
                    try
                    {
                        var stepOutputs = JsonSerializer.Deserialize<string[]>(stepResult.ToString());
                        outputs.AddRange(stepOutputs!);
                    }
                    catch (JsonException)
                    {
                        outputs.Add(stepResult.ToString());
                    }
                }
                else if (stepResult.TryGetValue(Constants.ChatPluginVariables.ExitLoopName, out var exitResponse))
                {
                    stepState.Status = ExecutionState.Status.Completed;
                    foreach (var variable in step.Provides)
                    {
                        if (!stepResult.ContainsKey(variable))
                        {
                            stepResult[variable] = string.Empty;
                        }
                    }

                    if (!string.IsNullOrWhiteSpace(exitResponse))
                    {
                        outputs.Add(exitResponse);
                    }

                    this._logger?.LogInformation("Exiting loop for step {StepIndex} with iteration={Iteration}, goal={StepGoal}.", stepIndex, stepState.ExecutionCount, step.Goal);
                }
                else if (stepResult.IsContinueLoop())
                {
                    continueLoop = true;
                    this._logger?.LogInformation("Continuing to the next loop iteration for step {StepIndex} with iteration={Iteration}, goal={StepGoal}.", stepIndex, stepState.ExecutionCount, step.Goal);
                }

                // check if current execution is complete by checking whether all variables are already provided
                completed = true;
                foreach (var variable in step.Provides)
                {
                    if (!stepResult.ContainsKey(variable))
                    {
                        completed = false;
                    }
                    else
                    {
                        executionState.Variables[variable] = stepResult[variable];
                        stepState.AddOrUpdateVariable(stepState.ExecutionCount, variable,
                            stepResult[variable]);
                    }
                }

                foreach (var variable in step.Passthrough)
                {
                    if (stepResult.ContainsKey(variable))
                    {
                        executionState.Variables[variable] = stepResult[variable];
                        stepState.AddOrUpdateVariable(stepState.ExecutionCount, variable,
                            stepResult[variable]);

                        // propagate variables to root context, needed if Flow itself is a step
                        this.PropagateVariable(rootContext, stepResult, variable);
                    }
                }

                // propagate variables to root context, needed if Flow itself is a step
                foreach (var variable in Constants.ChatPluginVariables.ControlVariables)
                {
                    this.PropagateVariable(rootContext, stepResult, variable);
                }
            }

            if (completed)
            {
                this._logger?.LogInformation("Completed step {StepIndex} for iteration={Iteration}, goal={StepGoal}.", stepIndex, stepState.ExecutionCount, step.Goal);

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
                        this._logger?.LogInformation("Unclear intention, need follow up to check whether to repeat the step");
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
                        this._logger?.LogInformation("Need repeat step {StepIndex} for iteration={Iteration}, goal={StepGoal}.", stepIndex, stepState.ExecutionCount, step.Goal);
                    }
                    else
                    {
                        // completed
                        await this.CompleteStepAsync(rootContext, sessionId, executionState, step, stepState).ConfigureAwait(false);
                        this._logger?.LogInformation("Completed step {StepIndex} with iteration={Iteration}, goal={StepGoal}.", stepIndex, stepState.ExecutionCount, step.Goal);
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

        foreach (var output in outputs)
        {
            this._logger?.LogInformation("[Output] {Output}", output);
        }

        rootContext.Update(JsonSerializer.Serialize(outputs));

        return rootContext;
    }

    private void PropagateVariable(ContextVariables rootContext, ContextVariables stepResult, string variableName)
    {
        if (stepResult.ContainsKey(variableName))
        {
            rootContext[variableName] = stepResult[variableName];
        }
    }

    private async Task CompleteStepAsync(ContextVariables context, string sessionId, ExecutionState state, FlowStep step, ExecutionState.StepExecutionState stepState)
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
                // kvp.Value may contain empty strings when the loop was exited and the variables the step provides weren't set
                state.Variables[kvp.Key] = JsonSerializer.Serialize(kvp.Value.Where(x => !string.IsNullOrWhiteSpace(x)).ToList());
            }
        }

        foreach (var variable in step.Provides)
        {
            context[variable] = state.Variables[variable];
        }

        await this._flowStatusProvider.SaveExecutionStateAsync(sessionId, state).ConfigureAwait(false);
    }

    private void ValidateStep(FlowStep step, ContextVariables context)
    {
        if (step.Requires.Any(p => !context.ContainsKey(p)))
        {
            throw new KernelException($"Step {step.Goal} requires variables {string.Join(",", step.Requires.Where(p => !context.ContainsKey(p)))} that are not provided. ");
        }
    }

    private async Task<RepeatOrStartStepResult?> CheckStartStepAsync(ContextVariables context, FlowStep step, string sessionId, string stepId, string input)
    {
        context = context.Clone();
        context.Set("goal", step.Goal);
        context.Set("message", step.StartingMessage);
        return await this.CheckRepeatOrStartStepAsync(context, this._checkStartStepFunction, sessionId, $"{stepId}_CheckStartStep", input).ConfigureAwait(false);
    }

    private async Task<RepeatOrStartStepResult?> CheckRepeatStepAsync(ContextVariables context, FlowStep step, string sessionId, string nextStepId, string input)
    {
        context = context.Clone();
        context.Set("goal", step.Goal);
        context.Set("transitionMessage", step.TransitionMessage);
        return await this.CheckRepeatOrStartStepAsync(context, this._checkRepeatStepFunction, sessionId, $"{nextStepId}_CheckRepeatStep", input).ConfigureAwait(false);
    }

    private async Task<RepeatOrStartStepResult?> CheckRepeatOrStartStepAsync(ContextVariables context, KernelFunction function, string sessionId, string checkRepeatOrStartStepId, string input)
    {
        var chatHistory = await this._flowStatusProvider.GetChatHistoryAsync(sessionId, checkRepeatOrStartStepId).ConfigureAwait(false);
        if (chatHistory != null)
        {
            chatHistory.AddUserMessage(input);
        }
        else
        {
            chatHistory = new ChatHistory();
        }

        var scratchPad = this.CreateRepeatOrStartStepScratchPad(chatHistory);
        context.Set("agentScratchPad", scratchPad);
        this._logger?.LogInformation("Scratchpad: {ScratchPad}", scratchPad);

        var llmResponse = await this._systemKernel.InvokeAsync(function, context).ConfigureAwait(false);

        string llmResponseText = llmResponse.GetValue<string>()?.Trim() ?? string.Empty;
        this._logger?.LogInformation("Response from {Function} : {ActionText}", "CheckRepeatOrStartStep", llmResponseText);

        Match finalAnswerMatch = s_finalAnswerRegex.Match(llmResponseText);
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
        Match thoughtMatch = s_thoughtRegex.Match(llmResponseText);
        if (thoughtMatch.Success)
        {
            string thoughtString = thoughtMatch.Groups[1].Value.Trim();
            chatHistory.AddSystemMessage(thoughtString);
        }

        Match questionMatch = s_questionRegex.Match(llmResponseText);
        if (questionMatch.Success)
        {
            string prompt = questionMatch.Groups[1].Value.Trim();
            chatHistory.AddAssistantMessage(prompt);
            await this._flowStatusProvider.SaveChatHistoryAsync(sessionId, checkRepeatOrStartStepId, chatHistory).ConfigureAwait(false);

            return new RepeatOrStartStepResult(null, prompt);
        }

        this._logger?.LogWarning("Missing result tag from {Function} : {ActionText}", "CheckRepeatOrStartStep", llmResponseText);
        chatHistory.AddSystemMessage(llmResponseText + "\nI should provide either [QUESTION] or [FINAL_ANSWER]");
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

            scratchPadLines.Add(message.Content);
        }

        return string.Join("\n", scratchPadLines).Trim();
    }

    private async Task<ContextVariables> ExecuteStepAsync(FlowStep step, string sessionId, string stepId, string input, Kernel kernel, ContextVariables variables)
    {
        var stepsTaken = await this._flowStatusProvider.GetReActStepsAsync(sessionId, stepId).ConfigureAwait(false);
        var lastStep = stepsTaken.LastOrDefault();
        if (lastStep != null)
        {
            lastStep.Observation += $"{AuthorRole.User.Label}: {input}\n";
            await this._flowStatusProvider.SaveReActStepsAsync(sessionId, stepId, stepsTaken).ConfigureAwait(false);
        }

        var question = step.Goal;
        foreach (var variable in step.Requires)
        {
            if (!variable.StartsWith("_", StringComparison.InvariantCulture) && variables[variable].Length <= this._config.MaxVariableLength)
            {
                question += $"\n - {variable}: {JsonSerializer.Serialize(variables[variable])}";
            }
        }

        for (int i = stepsTaken.Count; i < this._config.MaxStepIterations; i++)
        {
            var actionStep = await this._reActEngine.GetNextStepAsync(kernel, variables, question, stepsTaken).ConfigureAwait(false);

            if (actionStep is null)
            {
                this._logger?.LogWarning("Failed to get action step given input=\"{Input}\"", input);
                continue;
            }

            stepsTaken.Add(actionStep);

            this._logger?.LogInformation("Thought: {Thought}", actionStep.Thought);
            if (!string.IsNullOrEmpty(actionStep.Action!))
            {
                if (actionStep.Action!.Contains(Constants.StopAndPromptFunctionName))
                {
                    string prompt = actionStep.ActionVariables![Constants.StopAndPromptParameterName];
                    variables.Update(prompt);
                    variables.TerminateFlow();

                    return variables;
                }

                var actionContextVariables = new ContextVariables();
                foreach (var kvp in variables)
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
                    chatHistory = new ChatHistory();
                }
                else
                {
                    chatHistory.AddUserMessage(input);
                }

                try
                {
                    await Task.Delay(this._config.MinIterationTimeMs).ConfigureAwait(false);
                    var result = await this._reActEngine.InvokeActionAsync(actionStep, input, chatHistory, kernel, actionContextVariables).ConfigureAwait(false);

                    if (string.IsNullOrEmpty(result))
                    {
                        actionStep.Observation = "Got no result from action";
                    }
                    else
                    {
                        actionStep.Observation = $"{AuthorRole.Assistant.Label}: {result}\n";
                        variables.Update(result);
                        chatHistory.AddAssistantMessage(result);
                        await this._flowStatusProvider.SaveChatHistoryAsync(sessionId, stepId, chatHistory).ConfigureAwait(false);

                        foreach (var passthroughParam in step.Passthrough)
                        {
                            if (actionContextVariables.TryGetValue(passthroughParam, out string? paramValue) && !string.IsNullOrEmpty(paramValue))
                            {
                                variables.Set(passthroughParam, actionContextVariables[passthroughParam]);
                            }
                        }

                        foreach (var providedParam in step.Provides)
                        {
                            if (actionContextVariables.TryGetValue(providedParam, out string? paramValue) && !string.IsNullOrEmpty(paramValue))
                            {
                                variables.Set(providedParam, actionContextVariables[providedParam]);
                            }
                        }

                        foreach (var variable in Constants.ChatPluginVariables.ControlVariables)
                        {
                            if (actionContextVariables.TryGetValue(variable, out string? variableValue))
                            {
                                variables.Set(variable, variableValue);
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
                catch (Exception ex) when (!ex.IsCriticalException())
                {
                    actionStep.Observation = $"Error invoking action {actionStep.Action} : {ex.Message}";
                    this._logger?.LogWarning(ex, "Error invoking action {Action}", actionStep.Action);

                    continue;
                }

                this._logger?.LogInformation("Observation: {Observation}", actionStep.Observation);
                await this._flowStatusProvider.SaveReActStepsAsync(sessionId, stepId, stepsTaken).ConfigureAwait(false);

                if (!string.IsNullOrEmpty(variables.Input))
                {
                    if (variables.IsTerminateFlow())
                    {
                        // Terminate the flow without another round of reasoning, to save the LLM reasoning calls.
                        // This is not suggested unless plugin has performance requirement and has explicitly set the control variable.
                        return variables;
                    }

                    foreach (var variable in Constants.ChatPluginVariables.ControlVariables)
                    {
                        if (variables.ContainsKey(variable))
                        {
                            // redirect control to client
                            return variables;
                        }
                    }

                    if (!step.Provides.Except(variables.Where(v => !string.IsNullOrEmpty(v.Value)).Select(_ => _.Key)).Any())
                    {
                        // step is complete
                        return variables;
                    }

                    // continue to next iteration
                    continue;
                }

                this._logger?.LogInformation("Action: No result from action");
            }
            else if (!string.IsNullOrEmpty(actionStep.FinalAnswer))
            {
                if (step.Provides.Count() == 1)
                {
                    variables.Set(step.Provides.Single(), actionStep.FinalAnswer);
                    return variables;
                }
            }
            else
            {
                actionStep.Observation = "ACTION $JSON_BLOB must be provided as part of thought process.";
                this._logger?.LogInformation("Action: No action to take");
            }

            // continue to next iteration
            await Task.Delay(this._config.MinIterationTimeMs).ConfigureAwait(false);
        }

        throw new KernelException($"Failed to complete step {stepId} for session {sessionId}.");
    }

    private static KernelFunction CreateSemanticFunction(Kernel kernel, string functionName, string promptTemplate, PromptTemplateConfig config)
    {
        var factory = new KernelPromptTemplateFactory(kernel.LoggerFactory);
        var template = factory.Create(promptTemplate, config);
        return kernel.CreateFunctionFromPrompt(template, config, functionName);
    }

    private class RepeatOrStartStepResult
    {
        public RepeatOrStartStepResult(bool? execute, string? prompt = null)
        {
            this.Prompt = prompt;
            this.Execute = execute;
        }

        public bool? Execute { get; }

        public string? Prompt { get; }
    }
}
