// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0130 // Namespace does not match folder structure
// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticKernel.Planning.Flow;
#pragma warning restore IDE0130 // Namespace does not match folder structure

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SemanticFunctions;
using Microsoft.SemanticKernel.SkillDefinition;

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
    private readonly KernelBuilder _kernelBuilder;

    /// <summary>
    /// The logger
    /// </summary>
    private readonly ILogger _logger;

    /// <summary>
    /// The global skill collection
    /// </summary>
    private readonly Dictionary<object, string?> _globalSkillCollection;

    /// <summary>
    /// The flow planner config
    /// </summary>
    private readonly FlowPlannerConfig _config;

    /// <summary>
    /// The flow status provider
    /// </summary>
    private readonly IFlowStatusProvider _flowStatusProvider;

    /// <summary>
    /// System kernel for flow execution
    /// </summary>
    private readonly IKernel _systemKernel;

    /// <summary>
    /// Re-Act engine for flow execution
    /// </summary>
    private readonly ReActEngine _reActEngine;

    /// <summary>
    /// Restricted skill name
    /// </summary>
    private const string RestrictedSkillName = "FlowExecutor_Excluded";

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
    private readonly ISKFunction _checkRepeatStepFunction;

    internal FlowExecutor(KernelBuilder kernelBuilder, IFlowStatusProvider statusProvider, Dictionary<object, string?> globalSkillCollection, FlowPlannerConfig? config = null)
    {
        this._kernelBuilder = kernelBuilder;
        this._systemKernel = kernelBuilder.Build();

        this._logger = this._systemKernel.LoggerFactory.CreateLogger(nameof(FlowExecutor));
        this._config = config ?? new FlowPlannerConfig();

        this._flowStatusProvider = statusProvider;
        this._globalSkillCollection = globalSkillCollection;

        string checkRepeatStepPrompt = EmbeddedResource.Read("Skills.CheckRepeatStep.skprompt.txt");
        var checkRepeatStepConfig = PromptTemplateConfig.FromJson(EmbeddedResource.Read("Skills.CheckRepeatStep.config.json"));
        this._checkRepeatStepFunction = this.ImportSemanticFunction(this._systemKernel, "CheckRepeatStep", checkRepeatStepPrompt, checkRepeatStepConfig);

        this._config.ExcludedSkills.Add(RestrictedSkillName);
        this._reActEngine = new ReActEngine(this._systemKernel, this._logger, this._config);
    }

    public async Task<SKContext> ExecuteAsync(Flow flow, string sessionId, string input, ContextVariables contextVariables)
    {
        Verify.NotNull(flow, nameof(flow));

        this._logger?.BeginScope(nameof(FlowExecutor));
        this._logger?.LogInformation("Executing flow {FlowName} with sessionId={SessionId}.", flow.Name, sessionId);
        var sortedSteps = flow.SortSteps();

        SKContext rootContext = this._systemKernel.CreateNewContext();
        // populate context variables from upstream
        rootContext.Variables.Update(contextVariables);

        // populate persisted state variables
        ExecutionState executionState = await this._flowStatusProvider.GetExecutionStateAsync(sessionId).ConfigureAwait(false);
        List<string> outputs = new();

        while (executionState.CurrentStepIndex < sortedSteps.Count)
        {
            int stepIndex = executionState.CurrentStepIndex;
            FlowStep step = sortedSteps[stepIndex];

            foreach (var kv in executionState.Variables)
            {
                rootContext.Variables.Set(kv.Key, kv.Value);
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

            bool completed = step.Provides.All(_ => executionState.Variables.ContainsKey(_));
            if (!completed)
            {
                // execute step
                this._logger?.LogInformation(
                    "Executing step {StepIndex} for iteration={Iteration}, goal={StepGoal}, input={Input}.", stepIndex,
                    stepState.ExecutionCount, step.Goal, input);

                IKernel stepKernel = this._kernelBuilder.Build();
                var stepSkills = step.GetSKills(stepKernel, this._globalSkillCollection);
                foreach (var skill in stepSkills)
                {
                    stepKernel.ImportSkill(skill);
                }

                var stepContext = stepKernel.CreateNewContext();
                foreach (var key in step.Requires)
                {
                    stepContext.Variables.Set(key, rootContext.Variables[key]);
                }

                var stepResult = await this.ExecuteStepAsync(step, sessionId, stepId, input, stepKernel, stepContext)
                    .ConfigureAwait(false);
                if (!string.IsNullOrEmpty(stepResult.Result) &&
                    stepResult.Variables.ContainsKey(Constants.ChatSkillVariables.PromptInputName))
                {
                    outputs.Add(stepResult.Result);
                }

                // check if current execution is complete by checking whether all variables are already provided
                completed = true;
                foreach (var variable in step.Provides)
                {
                    if (!stepResult.Variables.ContainsKey(variable))
                    {
                        completed = false;
                    }
                    else
                    {
                        executionState.Variables[variable] = stepResult.Variables[variable];
                        stepState.AddOrUpdateVariable(stepState.ExecutionCount, variable,
                            stepResult.Variables[variable]);
                    }
                }
            }

            if (completed)
            {
                this._logger?.LogInformation("Completed step {StepIndex} for iteration={Iteration}, goal={StepGoal}.", stepIndex, stepState.ExecutionCount, step.Goal);

                if (step.CompletionType == CompletionType.AtLeastOnce && stepState.Status != ExecutionState.Status.Completed)
                {
                    var nextStepId = $"{stepKey}_{stepState.ExecutionCount + 1}";
                    RepeatStepResult? repeatStep = await this.CheckRepeatStepAsync(rootContext, step, sessionId, nextStepId, input).ConfigureAwait(false);
                    if (repeatStep == null)
                    {
                        // unknown error, try again
                        this._logger?.LogWarning("Unexpected error when checking whether to repeat the step, try again");
                    }
                    else if (repeatStep.Repeat == null)
                    {
                        // unconfirmed, prompt user
                        outputs.Add(repeatStep.Prompt!);
                        await this._flowStatusProvider.SaveExecutionStateAsync(sessionId, executionState).ConfigureAwait(false);
                        break;
                    }
                    else if (repeatStep.Repeat.Value)
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
                        await this.CompleteStep(rootContext, sessionId, executionState, step, stepState).ConfigureAwait(false);
                        this._logger?.LogInformation("Completed step {StepIndex} with iteration={Iteration}, goal={StepGoal}.", stepIndex, stepState.ExecutionCount, step.Goal);
                    }
                }
                else
                {
                    await this.CompleteStep(rootContext, sessionId, executionState, step, stepState).ConfigureAwait(false);
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

        rootContext.Variables.Update(JsonSerializer.Serialize(outputs));
        return rootContext;
    }

    private async Task CompleteStep(SKContext context, string sessionId, ExecutionState state, FlowStep step, ExecutionState.StepExecutionState stepState)
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
                state.Variables[kvp.Key] = JsonSerializer.Serialize(kvp.Value);
            }
        }

        foreach (var variable in step.Provides)
        {
            context.Variables[variable] = state.Variables[variable];
        }

        await this._flowStatusProvider.SaveExecutionStateAsync(sessionId, state).ConfigureAwait(false);
    }

    private void ValidateStep(FlowStep step, SKContext context)
    {
        if (step is Flow)
        {
            throw new SKException("Recursive flow is not supported yet.");
        }

        if (step.Requires.Any(p => !context.Variables.ContainsKey(p)))
        {
            throw new SKException($"Step {step.Goal} requires variables that are not provided. ");
        }
    }

    private async Task<RepeatStepResult?> CheckRepeatStepAsync(SKContext context, FlowStep step, string sessionId, string nextStepId, string input)
    {
        context = context.Clone();
        context.Variables.Set("goal", step.Goal);
        var checkRepeatStepId = $"{nextStepId}_CheckRepeatStep";
        var chatHistory = await this._flowStatusProvider.GetChatHistoryAsync(sessionId, checkRepeatStepId).ConfigureAwait(false);
        if (chatHistory != null)
        {
            chatHistory.AddUserMessage(input);
        }
        else
        {
            chatHistory = new ChatHistory();
        }

        var scratchPad = this.CreateRepeatStepScratchPad(chatHistory);
        context.Variables.Set("agentScratchPad", scratchPad);
        this._logger?.LogInformation("Scratchpad: {ScratchPad}", scratchPad);

        var llmResponse = await this._checkRepeatStepFunction.InvokeAsync(context).ConfigureAwait(false);
        if (llmResponse.ErrorOccurred)
        {
            string message = $"Error occurred while executing action step: {llmResponse.LastException?.Message}";
            throw new SKException(message, llmResponse.LastException);
        }

        string llmResponseText = llmResponse.Result.Trim();
        this._logger?.LogInformation("Response from {Function} : {ActionText}", "CheckRepeatStep", llmResponseText);

        Match finalAnswerMatch = s_finalAnswerRegex.Match(llmResponseText);
        if (finalAnswerMatch.Success)
        {
            string resultString = finalAnswerMatch.Groups[1].Value.Trim();
            if (bool.TryParse(resultString, out bool result))
            {
                await this._flowStatusProvider.SaveChatHistoryAsync(sessionId, checkRepeatStepId, chatHistory).ConfigureAwait(false);
                return new RepeatStepResult(result);
            }
        }

        // Extract thought
        Match thoughtMatch = s_thoughtRegex.Match(input);
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
            await this._flowStatusProvider.SaveChatHistoryAsync(sessionId, checkRepeatStepId, chatHistory).ConfigureAwait(false);

            return new RepeatStepResult(null, prompt);
        }

        await this._flowStatusProvider.SaveChatHistoryAsync(sessionId, checkRepeatStepId, chatHistory).ConfigureAwait(false);
        return null;
    }

    private string CreateRepeatStepScratchPad(ChatHistory chatHistory)
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

    private async Task<SKContext> ExecuteStepAsync(FlowStep step, string sessionId, string stepId, string input, IKernel kernel, SKContext context)
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
            if (!variable.StartsWith("_", StringComparison.InvariantCulture) && context.Variables[variable].Length <= this._config.MaxVariableLength)
            {
                question += $"\n - {variable}: {JsonSerializer.Serialize(context.Variables[variable])}";
            }
        }

        for (int i = stepsTaken.Count; i < this._config.MaxStepIterations; i++)
        {
            var actionStep = await this._reActEngine.GetNextStepAsync(context, question, stepsTaken).ConfigureAwait(false);

            if (actionStep == null)
            {
                this._logger?.LogWarning("Failed to get action step given input=\"{Input}\"", input);
                continue;
            }

            stepsTaken.Add(actionStep);

            this._logger?.LogInformation("Thought: {Thought}", actionStep.Thought);
            if (!string.IsNullOrEmpty(actionStep.Action!))
            {
                var actionContext = kernel.CreateNewContext();
                context.Variables.Where(p => step.Requires.Contains(p.Key)).ToList().ForEach(p => actionContext.Variables[p.Key] = p.Value);
                // get chat history
                var chatHistory = await this._flowStatusProvider.GetChatHistoryAsync(sessionId, stepId).ConfigureAwait(false);
                if (chatHistory == null)
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
                    var result = await this._reActEngine.InvokeActionAsync(actionStep, input, chatHistory, kernel, actionContext).ConfigureAwait(false);

                    if (string.IsNullOrEmpty(result))
                    {
                        actionStep.Observation = "Got no result from action";
                    }
                    else
                    {
                        actionStep.Observation = $"{AuthorRole.Assistant.Label}: {result}\n";
                        context.Variables.Update(result);
                        chatHistory.AddAssistantMessage(result);
                        await this._flowStatusProvider.SaveChatHistoryAsync(sessionId, stepId, chatHistory).ConfigureAwait(false);

                        foreach (var providedParam in step.Provides)
                        {
                            if (actionContext.Variables.TryGetValue(providedParam, out string? paramValue) && !string.IsNullOrEmpty(paramValue))
                            {
                                context.Variables.Set(providedParam, actionContext.Variables[providedParam]);
                            }
                        }

                        if (actionContext.Variables.ContainsKey(Constants.ChatSkillVariables.PromptInputName))
                        {
                            context.Variables.Set(Constants.ChatSkillVariables.PromptInputName, actionContext.Variables[Constants.ChatSkillVariables.PromptInputName]);
                        }
                    }
                }
                catch (MissingMethodException ex)
                {
                    actionStep.Observation = $"Error invoking action {actionStep.Action} : {ex.Message}. " +
                                             "Use only the available functions listed in the [AVAILABLE FUNCTIONS] section. " +
                                             "Do not attempt to use any other functions that are not specified.\r\n" +
                                             "The value of parameters should either by empty when missing information, or derived from the agent scratchpad.\r\n" +
                                             "You are not allowed to ask user directly for more information.";

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

                if (!string.IsNullOrEmpty(context.Result))
                {
                    if (context.Variables.ContainsKey(Constants.ChatSkillVariables.PromptInputName))
                    {
                        // redirect control to client if new input is required
                        return context;
                    }
                    else if (!step.Provides.Except(context.Variables.Where(v => !string.IsNullOrEmpty(v.Value)).Select(_ => _.Key)).Any())
                    {
                        // step is complete
                        return context;
                    }

                    // continue to next iteration
                    continue;
                }

                this._logger?.LogInformation("Action: No result from action");
            }
            else if (!string.IsNullOrEmpty(actionStep.FinalAnswer))
            {
                if (step.Provides.Count == 1)
                {
                    context.Variables.Set(step.Provides.Single(), actionStep.FinalAnswer);
                    return context;
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

        throw new SKException($"Failed to complete step {stepId} for session {sessionId}.");
    }

    private ISKFunction ImportSemanticFunction(IKernel kernel, string functionName, string promptTemplate, PromptTemplateConfig config)
    {
        var template = new PromptTemplate(promptTemplate, config, kernel.PromptTemplateEngine);
        var functionConfig = new SemanticFunctionConfig(config, template);

        return kernel.RegisterSemanticFunction(RestrictedSkillName, functionName, functionConfig);
    }

    private class RepeatStepResult
    {
        public RepeatStepResult(bool? repeat, string? prompt = null)
        {
            this.Prompt = prompt;
            this.Repeat = repeat;
        }

        public bool? Repeat { get; }

        public string? Prompt { get; }
    }
}
