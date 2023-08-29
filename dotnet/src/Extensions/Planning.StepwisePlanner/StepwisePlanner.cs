// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics.CodeAnalysis;
using System.Globalization;
using System.Linq;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning.Stepwise;
using Microsoft.SemanticKernel.SemanticFunctions;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.TemplateEngine.Prompt;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of Plan
namespace Microsoft.SemanticKernel.Planning;
#pragma warning restore IDE0130

/// <summary>
/// A planner that creates a Stepwise plan using Mrkl systems.
/// </summary>
/// <remark>
/// An implementation of a Mrkl system as described in https://arxiv.org/pdf/2205.00445.pdf
/// </remark>
public class StepwisePlanner : IStepwisePlanner
{
    /// <summary>
    /// Initialize a new instance of the <see cref="StepwisePlanner"/> class.
    /// </summary>
    /// <param name="kernel">The semantic kernel instance.</param>
    /// <param name="config">Optional configuration object</param>
    public StepwisePlanner(
        IKernel kernel,
        StepwisePlannerConfig? config = null)
    {
        Verify.NotNull(kernel);
        this._kernel = kernel;

        // Set up Config with default values and excluded skills
        this.Config = config ?? new();
        this.Config.ExcludedSkills.Add(RestrictedSkillName);

        // Set up prompt templates
        this._promptTemplate = this.Config.GetPromptTemplate?.Invoke() ?? EmbeddedResource.Read("Skills.StepwiseStep.skprompt.txt");
        this._manualTemplate = EmbeddedResource.Read("Skills.RenderFunctionManual.skprompt.txt");
        this._questionTemplate = EmbeddedResource.Read("Skills.RenderQuestion.skprompt.txt");

        // Load or use default PromptConfig
        this._promptConfig = this.Config.PromptUserConfig ?? LoadPromptConfigFromResource();

        // Set MaxTokens for the prompt config
        this._promptConfig.Completion.MaxTokens = this.Config.MaxTokens;

        // Initialize prompt renderer
        this._promptRenderer = new PromptTemplateEngine();

        // Import native functions
        this._nativeFunctions = this._kernel.ImportSkill(this, RestrictedSkillName);

        // Create context and logger
        this._context = this._kernel.CreateNewContext();
        this._logger = this._kernel.LoggerFactory.CreateLogger(this.GetType());
    }

    /// <inheritdoc />
    public Plan CreatePlan(string goal)
    {
        if (string.IsNullOrEmpty(goal))
        {
            throw new SKException("The goal specified is empty");
        }

        Plan planStep = new(this._nativeFunctions["ExecutePlan"]);
        planStep.Parameters.Set("question", goal);

        planStep.Outputs.Add("stepCount");
        planStep.Outputs.Add("skillCount");
        planStep.Outputs.Add("stepsTaken");
        planStep.Outputs.Add("iterations");

        Plan plan = new(goal);

        plan.AddSteps(planStep);

        return plan;
    }

