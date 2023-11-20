// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Json.More;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Functions.OpenAPI.Model;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.TemplateEngine;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of Plan
namespace Microsoft.SemanticKernel.Planners;
#pragma warning restore IDE0130

/// <summary>
/// A planner that uses OpenAI function calling in a stepwise manner to fulfill a user goal or question.
/// </summary>
public sealed class FunctionCallingStepwisePlanner
{
    /// <summary>
    /// Initialize a new instance of the <see cref="FunctionCallingStepwisePlanner"/> class.
    /// </summary>
    /// <param name="kernel">The semantic kernel instance.</param>
    /// <param name="config">The planner configuration.</param>
    public FunctionCallingStepwisePlanner(
        Kernel kernel,
        FunctionCallingStepwisePlannerConfig? config = null)
    {
        Verify.NotNull(kernel);
        this._kernel = kernel;
        this._chatCompletion = kernel.GetService<IChatCompletion>();

        // Initialize prompt renderer
        this._promptTemplateFactory = new KernelPromptTemplateFactory(this._kernel.LoggerFactory);

        // Set up Config with default values and excluded plugins
        this.Config = config ?? new();
        this.Config.ExcludedPlugins.Add(RestrictedPluginName);

        this._initialPlanPrompt = this.Config.GetPromptTemplate?.Invoke() ?? EmbeddedResource.Read("Stepwise.InitialPlanPrompt.txt");
        this._stepPrompt = this.Config.GetStepPromptTemplate?.Invoke() ?? EmbeddedResource.Read("Stepwise.StepPrompt.txt");

        // Create context and logger
        this._logger = this._kernel.LoggerFactory.CreateLogger(this.GetType());
    }

