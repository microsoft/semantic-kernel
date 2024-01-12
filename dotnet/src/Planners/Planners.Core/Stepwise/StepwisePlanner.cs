// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Globalization;
using System.Linq;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// A planner that creates a Stepwise plan using Mrkl systems.
/// </summary>
/// <remarks>
/// An implementation of a Mrkl system as described in https://arxiv.org/pdf/2205.00445.pdf
/// </remarks>
public class StepwisePlanner
{
    /// <summary>
    /// Initialize a new instance of the <see cref="StepwisePlanner"/> class.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="config">Optional configuration object</param>
    public StepwisePlanner(
        Kernel kernel,
        StepwisePlannerConfig? config = null)
    {
        Verify.NotNull(kernel);
        this._kernel = kernel;

        // Set up Config with default values and excluded plugins
        this.Config = config ?? new();
        this.Config.ExcludedPlugins.Add(RestrictedPluginName);

        // Set up prompt templates
        this._promptTemplate = this.Config.GetPromptTemplate?.Invoke() ?? EmbeddedResource.Read("Stepwise.Plugin.StepwiseStep.skprompt.txt");
        this._manualTemplate = EmbeddedResource.Read("Stepwise.Plugin.RenderFunctionManual.skprompt.txt");
        this._questionTemplate = EmbeddedResource.Read("Stepwise.Plugin.RenderQuestion.skprompt.txt");

        // Load or use default PromptModel
        this._promptConfig = this.Config.PromptUserConfig ?? LoadPromptConfigFromResource();

        // Set MaxTokens for the prompt config
        this._promptConfig.SetMaxTokens(this.Config.MaxCompletionTokens);

        ILoggerFactory loggerFactory = this._kernel.LoggerFactory;

        // Initialize prompt renderer
        this._promptTemplateFactory = new KernelPromptTemplateFactory(loggerFactory);

        // Import native functions
        this._nativeFunctions = this._kernel.ImportPluginFromObject(this, RestrictedPluginName);

        // Create context and logger
        this._logger = loggerFactory.CreateLogger(this.GetType()) ?? NullLogger.Instance;
    }

    /// <summary>Creates a plan for the specified goal.</summary>
    /// <param name="goal">The goal for which a plan should be created.</param>
    /// <returns>The created plan.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="goal"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="goal"/> is empty or entirely composed of whitespace.</exception>
    /// <exception cref="KernelException">A plan could not be created.</exception>
    public Plan CreatePlan(string goal)
    {
        Verify.NotNullOrWhiteSpace(goal);

        Task<Plan> task = PlannerInstrumentation.CreatePlanAsync(
            static (StepwisePlanner planner, string goal, CancellationToken _) =>
            {
                Plan plan = new(planner._nativeFunctions["ExecutePlan"])
                {
                    PluginName = RestrictedPluginName,
                    Outputs = { "stepCount", "functionCount", "stepsTaken", "iterations" },
                };
                plan.Parameters.Set("question", goal);
                return Task.FromResult(plan);
            },
            static (Plan plan) => plan.ToSafePlanString(),
            this, goal, this._logger, CancellationToken.None);

        // The instrumentation doesn't do any asynchronous work other than invoke the supplied callback,
        // which we know will complete synchronously, so we can safely use GetResult without incurring
        // blocking as the operation will have already completed by the time the call returns.
        Debug.Assert(task.IsCompleted);
#pragma warning disable VSTHRD002 // Avoid problematic synchronous waits
        return task.GetAwaiter().GetResult();
#pragma warning restore VSTHRD002
    }

    /// <summary>
    /// Execute a plan
    /// </summary>
    /// <param name="question">The question to answer</param>
    /// <param name="contextVariables">The context variables to use</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The result</returns>
    /// <exception cref="KernelException">No AIService available for getting completions.</exception>
    [KernelFunction, Description("Execute a plan")]
    public async Task<string> ExecutePlanAsync(
        [Description("The question to answer")]
        string question,
        ContextVariables contextVariables,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrEmpty(question))
        {
            contextVariables.Update("Question not found.");
            return "Question not found.";
        }