    [SKFunction, SKName("ExecutePlan"), Description("Execute a plan")]
    public async Task<SKContext> ExecutePlanAsync(
        [Description("The question to answer")]
        string question,
        SKContext context,
        CancellationToken token = default)
    {
        if (string.IsNullOrEmpty(question))
        {
            context.Variables.Update("Question not found.");
            return context;
        }

        var stepsTaken = new List<SystemStep>();

        ChatHistory chatHistory = await this.InitializeChatHistoryAsync(this.CreateChatHistory(this._kernel, out var aiService), aiService, context).ConfigureAwait(false);
        var chatCompletion = aiService as IChatCompletion;
        var textCompletion = aiService as ITextCompletion;

        var startingMessageCount = chatHistory.Messages.Count;

        var GetMessageTokens = () =>
        {
            var messages = string.Join("\n", chatHistory?.Messages);
            var tokenCount = messages.Length / 4;
            return tokenCount;
        };

        var GetCompletionAsync = async () =>
        {
            if (chatCompletion is not null)
            {
                var llmResponse = (await chatCompletion.GenerateMessageAsync(chatHistory, ChatRequestSettings.FromCompletionConfig(this._promptConfig.Completion), token).ConfigureAwait(false));
                return llmResponse;
            }
            else if (textCompletion is not null)
            {
                var thoughtProcess = string.Join("\n", chatHistory.Messages.Select(m => m.Content));
                var results = (await textCompletion.GetCompletionsAsync(thoughtProcess, CompleteRequestSettings.FromCompletionConfig(this._promptConfig.Completion), token).ConfigureAwait(false));

                if (results.Count == 0)
                {
                    throw new SKException("No completions returned.");
                }

                return await results[0].GetCompletionAsync(token).ConfigureAwait(false);
            }

            throw new SKException("No AIService available for getting completions.");
        };

        var GetNextStepCompletionAsync = () =>
            {
                var tokenCount = GetMessageTokens();

                var preserveFirstNSteps = 0; // first thought
                var removalIndex = (startingMessageCount) + preserveFirstNSteps;
                var messagesRemoved = 0;
                string? originalThought = null;
                while (tokenCount >= this.Config.MaxTokens && chatHistory?.Messages.Count > removalIndex)
                {
                    // something needs to be removed.
                    if (string.IsNullOrEmpty(originalThought))
                    {
                        originalThought = stepsTaken[0].Thought;

                        // Update message history
                        chatHistory.AddAssistantMessage($"{Thought} {originalThought}");
                        preserveFirstNSteps++;
                        chatHistory.AddAssistantMessage("... I've removed some of my previous work to make room for the new stuff ...");
                        preserveFirstNSteps++;

                        removalIndex = (startingMessageCount) + preserveFirstNSteps;
                    }

                    chatHistory.Messages.RemoveAt(removalIndex);
                    tokenCount = GetMessageTokens();
                    messagesRemoved++;
                }

                return GetCompletionAsync();
            };

        var GetNextStepAsync = async () =>
        {
            var actionText = await GetNextStepCompletionAsync().ConfigureAwait(false);
            this._logger?.LogDebug("Response: {ActionText}", actionText);
            return this.ParseResult(actionText);
        };

        SystemStep? lastStep = null;
        for (int i = 0; i < this.Config.MaxIterations; i++)
        {
            var nextStep = await GetNextStepAsync().ConfigureAwait(false);

            // If not Action/Thought/FinalAnswer is found,
            // add a message to the chat history to guide LLM into returning the next thought.
            if (string.IsNullOrEmpty(nextStep.Action) &&
                string.IsNullOrEmpty(nextStep.Thought) &&
                string.IsNullOrEmpty(nextStep.FinalAnswer))
            {
                this._logger?.LogWarning("No response from LLM");
                chatHistory?.AddUserMessage(Thought);
                continue;
            }

            // If a final answer is found, update and return the context with the result.
            if (!string.IsNullOrEmpty(nextStep.FinalAnswer))
            {
                this._logger?.LogInformation("Final Answer: {FinalAnswer}", nextStep.FinalAnswer);

                context.Variables.Update(nextStep.FinalAnswer);

                // Add additional results to the context
                AddExecutionStatsToContext(stepsTaken, context, i + 1);

                return context;
            }

            // If the thought is empty and the last step had no action, copy action to last step and set as new nextStep
            if (string.IsNullOrEmpty(nextStep.Thought) && lastStep is not null && string.IsNullOrEmpty(lastStep.Action))
            {
                lastStep.Action = nextStep.Action;
                lastStep.ActionVariables = nextStep.ActionVariables;

                lastStep.OriginalResponse += nextStep.OriginalResponse;
                nextStep = lastStep;
                if (chatHistory?.Messages.Count > startingMessageCount)
                {
                    chatHistory.Messages.RemoveAt(chatHistory.Messages.Count - 1);
                }
            }
            else
            {
                stepsTaken.Add(nextStep);
                lastStep = nextStep;
            }

            this._logger?.LogInformation("Thought: {Thought}", nextStep.Thought);

            if (!string.IsNullOrEmpty(nextStep!.Action!))
            {
                this._logger?.LogInformation("Action: {Action}({ActionVariables}). Iteration: {Iteration}.",
                    nextStep.Action, JsonSerializer.Serialize(nextStep.ActionVariables), i + 1);

                var actionMessage = $"{Action} {{\"action\": \"{nextStep.Action}\",\"action_variables\": {JsonSerializer.Serialize(nextStep.ActionVariables)}}}";

                var message = string.IsNullOrEmpty(nextStep.Thought) ? actionMessage : $"{Thought} {nextStep.Thought}\n{actionMessage}";
                chatHistory?.AddAssistantMessage(message);

                try
                {
                    await Task.Delay(this.Config.MinIterationTimeMs, token).ConfigureAwait(false);
                    var result = await this.InvokeActionAsync(nextStep.Action!, nextStep!.ActionVariables!).ConfigureAwait(false);

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
                    nextStep.Observation = $"Error invoking action {nextStep.Action} : {ex.Message}";
                    this._logger?.LogWarning(ex, "Error invoking action {Action}", nextStep.Action);
                }

                this._logger?.LogInformation("Observation: {Observation}", nextStep.Observation);
                chatHistory?.AddUserMessage($"{Observation} {nextStep.Observation}");
            }
            else
            {
                this._logger?.LogInformation("Action: No action to take");
                if (!string.IsNullOrEmpty(nextStep.Thought))
                {
                    chatHistory?.AddAssistantMessage($"{Thought} {nextStep.Thought}");
                }
            }

            // sleep for a bit to avoid rate limiting
            await Task.Delay(this.Config.MinIterationTimeMs, token).ConfigureAwait(false);
        }

        AddExecutionStatsToContext(stepsTaken, context, this.Config.MaxIterations);
        context.Variables.Update($"Result not found, review _stepsTaken to see what happened.\n{JsonSerializer.Serialize(stepsTaken)}");

        return context;
    }

