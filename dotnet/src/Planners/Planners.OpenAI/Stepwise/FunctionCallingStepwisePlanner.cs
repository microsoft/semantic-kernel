// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Json.More;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;
using Microsoft.SemanticKernel.Functions.OpenAPI.Model;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of Plan
namespace Microsoft.SemanticKernel.Planning;
#pragma warning restore IDE0130

/// <summary>
/// A planner that uses OpenAI function calling in a stepwise manner to fulfill a user goal or question.
/// </summary>
public sealed class FunctionCallingStepwisePlanner
{
    /// <summary>
    /// Initialize a new instance of the <see cref="FunctionCallingStepwisePlanner"/> class.
    /// </summary>
    /// <param name="config">The planner configuration.</param>
    public FunctionCallingStepwisePlanner(
        FunctionCallingStepwisePlannerConfig? config = null)
    {
        this.Config = config ?? new();
        this._stepPrompt = this.Config.GetStepPromptTemplate?.Invoke() ?? EmbeddedResource.Read("Stepwise.StepPrompt.txt");
        this.Config.ExcludedPlugins.Add(RestrictedPluginName);
    }

    /// <summary>
    /// Execute a plan
    /// </summary>
    /// <param name="question">The question to answer</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Result containing the model's response message and chat history.</returns>
    public async Task<FunctionCallingStepwisePlannerResult> ExecuteAsync(
        string question,
        Kernel kernel,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(question);
        Verify.NotNull(kernel);
        IChatCompletion chatCompletion = kernel.GetService<IChatCompletion>();
        ILoggerFactory loggerFactory = kernel.GetService<ILoggerFactory>();
        ILogger logger = loggerFactory.CreateLogger(this.GetType());
        var promptTemplateFactory = new KernelPromptTemplateFactory(loggerFactory);
        var stepExecutionSettings = this.Config.ExecutionSettings ?? new OpenAIPromptExecutionSettings();

        // Set max tokens on request settings. Should be minimum of model settings max tokens and planner config max completion tokens
        //this._executionSettings.MaxTokens = Math.Min(this.Config.MaxCompletionTokens, this._executionSettings.MaxTokens ?? int.MaxValue);

        // Clone the kernel and modify it to add the final answer function
        var clonedKernel = kernel.Clone();
        clonedKernel.ImportPluginFromObject<UserInteraction>();

        // Create and invoke a kernel function to generate the initial plan
        var initialPlan = await this.GeneratePlanAsync(question, clonedKernel, logger, cancellationToken).ConfigureAwait(false);

        var chatHistoryForSteps = await this.BuildChatHistoryForStepAsync(question, initialPlan, clonedKernel, chatCompletion, promptTemplateFactory, cancellationToken).ConfigureAwait(false);

        for (int i = 0; i < this.Config.MaxIterations; i++)
        {
            // sleep for a bit to avoid rate limiting
            if (i > 0)
            {
                await Task.Delay(this.Config.MinIterationTimeMs, cancellationToken).ConfigureAwait(false);
            }

            // For each step, request another completion to select a function for that step
            chatHistoryForSteps.AddUserMessage(StepwiseUserMessage);
            var chatResult = await this.GetCompletionWithFunctionsAsync(chatHistoryForSteps, clonedKernel, chatCompletion, stepExecutionSettings, logger, cancellationToken).ConfigureAwait(false);
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
            if (clonedKernel.Plugins.TryGetFunctionAndArguments(functionResponse, out KernelFunction? pluginFunction, out KernelArguments? arguments))
            {
                try
                {
                    // Execute function and add to result to chat history
                    var result = (await clonedKernel.InvokeAsync(pluginFunction, arguments, cancellationToken).ConfigureAwait(false)).GetValue<object>();
                    chatHistoryForSteps.AddFunctionMessage(ParseObjectAsString(result), functionResponse.FullyQualifiedName);
                }
                catch (KernelException)
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
    Kernel kernel,
    IChatCompletion chatCompletion,
    OpenAIPromptExecutionSettings openAIExecutionSettings,
    ILogger logger,
    CancellationToken cancellationToken)
    {
        openAIExecutionSettings.FunctionCallBehavior = FunctionCallBehavior.EnableKernelFunctions;

        await this.ValidateTokenCountAsync(chatHistory, kernel, logger, openAIExecutionSettings, cancellationToken).ConfigureAwait(false);
        return (await chatCompletion.GetChatCompletionsAsync(chatHistory, openAIExecutionSettings, kernel, cancellationToken).ConfigureAwait(false))[0];
    }

    private async Task<string> GetFunctionsManualAsync(Kernel kernel, ILogger logger, CancellationToken cancellationToken)
    {
        return await kernel.Plugins.GetJsonSchemaFunctionsManualAsync(this.Config, null, logger, false, cancellationToken).ConfigureAwait(false);
    }

    // Create and invoke a kernel function to generate the initial plan
    private async Task<string> GeneratePlanAsync(string question, Kernel kernel, ILogger logger, CancellationToken cancellationToken)
    {
        var generatePlanFunction = kernel.CreateFunctionFromPromptYaml(EmbeddedResource.Read("Stepwise.GeneratePlan.yaml"));
        string functionsManual = await this.GetFunctionsManualAsync(kernel, logger, cancellationToken).ConfigureAwait(false);
        var generatePlanArgs = new KernelArguments
        {
            [AvailableFunctionsKey] = functionsManual,
            [GoalKey] = question
        };
        var generatePlanResult = await kernel.InvokeAsync(generatePlanFunction, generatePlanArgs, cancellationToken).ConfigureAwait(false);
        return generatePlanResult.GetValue<string>() ?? string.Empty; //  TODO: throw if empty?
    }

    private async Task<ChatHistory> BuildChatHistoryForStepAsync(
        string goal,
        string initialPlan,
        Kernel kernel,
        IChatCompletion chatCompletion,
        KernelPromptTemplateFactory promptTemplateFactory,
        CancellationToken cancellationToken)
    {
        var chatHistory = chatCompletion.CreateNewChat();

        // Add system message with context about the initial goal/plan
        var arguments = new KernelArguments
        {
            [GoalKey] = goal,
            [InitialPlanKey] = initialPlan
        };
        var systemMessage = await promptTemplateFactory.Create(new PromptTemplateConfig(this._stepPrompt)).RenderAsync(kernel, arguments, cancellationToken).ConfigureAwait(false);

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

    private async Task ValidateTokenCountAsync(
        ChatHistory chatHistory,
        Kernel kernel,
        ILogger logger,
        OpenAIPromptExecutionSettings openAIExecutionSettings,
        CancellationToken cancellationToken)
    {
        string functionManual = string.Empty;

        // If using functions, get the functions manual to include in token count estimate
        if (openAIExecutionSettings.FunctionCallBehavior == FunctionCallBehavior.EnableKernelFunctions)
        {
            functionManual = await this.GetFunctionsManualAsync(kernel, logger, cancellationToken).ConfigureAwait(false);
        }

        var tokenCount = chatHistory.GetTokenCount(additionalMessage: functionManual);
        if (tokenCount >= this.Config.MaxPromptTokens)
        {
            throw new KernelException("ChatHistory is too long to get a completion. Try reducing the available functions.");
        }
    }

    /// <summary>
    /// The configuration for the StepwisePlanner
    /// </summary>
    private FunctionCallingStepwisePlannerConfig Config { get; }

    /// <summary>
    /// The prompt (system message) for performing the steps.
    /// </summary>
    private readonly string _stepPrompt;

    /// <summary>
    /// The user message to add to the chat history for each step of the plan.
    /// </summary>
    private const string StepwiseUserMessage = "Perform the next step of the plan if there is more work to do. When you have reached a final answer, use the UserInteraction_SendFinalAnswer function to communicate this back to the user.";

    // Context variable keys
    private const string AvailableFunctionsKey = "available_functions";
    private const string InitialPlanKey = "initial_plan";
    private const string GoalKey = "goal";

    /// <summary>
    /// The name to use when creating semantic functions that are restricted from plan creation
    /// </summary>
    private const string RestrictedPluginName = "FunctionCallingStepwisePlanner_Excluded"; // TODO: too long?

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
        [KernelFunction]
        [Description("This function is used to send the final answer of a plan to the user.")]
        public string SendFinalAnswer([Description("The final answer")] string answer)
        {
            return "Thanks";
        }
    }
}