        ChatHistory chatHistory = await this.InitializeChatHistoryAsync(this._kernel, this.CreateChatHistory(this._kernel, out var aiService), aiService, question, contextVariables, cancellationToken).ConfigureAwait(false);

        if (aiService is null)
        {
            throw new KernelException("No AIService available for getting completions.");
        }

        if (chatHistory is null)
        {
            throw new KernelException("ChatHistory is null.");
        }

        var startingMessageCount = chatHistory.Count;

        var stepsTaken = new List<SystemStep>();
        SystemStep? lastStep = null;

        async Task<SystemStep> GetNextStepAsync()
        {
            var actionText = await this.GetNextStepCompletionAsync(stepsTaken, chatHistory, aiService, startingMessageCount, cancellationToken).ConfigureAwait(false);
            this._logger?.LogDebug("Response: {ActionText}", actionText);
            return this.ParseResult(actionText);
        }

        string? TryGetFinalAnswer(SystemStep step, int iterations, ContextVariables variables)
        {
            // If a final answer is found, update the context to be returned
            if (!string.IsNullOrEmpty(step.FinalAnswer))
            {
                this._logger?.LogInformation("Final Answer: {FinalAnswer}", step.FinalAnswer);

                variables.Update(step.FinalAnswer);

                stepsTaken.Add(step);

                // Add additional results to the context
                AddExecutionStatsToContextVariables(stepsTaken, variables, iterations);

                return variables.Input;
            }

            return null;
        }

        bool TryGetObservations(SystemStep step)
        {
            // If no Action/Thought is found, return any already available Observation from parsing the response.
            // Otherwise, add a message to the chat history to guide LLM into returning the next thought|action.
            if (string.IsNullOrEmpty(step.Action) &&
                string.IsNullOrEmpty(step.Thought))
            {
                // If there is an observation, add it to the chat history
                if (!string.IsNullOrEmpty(step.Observation))
                {
                    this._logger?.LogWarning("Invalid response from LLM, observation: {Observation}", step.Observation);
                    chatHistory.AddUserMessage($"{Observation} {step.Observation}");
                    stepsTaken.Add(step);
                    lastStep = step;
                    return true;
                }

                if (lastStep is not null && string.IsNullOrEmpty(lastStep.Action))
                {
                    this._logger?.LogWarning("No response from LLM, expected Action");
                    chatHistory.AddUserMessage(Action);
                }
                else
                {
                    this._logger?.LogWarning("No response from LLM, expected Thought");
                    chatHistory.AddUserMessage(Thought);
                }

                // No action or thought from LLM
                return true;
            }

            return false;
        }

        SystemStep AddNextStep(SystemStep step)
        {
            // If the thought is empty and the last step had no action, copy action to last step and set as new nextStep
            if (string.IsNullOrEmpty(step.Thought) && lastStep is not null && string.IsNullOrEmpty(lastStep.Action))
            {
                lastStep.Action = step.Action;
                lastStep.ActionVariables = step.ActionVariables;

                lastStep.OriginalResponse += step.OriginalResponse;
                step = lastStep;
                if (chatHistory.Count > startingMessageCount)
                {
                    chatHistory.RemoveAt(chatHistory.Count - 1);
                }
            }
            else
            {
                this._logger?.LogInformation("Thought: {Thought}", step.Thought);
                stepsTaken.Add(step);
                lastStep = step;
            }

            return step;
        }

        async Task<bool> TryGetActionObservationAsync(SystemStep step)
        {
            if (!string.IsNullOrEmpty(step.Action))
            {
                this._logger?.LogInformation("Action: {Action}({ActionVariables}).",
                    step.Action, JsonSerializer.Serialize(step.ActionVariables));

                // add [thought and] action to chat history
                var actionMessage = $"{Action} {{\"action\": \"{step.Action}\",\"action_variables\": {JsonSerializer.Serialize(step.ActionVariables)}}}";
                var message = string.IsNullOrEmpty(step.Thought) ? actionMessage : $"{Thought} {step.Thought}\n{actionMessage}";

                chatHistory.AddAssistantMessage(message);

                // Invoke the action
                try
                {
                    var result = await this.InvokeActionAsync(step.Action, step.ActionVariables, cancellationToken).ConfigureAwait(false);

                    step.Observation = string.IsNullOrEmpty(result) ? "Got no result from action" : result!;
                }
                catch (Exception ex) when (!ex.IsCriticalException())
                {
                    step.Observation = $"Error invoking action {step.Action} : {ex.Message}";
                    this._logger?.LogWarning(ex, "Error invoking action {Action}", step.Action);
                }

                this._logger?.LogInformation("Observation: {Observation}", step.Observation);
                chatHistory.AddUserMessage($"{Observation} {step.Observation}");

                return true;
            }

            return false;
        }