    #region setup helpers
    // Function to load PromptConfig from embedded resource
    private static PromptTemplateConfig LoadPromptConfigFromResource()
    {
        string promptConfigString = EmbeddedResource.Read("Skills.StepwiseStep.config.json");
        return !string.IsNullOrEmpty(promptConfigString) ? PromptTemplateConfig.FromJson(promptConfigString) : new PromptTemplateConfig();
    }

    private async Task<ChatHistory> InitializeChatHistoryAsync(ChatHistory chatHistory, IAIService aiService, SKContext context)
    {
        // this.CreateChatHistory(this._kernel, out var aiService);
        var chatCompletion = aiService as IChatCompletion;
        var textCompletion = aiService as ITextCompletion;

        string userManual = await this.GetUserManualAsync(context).ConfigureAwait(false);
        string userQuestion = await this.GetUserQuestionAsync(context).ConfigureAwait(false);

#pragma warning disable CA2016 // Forward the 'CancellationToken' parameter to methods that take one -- the method is obsolete and to be removed.
        var systemContext = this._kernel.CreateNewContext();
#pragma warning restore CA2016

        systemContext.Variables.Set("suffix", this.Config.Suffix);

        if (chatCompletion is null)
        {
            systemContext.Variables.Set("functionDescriptions", userManual);
        }
        string systemMessage = await this.GetSystemMessage(systemContext).ConfigureAwait(false);

        chatHistory.AddSystemMessage(systemMessage);
        if (chatCompletion is not null)
        {
            chatHistory.AddUserMessage(userManual);
        }
        chatHistory.AddUserMessage(userQuestion);

        return chatHistory;
    }

    private ChatHistory CreateChatHistory(IKernel kernel, out IAIService aiService)
    {
        ChatHistory chatHistory;
        if (TryGetChatCompletion(this._kernel, out var chatCompletion))
        {
            chatHistory = chatCompletion.CreateNewChat();
            aiService = chatCompletion;
        }
        else
        {
            var textCompletion = this._kernel.GetService<ITextCompletion>();
            aiService = textCompletion;
            chatHistory = new ChatHistory();
        }

        return chatHistory;
    }

    private static bool TryGetChatCompletion(IKernel kernel, [NotNullWhen(true)] out IChatCompletion? chatCompletion)
    {
        try
        {
            // Client used to request answers to chat completion models
            chatCompletion = kernel.GetService<IChatCompletion>();
            return true;
        }
        catch (SKException)
        {
            chatCompletion = null;
        }

        return false;
    }

