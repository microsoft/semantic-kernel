// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0130 // Namespace does not match folder structure
// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticKernel.Planning.Flow;
#pragma warning restore IDE0130 // Namespace does not match folder structure

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;

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

    internal FlowExecutor(KernelBuilder kernelBuilder, IFlowStatusProvider statusProvider, Dictionary<object, string?> globalSkillCollection, FlowPlannerConfig? config = null)
    {
        this._kernelBuilder = kernelBuilder;
        this._systemKernel = kernelBuilder.Build();

        this._logger = this._systemKernel.Log;
        this._config = config ?? new FlowPlannerConfig();

        this._flowStatusProvider = statusProvider;
        this._globalSkillCollection = globalSkillCollection;
        this._reActEngine = new ReActEngine(this._systemKernel, this._logger, this._config);
    }

    public async Task<SKContext> ExecuteAsync(Flow flow, string sessionId, string input)
    {
        Verify.NotNull(flow, nameof(flow));

        this._logger?.BeginScope(nameof(FlowExecutor));
        this._logger?.LogInformation("Executing flow {FlowName} with sessionId={SessionId}.", flow.Name, sessionId);
        var sortedSteps = flow.SortSteps();

        SKContext rootContext = this._systemKernel.CreateNewContext();
        var variables = await this._flowStatusProvider.GetVariables(sessionId).ConfigureAwait(false);
        foreach (var kv in variables)
        {
            rootContext.Variables.Set(kv.Key, kv.Value);
        }

        List<string> outputs = new();

        for (int stepIndex = 0; stepIndex < sortedSteps.Count; stepIndex++)
        {
            var step = sortedSteps[stepIndex];
            variables = rootContext.Variables.ToDictionary(_ => _.Key, _ => _.Value);

            if (step is Flow)
            {
                throw new PlanningException(PlanningException.ErrorCodes.InvalidPlan, "Recursive flow is not supported yet.");
            }

            if (step.Requires.Except(variables.Keys).Any())
            {
                throw new PlanningException(PlanningException.ErrorCodes.InvalidPlan, $"Step {step.Goal} requires variables that are not provided. ");
            }

            // continue if all variables are provided
            if (!step.Provides.Except(variables.Keys).Any())
            {
                continue;
            }

            this._logger?.LogInformation("Executing step {StepIndex}: {StepGoal}.", stepIndex, step.Goal);
            IKernel stepKernel = this._kernelBuilder.Build();

            var stepSkills = step.GetSKills(stepKernel, this._globalSkillCollection);
            foreach (var skill in stepSkills)
            {
                stepKernel.ImportSkill(skill);
            }

            var stepContext = stepKernel.CreateNewContext();
            foreach (var key in step.Requires)
            {
                stepContext.Variables.Set(key, variables[key]);
            }

            var stepResult = await this.ExecuteStepAsync(step, sessionId, $"{stepIndex}_{step.Goal}", input, stepKernel, stepContext).ConfigureAwait(false);
            if (stepResult.ErrorOccurred)
            {
                rootContext.Fail(stepResult.LastErrorDescription);
            }

            if (!string.IsNullOrEmpty(stepResult.Result) && stepResult.Variables.ContainsKey(Constants.ChatSkillVariables.PromptInputName))
            {
                outputs.Add(stepResult.Result);
            }

            bool completed = true;
            foreach (var variable in step.Provides)
            {
                if (!stepResult.Variables.ContainsKey(variable))
                {
                    completed = false;
                }
                else
                {
                    rootContext.Variables[variable] = stepResult.Variables[variable];
                }
            }

            await this._flowStatusProvider.SaveVariables(sessionId, rootContext.Variables.ToDictionary(_ => _.Key, _ => _.Value)).ConfigureAwait(false);

            if (completed)
            {
                this._logger?.LogInformation("Completed step {StepIndex}: {StepGoal}.", stepIndex, step.Goal);
            }
            else
            {
                break;
            }
        }

        rootContext.Variables.Update(JsonSerializer.Serialize(outputs));

        return rootContext;
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
            question += $"\n{variable}: {context.Variables[variable]}";
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

        context.Fail($"Failed to complete step {stepId} for session {sessionId}.");
        return context;
    }
}