        bool TryGetThought(SystemStep step)
        {
            // Add thought to chat history
            if (!string.IsNullOrEmpty(step.Thought))
            {
                chatHistory.AddAssistantMessage($"{Thought} {step.Thought}");
            }

            return false;
        }

        for (int i = 0; i < this.Config.MaxIterations; i++)
        {
            // sleep for a bit to avoid rate limiting
            if (i > 0)
            {
                await Task.Delay(this.Config.MinIterationTimeMs, cancellationToken).ConfigureAwait(false);
            }

            // Get next step from LLM
            var nextStep = await GetNextStepAsync().ConfigureAwait(false);

            // If final answer is available, we're done, return the context
            var answer = TryGetFinalAnswer(nextStep, i + 1, contextVariables);
            if (answer is not null)
            {
                return answer;
            }

            // If we have an observation before running the action, continue to the next iteration
            if (TryGetObservations(nextStep))
            {
                continue;
            }

            // Add next step to steps taken, merging with last step if necessary
            // (e.g. the LLM gave Thought and Action one at a time, merge to encourage LLM to give both at once in future steps)
            nextStep = AddNextStep(nextStep);

            // Execute actions and get observations
            if (await TryGetActionObservationAsync(nextStep).ConfigureAwait(false))
            {
                continue;
            }

            this._logger?.LogInformation("Action: No action to take");

            // If we have a thought, continue to the next iteration
            if (TryGetThought(nextStep))
            {
                continue;
            }
        }

        AddExecutionStatsToContextVariables(stepsTaken, contextVariables, this.Config.MaxIterations);
        contextVariables.Update(NoFinalAnswerFoundMessage);