    /// <summary>
    /// Execute a plan
    /// </summary>
    /// <param name="question">The question to answer</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Result containing the model's response message and chat history.</returns>
    public async Task<FunctionCallingStepwisePlannerResult> ExecuteAsync(
        string question,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(question);

        // Add the final answer function
        this._kernel.ImportPluginFromObject(new UserInteraction(), "UserInteraction");

        // Request completion for initial plan
        var chatHistoryForPlan = await this.BuildChatHistoryForInitialPlanAsync(question, cancellationToken).ConfigureAwait(false);
        string initialPlan = (await this._chatCompletion.GenerateMessageAsync(chatHistoryForPlan, null /* request settings */, cancellationToken).ConfigureAwait(false));

        var chatHistoryForSteps = await this.BuildChatHistoryForStepAsync(question, initialPlan, cancellationToken).ConfigureAwait(false);

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

            // Check for function response
            if (!this.TryGetFunctionResponse(chatResult, out OpenAIFunctionResponse? functionResponse, out string? functionResponseError))
            {
                // No function response found. Either AI returned a chat message, or something went wrong when parsing the function.
                // Log the error (if applicable), then let the planner continue.
                if (functionResponseError is not null)
                {
                    chatHistoryForSteps.AddUserMessage(functionResponseError);
                }
                continue;
            }

            // Check for final answer in the function response
            if (this.TryFindFinalAnswer(functionResponse, out string finalAnswer, out string? finalAnswerError))
            {
                if (finalAnswerError is not null)
                {
                    // We found a final answer, but failed to parse it properly.
                    // Log the error message in chat history and let the planner try again.
                    chatHistoryForSteps.AddUserMessage(finalAnswerError);
                    continue;
                }

                // Success! We found a final answer, so return the planner result.
                return new FunctionCallingStepwisePlannerResult
                {
                    FinalAnswer = finalAnswer,
                    ChatHistory = chatHistoryForSteps,
                    Iterations = i + 1,
                };
            }

            // Look up function in kernel
            if (this._kernel.Plugins.TryGetFunctionAndContext(functionResponse, out ISKFunction? pluginFunction, out ContextVariables? funcContext))
            {
                try
                {
                    // Execute function and add to result to chat history
                    var result = (await this._kernel.RunAsync(funcContext, cancellationToken, pluginFunction).ConfigureAwait(false)).GetValue<object>();
                    chatHistoryForSteps.AddFunctionMessage(ParseObjectAsString(result), functionResponse.FullyQualifiedName);
                }
                catch (SKException)
                {
                    chatHistoryForSteps.AddUserMessage($"Failed to execute function {functionResponse.FullyQualifiedName}. Try something else!");
                }
            }
            else
            {
                chatHistoryForSteps.AddUserMessage($"Function {functionResponse.FullyQualifiedName} does not exist in the kernel. Try something else!");
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

    #region private

    private async Task<IChatResult> GetCompletionWithFunctionsAsync(
            ChatHistory chatHistory,
            CancellationToken cancellationToken)
    {
        var requestSettings = this.PrepareOpenAIRequestSettingsWithFunctions();
        return (await this._chatCompletion.GetChatCompletionsAsync(chatHistory, requestSettings, cancellationToken).ConfigureAwait(false))[0];
    }

    private async Task<string> GetFunctionsManualAsync(CancellationToken cancellationToken)
    {
        return await this._kernel.Plugins.GetJsonSchemaFunctionsManualAsync(this.Config, null, this._logger, false, cancellationToken).ConfigureAwait(false);
    }

    private OpenAIRequestSettings PrepareOpenAIRequestSettingsWithFunctions()
    {
        var requestSettings = this.Config.ModelSettings ?? new OpenAIRequestSettings();
        requestSettings.FunctionCall = OpenAIRequestSettings.FunctionCallAuto;
        requestSettings.Functions = this._kernel.Plugins.GetFunctionViews().Select(f => f.ToOpenAIFunction()).ToList();
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
        string systemMessage = await this._promptTemplateFactory.Create(this._initialPlanPrompt, new PromptTemplateConfig()).RenderAsync(this._kernel, systemContext, cancellationToken).ConfigureAwait(false);

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

        // Add system message with context about the initial goal/plan
        var systemContext = this._kernel.CreateNewContext();
        systemContext.Variables.Set(GoalKey, goal);
        systemContext.Variables.Set(InitialPlanKey, initialPlan);
        var systemMessage = await this._promptTemplateFactory.Create(this._stepPrompt, new PromptTemplateConfig()).RenderAsync(this._kernel, systemContext, cancellationToken).ConfigureAwait(false);

        chatHistory.AddSystemMessage(systemMessage);

        return chatHistory;
    }

    private bool TryGetFunctionResponse(IChatResult chatResult, [NotNullWhen(true)] out OpenAIFunctionResponse? functionResponse, out string? errorMessage)
    {
        functionResponse = null;
        errorMessage = null;
        try
        {
            functionResponse = chatResult.GetOpenAIFunctionResponse();
        }
        catch (JsonException)
        {
            errorMessage = "That function call is invalid. Try something else!";
        }

        return functionResponse is not null;
    }

    private bool TryFindFinalAnswer(OpenAIFunctionResponse functionResponse, out string finalAnswer, out string? errorMessage)
    {
        finalAnswer = string.Empty;
        errorMessage = null;

        if (functionResponse.PluginName == "UserInteraction" && functionResponse.FunctionName == "SendFinalAnswer")
        {
            if (functionResponse.Parameters.Count > 0 && functionResponse.Parameters.TryGetValue("answer", out object valueObj))
            {
                finalAnswer = ParseObjectAsString(valueObj);
            }
            else
            {
                errorMessage = "Returned answer in incorrect format. Try again!";
            }
            return true;
        }
        return false;
    }

    private static string ParseObjectAsString(object? valueObj)
    {
        string resultStr = string.Empty;

        if (valueObj is RestApiOperationResponse apiResponse)
        {
            resultStr = apiResponse.Content as string ?? string.Empty;
        }
        else if (valueObj is string valueStr)
        {
            resultStr = valueStr;
        }
        else if (valueObj is JsonElement valueElement)
        {
            if (valueElement.ValueKind == JsonValueKind.String)
            {
                resultStr = valueElement.GetString() ?? "";
            }
            else
            {
                resultStr = valueElement.ToJsonString();
            }
        }
        else
        {
            resultStr = JsonSerializer.Serialize(valueObj);
        }

        return resultStr;
    }

    /// <summary>
    /// The configuration for the StepwisePlanner
    /// </summary>
    private FunctionCallingStepwisePlannerConfig Config { get; }

    // Context used to access the list of functions in the kernel
    private readonly Kernel _kernel;
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
    private readonly KernelPromptTemplateFactory _promptTemplateFactory;

    /// <summary>
    /// The name to use when creating semantic functions that are restricted from plan creation
    /// </summary>
    private const string RestrictedPluginName = "OpenAIFunctionsStepwisePlanner_Excluded";

    /// <summary>
    /// The user message to add to the chat history for each step of the plan.
    /// </summary>
    private const string StepwiseUserMessage = "Perform the next step of the plan if there is more work to do. When you have reached a final answer, use the UserInteraction_SendFinalAnswer function to communicate this back to the user.";

    // Context variable keys
    private const string AvailableFunctionsKey = "available_functions";
    private const string InitialPlanKey = "initial_plan";
    private const string GoalKey = "goal";

    #endregion private

    /// <summary>
    /// Plugin used by the <see cref="FunctionCallingStepwisePlanner"/> to interact with the caller.
    /// </summary>
    public sealed class UserInteraction
    {
        /// <summary>
        /// This function is used by the <see cref="FunctionCallingStepwisePlanner"/> to indicate when the final answer has been found.
        /// </summary>
        /// <param name="answer">The final answer for the plan.</param>
        [SKFunction]
        [Description("This function is used to send the final answer of a plan to the user.")]
        public string SendFinalAnswer([Description("The final answer")] string answer)
        {
            return "Thanks";
        }
    }
}