    private async Task<string> GetUserManualAsync(SKContext context)
    {
        var descriptions = await this.GetFunctionDescriptionsAsync().ConfigureAwait(false);
        context.Variables.Set("functionDescriptions", descriptions);
        return await this._promptRenderer.RenderAsync(this._manualTemplate, context).ConfigureAwait(false);
    }

    private Task<string> GetUserQuestionAsync(SKContext context)
    {
        return this._promptRenderer.RenderAsync(this._questionTemplate, context);
    }

    private Task<string> GetSystemMessage(SKContext context)
    {
        return this._promptRenderer.RenderAsync(this._promptTemplate, context);
    }
    #endregion setup helpers

    #region execution helpers
    public virtual SystemStep ParseResult(string input)
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
            throw new InvalidOperationException("Unexpected input format");
        }

        result.Thought = result.Thought?.Replace(Thought, string.Empty).Trim();

        // Extract action
        Match actionMatch = s_actionRegex.Match(input);

        if (actionMatch.Success)
        {
            var json = actionMatch.Groups[1].Value.Trim();

            try
            {
                var systemStepResults = JsonSerializer.Deserialize<SystemStep>(json);

                if (systemStepResults == null)
                {
                    result.Observation = $"System step parsing error, empty JSON: {json}";
                }
                else
                {
                    result.Action = systemStepResults.Action;
                    result.ActionVariables = systemStepResults.ActionVariables;
                }
            }
            catch (JsonException)
            {
                result.Observation = $"System step parsing error, invalid JSON: {json}";
            }
        }

        if (string.IsNullOrEmpty(result.Thought) && string.IsNullOrEmpty(result.Action))
        {
            result.Observation = "System step error, no thought or action found. Please give a valid thought and/or action.";
        }

        return result;
    }

    private async Task<string> InvokeActionAsync(string actionName, Dictionary<string, string> actionVariables)
    {
        var availableFunctions = await this.GetAvailableFunctionsAsync().ConfigureAwait(false);
        var targetFunction = availableFunctions.FirstOrDefault(f => ToFullyQualifiedName(f) == actionName);
        if (targetFunction == null)
        {
            this._logger?.LogDebug("Attempt to invoke action {Action} failed", actionName);
            return $"{actionName} is not in [AVAILABLE FUNCTIONS]. Please try again using one of the [AVAILABLE FUNCTIONS].";
        }

        try
        {
            ISKFunction function = this.GetFunction(targetFunction);

            var actionContext = this.CreateActionContext(actionVariables);

            var result = await function.InvokeAsync(actionContext).ConfigureAwait(false);

            if (result.ErrorOccurred)
            {
                this._logger?.LogError("Error occurred: {Error}", result.LastException);
                return $"Error occurred: {result.LastException}";
            }

            this._logger?.LogTrace("Invoked {FunctionName}. Result: {Result}", targetFunction.Name, result.Result);

            return result.Result;
        }
        catch (Exception e) when (!e.IsCriticalException())
        {
            this._logger?.LogError(e, "Something went wrong in system step: {0}.{1}. Error: {2}", targetFunction.SkillName, targetFunction.Name, e.Message);
            return $"Something went wrong in system step: {targetFunction.SkillName}.{targetFunction.Name}. Error: {e.Message} {e.InnerException.Message}";
        }
    }

    private ISKFunction GetFunction(FunctionView targetFunction)
    {
        var getFunction = (string skillName, string functionName) =>
        {
            return this._kernel.Func(skillName, functionName);
        };
        var getSkillFunction = this.Config.GetSkillFunction ?? getFunction;
        var function = getSkillFunction(targetFunction.SkillName, targetFunction.Name);
        return function;
    }

    private async Task<string> GetFunctionDescriptionsAsync()
    {
        // Use configured function provider if available, otherwise use the default SKContext function provider.
        var availableFunctions = await this.GetAvailableFunctionsAsync().ConfigureAwait(false);
        var functionDescriptions = string.Join("\n\n", availableFunctions.Select(x => ToManualString(x)));
        return functionDescriptions;
    }

    private Task<IOrderedEnumerable<FunctionView>> GetAvailableFunctionsAsync()
    {
        if (this.Config.GetAvailableFunctionsAsync is null)
        {
            FunctionsView functionsView = this._context.Skills!.GetFunctionsView();

            var excludedSkills = this.Config.ExcludedSkills ?? new();
            var excludedFunctions = this.Config.ExcludedFunctions ?? new();

            var availableFunctions =
                functionsView.NativeFunctions
                    .Concat(functionsView.SemanticFunctions)
                    .SelectMany(x => x.Value)
                    .Where(s => !excludedSkills.Contains(s.SkillName) && !excludedFunctions.Contains(s.Name))
                    .OrderBy(x => x.SkillName)
                    .ThenBy(x => x.Name);

            return Task.FromResult(availableFunctions);
        }

        return this.Config.GetAvailableFunctionsAsync(this.Config, null, CancellationToken.None);
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

    private SKContext CreateActionContext(Dictionary<string, string> actionVariables)
    {
        var actionContext = this._kernel.CreateNewContext();
        if (actionVariables != null)
        {
            foreach (var kvp in actionVariables)
            {
                actionContext.Variables.Set(kvp.Key, kvp.Value);
            }
        }

        return actionContext;
    }

    private static void AddExecutionStatsToContext(List<SystemStep> stepsTaken, SKContext context, int iterations)
    {
        context.Variables.Set("stepCount", stepsTaken.Count.ToString(CultureInfo.InvariantCulture));
        context.Variables.Set("stepsTaken", JsonSerializer.Serialize(stepsTaken));
        context.Variables.Set("iterations", iterations.ToString(CultureInfo.InvariantCulture));

        Dictionary<string, int> actionCounts = new();
        foreach (var step in stepsTaken)
        {
            if (string.IsNullOrEmpty(step.Action)) { continue; }

            _ = actionCounts.TryGetValue(step.Action!, out int currentCount);
            actionCounts[step.Action!] = ++currentCount;
        }

        var skillCallListWithCounts = string.Join(", ", actionCounts.Keys.Select(skill =>
            $"{skill}({actionCounts[skill]})"));

        var skillCallCountStr = actionCounts.Values.Sum().ToString(CultureInfo.InvariantCulture);

        context.Variables.Set("skillCount", $"{skillCallCountStr} ({skillCallListWithCounts})");
    }
    #endregion execution helpers

    #region private
    /// <summary>
    /// The configuration for the StepwisePlanner
    /// </summary>
    private StepwisePlannerConfig Config { get; }

    // Context used to access the list of functions in the kernel
    private readonly SKContext _context;
    private readonly IKernel _kernel;
    private readonly ILogger? _logger;

    /// <summary>
    /// Planner native functions
    /// </summary>
    private IDictionary<string, ISKFunction> _nativeFunctions = new Dictionary<string, ISKFunction>();

    /// <summary>
    /// The prompt template to use for the system step
    /// </summary>
    private string _promptTemplate;

    /// <summary>
    /// The question template to use for the system step
    /// </summary>
    private string _questionTemplate;

    /// <summary>
    /// The function manual template to use for the system step
    /// </summary>
    private string _manualTemplate;

    /// <summary>
    /// The prompt renderer to use for the system step
    /// </summary>
    private PromptTemplateEngine _promptRenderer;

    /// <summary>
    /// The prompt config to use for the system step
    /// </summary>
    private PromptTemplateConfig _promptConfig;

    /// <summary>
    /// The name to use when creating semantic functions that are restricted from plan creation
    /// </summary>
    private const string RestrictedSkillName = "StepwisePlanner_Excluded";

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
    /// The regex for parsing the action response
    /// </summary>
    private static readonly Regex s_actionRegex = new(@"\[ACTION\][^{}]*({(?:[^{}]*{[^{}]*})*[^{}]*})", RegexOptions.Singleline | RegexOptions.IgnoreCase);

    /// <summary>
    /// The regex for parsing the thought response
    /// </summary>
    private static readonly Regex s_thoughtRegex = new(@"(\[THOUGHT\])?(?<thought>.+?)(?=\[ACTION\]|$)", RegexOptions.Singleline | RegexOptions.IgnoreCase);

    /// <summary>
    /// The regex for parsing the final answer response
    /// </summary>
    private static readonly Regex s_finalAnswerRegex = new(@"\[FINAL[_\s\-]?ANSWER\](?<final_answer>.+)", RegexOptions.Singleline | RegexOptions.IgnoreCase);
    #endregion private
}
