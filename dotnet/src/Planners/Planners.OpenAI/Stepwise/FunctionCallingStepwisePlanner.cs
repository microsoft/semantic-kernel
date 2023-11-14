// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Functions.OpenAPI.Model;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.TemplateEngine;
using Microsoft.SemanticKernel.TemplateEngine.Basic;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of Plan
namespace Microsoft.SemanticKernel.Planners;
#pragma warning restore IDE0130

/// <summary>
/// A planner that uses OpenAI function calling in a stepwise manner to fulfill a user goal or question.
/// </summary>
public class FunctionCallingStepwisePlanner
{
    /// <summary>
    /// Initialize a new instance of the <see cref="FunctionCallingStepwisePlanner"/> class.
    /// </summary>
    /// <param name="kernel">The semantic kernel instance.</param>
    /// <param name="config">The planner configuration.</param>
    public FunctionCallingStepwisePlanner(
        IKernel kernel,
        FunctionCallingStepwisePlannerConfig? config = null)
    {
        Verify.NotNull(kernel);
        this._kernel = kernel;
        this._chatCompletion = kernel.GetService<IChatCompletion>();

        // Initialize prompt renderer
        this._promptTemplateFactory = new BasicPromptTemplateFactory(this._kernel.LoggerFactory);

        // Set up Config with default values and excluded plugins
        this.Config = config ?? new();
        this.Config.ExcludedPlugins.Add(RestrictedPluginName);

        this._initialPlanPrompt = EmbeddedResource.Read("Stepwise.InitialPlanPrompt.txt");
        this._stepPrompt = EmbeddedResource.Read("Stepwise.StepPrompt.txt");

        // Create context and logger
        this._logger = this._kernel.LoggerFactory.CreateLogger(this.GetType());
    }

    /// <summary>
    /// Execute a plan
    /// </summary>
    /// <param name="question">The question to answer</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Result containing the model's response message and chat history.</returns>
    /// <exception cref="SKException">If no goal found or failed to retrieve function from kernel.</exception>
    public async Task<FunctionCallingStepwisePlannerResult> ExecuteAsync(
        string question,
        CancellationToken cancellationToken = default)
    {
        string planResponse = string.Empty;

        if (string.IsNullOrEmpty(question))
        {
            throw new SKException("Goal not found.");
        }

        // Request completion for initial plan
        var chatHistoryForPlan = await this.BuildChatHistoryForInitialPlanAsync(question, cancellationToken).ConfigureAwait(false);
        string initialPlan = (await this._chatCompletion.GenerateMessageAsync(chatHistoryForPlan, null /* request settings */, cancellationToken).ConfigureAwait(false));

        var chatHistoryForSteps = await this.BuildChatHistoryForStepAsync(question, initialPlan, cancellationToken).ConfigureAwait(false);
        string resultContent = string.Empty;

        for (int i = 0; i < this.Config.MaxIterations; i++)
        {
            // sleep for a bit to avoid rate limiting
            if (i > 0)
            {
                await Task.Delay(this.Config.MinIterationTimeMs, cancellationToken).ConfigureAwait(false);
            }

            // For each step, request another completion to select a function for that step
            chatHistoryForSteps.AddUserMessage(StepwiseUserMessage);
            var chatResult = await this.GetCompletionWithFunctionsAsync(chatHistoryForSteps, cancellationToken).ConfigureAwait(false);
            chatHistoryForSteps.AddAssistantMessage(chatResult);

            OpenAIFunctionResponse? functionResponse = null;
            try
            {
                functionResponse = chatResult.GetOpenAIFunctionResponse();
            }
            catch (JsonException)
            {
                var errorMessage = "That function call is invalid. Try something else!";
                chatHistoryForSteps.AddUserMessage(errorMessage);
                continue;
            }

            if (functionResponse is null)
            {
                // The model replied with a message - check for final answer
                var messageContent = (await chatResult.GetChatMessageAsync(cancellationToken).ConfigureAwait(false)).Content;

                Match finalAnswerMatch = s_finalAnswerRegex.Match(messageContent);
                if (finalAnswerMatch.Success)
                {
                    return new FunctionCallingStepwisePlannerResult
                    {
                        FinalAnswer = finalAnswerMatch.Groups[1].Value.Trim(),
                        ChatHistory = chatHistoryForSteps,
                        Iterations = i + 1,
                    };
                }

                // No final answer found yet, so continue looping through steps
                continue;
            }

            // Look up SKFunction
            if (!this._kernel.Functions.TryGetFunctionAndContext(functionResponse, out ISKFunction? pluginFunction, out ContextVariables? funcContext))
            {
                var errorMessage = $"Function {functionResponse.FullyQualifiedName} does not exist in the kernel. Try something else!";
                chatHistoryForSteps.AddUserMessage(errorMessage);

                continue;
            }

            // Execute function and add to chat history
            try
            {
                var result = (await this._kernel.RunAsync(funcContext, cancellationToken, pluginFunction).ConfigureAwait(false)).GetValue<object>();

                if (result is RestApiOperationResponse apiResponse)
                {
                    resultContent = apiResponse.Content as string ?? string.Empty;
                }
                else if (result is string str)
                {
                    resultContent = str;
                }
                else
                {
                    resultContent = JsonSerializer.Serialize(result);
                }

                chatHistoryForSteps.AddFunctionMessage(resultContent, functionResponse.FullyQualifiedName);
            }
            catch (SKException)
            {
                var errorMessage = $"Failed to execute function {functionResponse.FullyQualifiedName}. Try something else!";
                chatHistoryForSteps.AddUserMessage(errorMessage);
            }
        }

        // We've completed the max iterations, but the model hasn't returned a final answer.
        return new FunctionCallingStepwisePlannerResult
        {
            FinalAnswer = string.Empty,
            ChatHistory = chatHistoryForSteps,
            Iterations = this.Config.MaxIterations,
        };
    }