        return NoFinalAnswerFoundMessage;
    }

    #region setup helpers

    private async Task<ChatHistory> InitializeChatHistoryAsync(Kernel kernel, ChatHistory chatHistory, IAIService aiService, string question, ContextVariables variables, CancellationToken cancellationToken)
    {
        string userManual = await this.GetUserManualAsync(kernel, question, variables, cancellationToken).ConfigureAwait(false);
        string userQuestion = await this.GetUserQuestionAsync(kernel, variables, cancellationToken).ConfigureAwait(false);

        var systemVariables = new ContextVariables();

        systemVariables.Set("suffix", this.Config.Suffix);
        systemVariables.Set("functionDescriptions", userManual);
        string systemMessage = await this.GetSystemMessageAsync(kernel, systemVariables, cancellationToken).ConfigureAwait(false);

        chatHistory.AddSystemMessage(systemMessage);
        chatHistory.AddUserMessage(userQuestion);

        return chatHistory;
    }

    private ChatHistory CreateChatHistory(Kernel kernel, out IAIService aiService)
    {
        ChatHistory chatHistory;
        if (TryGetChatCompletion(this._kernel, out var chatCompletion))
        {
            chatHistory = chatCompletion.CreateNewChat();
            aiService = chatCompletion;
        }
        else
        {
            aiService = this._kernel.GetService<ITextGeneration>();
            chatHistory = new ChatHistory();
        }

        return chatHistory;
    }

    private async Task<string> GetUserManualAsync(Kernel kernel, string question, ContextVariables variables, CancellationToken cancellationToken)
    {
        var descriptions = await this._kernel.Plugins.GetFunctionsManualAsync(this.Config, question, this._logger, cancellationToken).ConfigureAwait(false);
        variables.Set("functionDescriptions", descriptions);
        var promptTemplate = this._promptTemplateFactory.Create(this._manualTemplate, new PromptTemplateConfig());
        return await promptTemplate.RenderAsync(kernel, variables, cancellationToken).ConfigureAwait(false);
    }

    private Task<string> GetUserQuestionAsync(Kernel kernel, ContextVariables variables, CancellationToken cancellationToken)
        => this._promptTemplateFactory.Create(this._questionTemplate, new PromptTemplateConfig()).RenderAsync(kernel, variables, cancellationToken);

    private Task<string> GetSystemMessageAsync(Kernel kernel, ContextVariables variables, CancellationToken cancellationToken)
        => this._promptTemplateFactory.Create(this._promptTemplate, new PromptTemplateConfig()).RenderAsync(kernel, variables, cancellationToken);

    #endregion setup helpers

    #region execution helpers

    private Task<string> GetNextStepCompletionAsync(List<SystemStep> stepsTaken, ChatHistory chatHistory, IAIService aiService, int startingMessageCount, CancellationToken token)
    {
        var skipStart = startingMessageCount;
        var skipCount = 0;
        var lastObservationIndex = chatHistory.FindLastIndex(m => m.Content.StartsWith(Observation, StringComparison.OrdinalIgnoreCase));
        var messagesToKeep = lastObservationIndex >= 0 ? chatHistory.Count - lastObservationIndex : 0;

        string? originalThought = null;

        var tokenCount = chatHistory.GetTokenCount();
        while (tokenCount >= this.Config.MaxPromptTokens && chatHistory.Count > (skipStart + skipCount + messagesToKeep))
        {
            originalThought = $"{Thought} {stepsTaken.FirstOrDefault()?.Thought}";
            tokenCount = chatHistory.GetTokenCount($"{originalThought}\n{string.Format(CultureInfo.InvariantCulture, TrimMessageFormat, skipCount)}", skipStart, ++skipCount);
        }

        if (tokenCount >= this.Config.MaxPromptTokens)
        {
            throw new KernelException("ChatHistory is too long to get a completion. Try reducing the available functions.");
        }

        var reducedChatHistory = new ChatHistory();
        reducedChatHistory.AddRange(chatHistory.Where((m, i) => i < skipStart || i >= skipStart + skipCount));

        if (skipCount > 0 && originalThought is not null)
        {
            reducedChatHistory.InsertMessage(skipStart, AuthorRole.Assistant, string.Format(CultureInfo.InvariantCulture, TrimMessageFormat, skipCount));
            reducedChatHistory.InsertMessage(skipStart, AuthorRole.Assistant, originalThought);
        }

        return this.GetCompletionAsync(aiService, reducedChatHistory, stepsTaken.Count == 0, token);
    }

    private async Task<string> GetCompletionAsync(IAIService aiService, ChatHistory chatHistory, bool addThought, CancellationToken token)
    {
        if (aiService is IChatCompletion chatCompletion)
        {
            var llmResponse = (await chatCompletion.GenerateMessageAsync(chatHistory, this._promptConfig.GetDefaultRequestSettings(), token).ConfigureAwait(false));
            return llmResponse;
        }
        else if (aiService is ITextGeneration textGeneration)
        {
            var thoughtProcess = string.Join("\n", chatHistory.Select(m => m.Content));

            // Add Thought to the thought process at the start of the first iteration
            if (addThought)
            {
                thoughtProcess = $"{thoughtProcess}\n{Thought}";
                addThought = false;
            }

            thoughtProcess = $"{thoughtProcess}\n";
            IReadOnlyList<ITextResult> results = await textGeneration.GetCompletionsAsync(thoughtProcess, this._promptConfig.GetDefaultRequestSettings(), token).ConfigureAwait(false);

            if (results.Count == 0)
            {
                throw new KernelException("No completions returned.");
            }

            return await results[0].GetCompletionAsync(token).ConfigureAwait(false);
        }

        throw new KernelException("No AIService available for getting completions.");
    }

    /// <summary>
    /// Parse LLM response into a SystemStep during execution
    /// </summary>
    /// <param name="input">The response from the LLM</param>
    /// <returns>A SystemStep</returns>
    protected internal virtual SystemStep ParseResult(string input)
    {
        var result = new SystemStep
        {
            OriginalResponse = input
        };

        // Extract final answer
        Match finalAnswerMatch = s_finalAnswerRegex.Match(input);

        if (finalAnswerMatch.Success)
        {
            result.FinalAnswer = finalAnswerMatch.Groups[1].Value.Trim();
            return result;
        }

        // Extract thought
        Match thoughtMatch = s_thoughtRegex.Match(input);

        if (thoughtMatch.Success)
        {
            // if it contains Action, it was only an action
            if (!thoughtMatch.Value.Contains(Action))
            {
                result.Thought = thoughtMatch.Value.Trim();
            }
        }
        else if (!input.Contains(Action))
        {
            result.Thought = input;
        }
        else
        {
            return result;
        }

        result.Thought = result.Thought.Replace(Thought, string.Empty).Trim();

        // Extract action
        // Using regex is prone to issues with complex action json, so we use a simple string search instead
        // This can be less fault tolerant in some scenarios where the LLM tries to call multiple actions, for example.
        // TODO -- that could possibly be improved if we allow an action to be a list of actions.
        int actionIndex = input.IndexOf(Action, StringComparison.OrdinalIgnoreCase);

        if (actionIndex != -1)
        {
            int jsonStartIndex = input.IndexOf("{", actionIndex, StringComparison.OrdinalIgnoreCase);
            if (jsonStartIndex != -1)
            {
                int jsonEndIndex = input.Substring(jsonStartIndex).LastIndexOf("}", StringComparison.OrdinalIgnoreCase);
                if (jsonEndIndex != -1)
                {
                    string json = input.Substring(jsonStartIndex, jsonEndIndex + 1);

                    try
                    {
                        var systemStepResults = JsonSerializer.Deserialize<SystemStep>(json);

                        if (systemStepResults is not null)
                        {
                            result.Action = systemStepResults.Action;
                            result.ActionVariables = systemStepResults.ActionVariables;
                        }
                    }
                    catch (JsonException je)
                    {
                        result.Observation = $"Action parsing error: {je.Message}\nInvalid action: {json}";
                    }
                }
            }
        }

        return result;
    }

    private async Task<string?> InvokeActionAsync(string actionName, Dictionary<string, string> actionVariables, CancellationToken cancellationToken)
    {
        FunctionUtils.SplitPluginFunctionName(actionName, out var pluginName, out var functionName);
        if (string.IsNullOrEmpty(functionName))
        {
            this._logger?.LogDebug("Attempt to invoke action {Action} failed", actionName);
            return $"Could not parse functionName from actionName: {actionName}. Please try again using one of the [AVAILABLE FUNCTIONS].";
        }

        var getFunctionCallback = this.Config.GetFunctionCallback ?? this._kernel.Plugins.GetFunctionCallback();
        var targetFunction = getFunctionCallback(pluginName, functionName);

        if (targetFunction == null)
        {
            this._logger?.LogDebug("Attempt to invoke action {Action} failed", actionName);
            return $"{actionName} is not in [AVAILABLE FUNCTIONS]. Please try again using one of the [AVAILABLE FUNCTIONS].";
        }

        try
        {
            string? result = null;

            var vars = this.CreateActionContextVariables(actionVariables);
            var functionResult = await this._kernel.InvokeAsync(targetFunction, vars, cancellationToken).ConfigureAwait(false);
            var resultObject = functionResult.GetValue<object>();

            if (resultObject is not null)
            {
                var converter = TypeDescriptor.GetConverter(resultObject);
                if (converter.CanConvertTo(typeof(string)))
                {
                    result = converter.ConvertToString(resultObject);
                }
            }

            this._logger?.LogTrace("Invoked {FunctionName}. Result: {Result}", targetFunction.Name, result);

            return result;
        }
        catch (Exception e) when (!e.IsCriticalException())
        {
            this._logger?.LogError(e, "Something went wrong in system step: {Function}. Error: {Error}", targetFunction.Name, e.Message);
            throw;
        }
    }

    private ContextVariables CreateActionContextVariables(Dictionary<string, string> actionVariables)
    {
        ContextVariables vars = new();
        if (actionVariables != null)
        {
            foreach (var kvp in actionVariables)
            {
                vars.Set(kvp.Key, kvp.Value);
            }
        }

        return vars;
    }

    #endregion execution helpers

    private static PromptTemplateConfig LoadPromptConfigFromResource()
    {
        string promptConfigString = EmbeddedResource.Read("Stepwise.Plugin.StepwiseStep.config.json");
        return !string.IsNullOrEmpty(promptConfigString) ? PromptTemplateConfig.FromJson(promptConfigString) : new PromptTemplateConfig();
    }

    private static bool TryGetChatCompletion(Kernel kernel, [NotNullWhen(true)] out IChatCompletion? chatCompletion)
    {
        try
        {
            // Client used to request answers to chat completion models
            // TODO #2635 - Using TryGetService would improve cost of this method to avoid exception handling
            chatCompletion = kernel.GetService<IChatCompletion>();
            return true;
        }
        catch (KernelException)
        {
            chatCompletion = null;
        }

        return false;
    }

    private static void AddExecutionStatsToContextVariables(List<SystemStep> stepsTaken, ContextVariables variables, int iterations)
    {
        variables.Set("stepCount", stepsTaken.Count.ToString(CultureInfo.InvariantCulture));
        variables.Set("stepsTaken", JsonSerializer.Serialize(stepsTaken));
        variables.Set("iterations", iterations.ToString(CultureInfo.InvariantCulture));

        Dictionary<string, int> actionCounts = new();
        foreach (var step in stepsTaken)
        {
            if (string.IsNullOrEmpty(step.Action)) { continue; }

            _ = actionCounts.TryGetValue(step.Action, out int currentCount);
            actionCounts[step.Action!] = ++currentCount;
        }

        var functionCallListWithCounts = string.Join(", ", actionCounts.Keys.Select(function =>
            $"{function}({actionCounts[function]})"));

        var functionCallCountStr = actionCounts.Values.Sum().ToString(CultureInfo.InvariantCulture);

        variables.Set("functionCount", $"{functionCallCountStr} ({functionCallListWithCounts})");
    }

    #region private

    /// <summary>
    /// The configuration for the StepwisePlanner
    /// </summary>
    private StepwisePlannerConfig Config { get; }

    // Context used to access the list of functions in the kernel
    private readonly Kernel _kernel;
    private readonly ILogger _logger;

    /// <summary>
    /// Planner native functions
    /// </summary>
    private readonly IKernelPlugin _nativeFunctions;

    /// <summary>
    /// The prompt template to use for the system step
    /// </summary>
    private readonly string _promptTemplate;

    /// <summary>
    /// The question template to use for the system step
    /// </summary>
    private readonly string _questionTemplate;

    /// <summary>
    /// The function manual template to use for the system step
    /// </summary>
    private readonly string _manualTemplate;

    /// <summary>
    /// The prompt renderer to use for the system step
    /// </summary>
    private readonly KernelPromptTemplateFactory _promptTemplateFactory;

    /// <summary>
    /// The prompt config to use for the system step
    /// </summary>
    private readonly PromptTemplateConfig _promptConfig;

    /// <summary>
    /// The name to use when creating semantic functions that are restricted from plan creation
    /// </summary>
    private const string RestrictedPluginName = "StepwisePlanner_Excluded";

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
    /// The chat message to include when trimming thought process history
    /// </summary>
    private const string TrimMessageFormat = "... I've removed the first {0} steps of my previous work to make room for the new stuff ...";

    /// <summary>
    /// The regex for parsing the thought response
    /// </summary>
    private static readonly Regex s_thoughtRegex = new(@"(\[THOUGHT\])?(?<thought>.+?)(?=\[ACTION\]|$)", RegexOptions.Singleline | RegexOptions.IgnoreCase);

    /// <summary>
    /// The regex for parsing the final answer response
    /// </summary>
    private static readonly Regex s_finalAnswerRegex = new(@"\[FINAL[_\s\-]?ANSWER\](?<final_answer>.+)", RegexOptions.Singleline | RegexOptions.IgnoreCase);

    /// <summary>
    /// The message to include when no final answer is found
    /// </summary>
    private const string NoFinalAnswerFoundMessage = "Result not found, review 'stepsTaken' to see what happened.";

    #endregion private
}