    private async Task<IChatResult> GetCompletionWithFunctionsAsync(
            ChatHistory chatHistory,
            CancellationToken cancellationToken)
    {
        var requestSettings = this.PrepareOpenAIRequestSettingsWithFunctions();
        return (await this._chatCompletion.GetChatCompletionsAsync(chatHistory, requestSettings, cancellationToken).ConfigureAwait(false))[0];
    }

    private async Task<string> GetFunctionsManualAsync(CancellationToken cancellationToken)
    {
        var availableFunctions = await this._kernel.Functions.GetFunctionsAsync(this.Config, null, this._logger, cancellationToken).ConfigureAwait(false);

        return string.Join("\n\n", availableFunctions.Select(x => x.ToManualString()));
    }

    private OpenAIRequestSettings PrepareOpenAIRequestSettingsWithFunctions()
    {
        var requestSettings = this.Config.ModelSettings ?? new OpenAIRequestSettings();
        requestSettings.FunctionCall = OpenAIRequestSettings.FunctionCallAuto;
        requestSettings.Functions = this._kernel.Functions.GetFunctionViews().Select(f => f.ToOpenAIFunction()).ToList();
        return requestSettings;
    }

    private async Task<ChatHistory> BuildChatHistoryForInitialPlanAsync(
        string goal,
        CancellationToken cancellationToken)
    {
        var chatHistory = this._chatCompletion.CreateNewChat();

        var systemContext = this._kernel.CreateNewContext();
        string functionsManual = await this.GetFunctionsManualAsync(cancellationToken).ConfigureAwait(false);
        systemContext.Variables.Set(AvailableFunctionsKey, functionsManual);
        string systemMessage = await this._promptTemplateFactory.Create(this._initialPlanPrompt, new PromptTemplateConfig()).RenderAsync(systemContext, cancellationToken).ConfigureAwait(false);

        chatHistory.AddSystemMessage(systemMessage);
        chatHistory.AddUserMessage(goal);

        return chatHistory;
    }

    private async Task<ChatHistory> BuildChatHistoryForStepAsync(
        string goal,
        string initialPlan,
        CancellationToken cancellationToken)
    {
        var chatHistory = this._chatCompletion.CreateNewChat();

        // Add system message with context about outputs of previous functions
        var systemContext = this._kernel.CreateNewContext();
        systemContext.Variables.Set(GoalKey, goal);
        systemContext.Variables.Set(InitialPlanKey, initialPlan);
        var systemMessage = await this._promptTemplateFactory.Create(this._stepPrompt, new PromptTemplateConfig()).RenderAsync(systemContext, cancellationToken).ConfigureAwait(false);

        chatHistory.AddSystemMessage(systemMessage);

        return chatHistory;
    }

    #region private

    /// <summary>
    /// The configuration for the StepwisePlanner
    /// </summary>
    private FunctionCallingStepwisePlannerConfig Config { get; }

    // Context used to access the list of functions in the kernel
    private readonly IKernel _kernel;
    private readonly IChatCompletion _chatCompletion;
    private readonly ILogger? _logger;

    /// <summary>
    /// The prompt (system message) used to generate the initial set of steps to perform.
    /// </summary>
    private readonly string _initialPlanPrompt;

    /// <summary>
    /// The prompt (system message) for performing the steps.
    /// </summary>
    private readonly string _stepPrompt;

    /// <summary>
    /// The prompt renderer to use for the system step
    /// </summary>
    private readonly BasicPromptTemplateFactory _promptTemplateFactory;

    /// <summary>
    /// The name to use when creating semantic functions that are restricted from plan creation
    /// </summary>
    private const string RestrictedPluginName = "OpenAIFunctionsStepwisePlanner_Excluded";

    /// <summary>
    /// The user message to add to the chat history for each step of the plan.
    /// </summary>
    private const string StepwiseUserMessage = "Perform the next step of the plan, or reply with the final answer prefixed with [FINAL ANSWER]";

    /// <summary>
    /// The regex for parsing the final answer response
    /// </summary>
    private static readonly Regex s_finalAnswerRegex = new(@"\[FINAL[_\s\-]?ANSWER\](?<final_answer>.+)", RegexOptions.Singleline | RegexOptions.IgnoreCase);

    // Context variable keys
    private const string AvailableFunctionsKey = "available_functions";
    private const string InitialPlanKey = "initial_plan";
    private const string GoalKey = "goal";

    #endregion private
}
