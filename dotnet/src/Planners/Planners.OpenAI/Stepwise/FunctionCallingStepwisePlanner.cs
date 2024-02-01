// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Json.More;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// A planner that uses OpenAI function calling in a stepwise manner to fulfill a user goal or question.
/// </summary>
public sealed class FunctionCallingStepwisePlanner
{
    /// <summary>
    /// Initialize a new instance of the <see cref="FunctionCallingStepwisePlanner"/> class.
    /// </summary>
    /// <param name="options">The planner options.</param>
    public FunctionCallingStepwisePlanner(
        FunctionCallingStepwisePlannerOptions? options = null)
    {
        this._options = options ?? new();
        this._generatePlanYaml = this._options.GetInitialPlanPromptTemplate?.Invoke() ?? EmbeddedResource.Read("Stepwise.GeneratePlan.yaml");
        this._stepPrompt = this._options.GetStepPromptTemplate?.Invoke() ?? EmbeddedResource.Read("Stepwise.StepPrompt.txt");
        this._options.ExcludedPlugins.Add(StepwisePlannerPluginName);
    }

    /// <summary>
    /// Execute a plan
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="question">The question to answer</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Result containing the model's response message and chat history.</returns>
    public Task<FunctionCallingStepwisePlannerResult> ExecuteAsync(
        Kernel kernel,
        string question,
        CancellationToken cancellationToken = default)
    {
        var logger = kernel.LoggerFactory.CreateLogger(this.GetType()) ?? NullLogger.Instance;

        return PlannerInstrumentation.InvokePlanAsync(
            static (FunctionCallingStepwisePlanner plan, Kernel kernel, string? question, CancellationToken cancellationToken)
                => plan.ExecuteCoreAsync(kernel, question!, cancellationToken),
            this, kernel, question, logger, cancellationToken);
    }

    #region private

    private async Task<FunctionCallingStepwisePlannerResult> ExecuteCoreAsync(
        Kernel kernel,
        string question,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(question);
        Verify.NotNull(kernel);
        IChatCompletionService chatCompletion = kernel.GetRequiredService<IChatCompletionService>();
        ILoggerFactory loggerFactory = kernel.LoggerFactory;
        ILogger logger = loggerFactory.CreateLogger(this.GetType()) ?? NullLogger.Instance;
        var promptTemplateFactory = new KernelPromptTemplateFactory(loggerFactory);
        var stepExecutionSettings = this._options.ExecutionSettings ?? new OpenAIPromptExecutionSettings();

        // Clone the kernel so that we can add planner-specific plugins without affecting the original kernel instance
        var clonedKernel = kernel.Clone();
        clonedKernel.ImportPluginFromType<UserInteraction>();

        // Create and invoke a kernel function to generate the initial plan
        var initialPlan = await this.GeneratePlanAsync(question, clonedKernel, logger, cancellationToken).ConfigureAwait(false);

        var chatHistoryForSteps = await this.BuildChatHistoryForStepAsync(question, initialPlan, clonedKernel, promptTemplateFactory, cancellationToken).ConfigureAwait(false);

        for (int i = 0; i < this._options.MaxIterations; i++)
        {
            // sleep for a bit to avoid rate limiting
            if (i > 0)
            {
                await Task.Delay(this._options.MinIterationTimeMs, cancellationToken).ConfigureAwait(false);
            }

            // For each step, request another completion to select a function for that step
            chatHistoryForSteps.AddUserMessage(StepwiseUserMessage);
            var chatResult = await this.GetCompletionWithFunctionsAsync(chatHistoryForSteps, clonedKernel, chatCompletion, stepExecutionSettings, logger, cancellationToken).ConfigureAwait(false);
            chatHistoryForSteps.Add(chatResult);

            // Check for function response
            if (!this.TryGetFunctionResponse(chatResult, out IReadOnlyList<OpenAIFunctionToolCall>? functionResponses, out string? functionResponseError))
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
            foreach (OpenAIFunctionToolCall functionResponse in functionResponses)
            {
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
            }

            // Look up function in kernel
            foreach (OpenAIFunctionToolCall functionResponse in functionResponses)
            {
                if (clonedKernel.Plugins.TryGetFunctionAndArguments(functionResponse, out KernelFunction? pluginFunction, out KernelArguments? arguments))
                {
                    try
                    {
                        // Execute function and add to result to chat history
                        var result = (await clonedKernel.InvokeAsync(pluginFunction, arguments, cancellationToken).ConfigureAwait(false)).GetValue<object>();
                        chatHistoryForSteps.AddMessage(AuthorRole.Tool, ParseObjectAsString(result), metadata: new Dictionary<string, object?>(1) { { OpenAIChatMessageContent.ToolIdProperty, functionResponse.Id } });
                    }
                    catch (Exception ex) when (!ex.IsCriticalException())
                    {
                        chatHistoryForSteps.AddMessage(AuthorRole.Tool, ex.Message, metadata: new Dictionary<string, object?>(1) { { OpenAIChatMessageContent.ToolIdProperty, functionResponse.Id } });
                        chatHistoryForSteps.AddUserMessage($"Failed to execute function {functionResponse.FullyQualifiedName}. Try something else!");
                    }
                }
                else
                {
                    chatHistoryForSteps.AddUserMessage($"Function {functionResponse.FullyQualifiedName} does not exist in the kernel. Try something else!");
                }
            }
        }

        // We've completed the max iterations, but the model hasn't returned a final answer.
        return new FunctionCallingStepwisePlannerResult
        {
            FinalAnswer = string.Empty,
            ChatHistory = chatHistoryForSteps,
            Iterations = this._options.MaxIterations,
        };
    }

    private async Task<ChatMessageContent> GetCompletionWithFunctionsAsync(
        ChatHistory chatHistory,
        Kernel kernel,
        IChatCompletionService chatCompletion,
        OpenAIPromptExecutionSettings openAIExecutionSettings,
        ILogger logger,
        CancellationToken cancellationToken)
    {
        openAIExecutionSettings.ToolCallBehavior = ToolCallBehavior.EnableKernelFunctions;

        await this.ValidateTokenCountAsync(chatHistory, kernel, logger, openAIExecutionSettings, cancellationToken).ConfigureAwait(false);
        return await chatCompletion.GetChatMessageContentAsync(chatHistory, openAIExecutionSettings, kernel, cancellationToken).ConfigureAwait(false);
    }

    private async Task<string> GetFunctionsManualAsync(Kernel kernel, ILogger logger, CancellationToken cancellationToken)
    {
        return await kernel.Plugins.GetJsonSchemaFunctionsManualAsync(this._options, null, logger, false, OpenAIFunction.NameSeparator, cancellationToken).ConfigureAwait(false);
    }

    // Create and invoke a kernel function to generate the initial plan
    private async Task<string> GeneratePlanAsync(string question, Kernel kernel, ILogger logger, CancellationToken cancellationToken)
    {
        var generatePlanFunction = kernel.CreateFunctionFromPromptYaml(this._generatePlanYaml);
        string functionsManual = await this.GetFunctionsManualAsync(kernel, logger, cancellationToken).ConfigureAwait(false);
        var generatePlanArgs = new KernelArguments
        {
            [NameDelimiterKey] = OpenAIFunction.NameSeparator,
            [AvailableFunctionsKey] = functionsManual,
            [GoalKey] = question
        };
        var generatePlanResult = await kernel.InvokeAsync(generatePlanFunction, generatePlanArgs, cancellationToken).ConfigureAwait(false);
        return generatePlanResult.GetValue<string>() ?? throw new KernelException("Failed get a completion for the plan.");
    }

    private async Task<ChatHistory> BuildChatHistoryForStepAsync(
        string goal,
        string initialPlan,
        Kernel kernel,
        KernelPromptTemplateFactory promptTemplateFactory,
        CancellationToken cancellationToken)
    {
        var chatHistory = new ChatHistory();

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

    private bool TryGetFunctionResponse(ChatMessageContent chatMessage, [NotNullWhen(true)] out IReadOnlyList<OpenAIFunctionToolCall>? functionResponses, out string? errorMessage)
    {
        OpenAIChatMessageContent? openAiChatMessage = chatMessage as OpenAIChatMessageContent;
        Verify.NotNull(openAiChatMessage, nameof(openAiChatMessage));

        functionResponses = null;
        errorMessage = null;
        try
        {
            functionResponses = openAiChatMessage.GetOpenAIFunctionToolCalls();
        }
        catch (JsonException)
        {
            errorMessage = "That function call is invalid. Try something else!";
        }

        return functionResponses is { Count: > 0 };
    }

    private bool TryFindFinalAnswer(OpenAIFunctionToolCall functionResponse, out string finalAnswer, out string? errorMessage)
    {
        finalAnswer = string.Empty;
        errorMessage = null;

        if (functionResponse.PluginName == "UserInteraction" && functionResponse.FunctionName == "SendFinalAnswer")
        {
            if (functionResponse.Arguments is { Count: > 0 } arguments && arguments.TryGetValue("answer", out object? valueObj))
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
        if (this._options.MaxPromptTokens is not null)
        {
            string functionManual = string.Empty;

            // If using functions, get the functions manual to include in token count estimate
            if (openAIExecutionSettings.ToolCallBehavior == ToolCallBehavior.EnableKernelFunctions)
            {
                functionManual = await this.GetFunctionsManualAsync(kernel, logger, cancellationToken).ConfigureAwait(false);
            }

            var tokenCount = chatHistory.GetTokenCount(additionalMessage: functionManual);
            if (tokenCount >= this._options.MaxPromptTokens)
            {
                throw new KernelException("ChatHistory is too long to get a completion. Try reducing the available functions.");
            }
        }
    }

    /// <summary>
    /// The options for the planner
    /// </summary>
    private readonly FunctionCallingStepwisePlannerOptions _options;

    /// <summary>
    /// The prompt YAML for generating the initial stepwise plan.
    /// </summary>
    private readonly string _generatePlanYaml;

    /// <summary>
    /// The prompt (system message) for performing the steps.
    /// </summary>
    private readonly string _stepPrompt;

    /// <summary>
    /// The name to use when creating semantic functions that are restricted from plan creation
    /// </summary>
    private const string StepwisePlannerPluginName = "StepwisePlanner_Excluded";

    /// <summary>
    /// The user message to add to the chat history for each step of the plan.
    /// </summary>
    private const string StepwiseUserMessage = "Perform the next step of the plan if there is more work to do. When you have reached a final answer, use the UserInteraction-SendFinalAnswer function to communicate this back to the user.";

    // Context variable keys
    private const string AvailableFunctionsKey = "available_functions";
    private const string InitialPlanKey = "initial_plan";
    private const string GoalKey = "goal";
    private const string NameDelimiterKey = "name_delimiter";

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
#pragma warning disable IDE0060 // Remove unused parameter. The parameter is purely an indication to the LLM and is not intended to be used.
        public string SendFinalAnswer([Description("The final answer")] string answer)
#pragma warning restore IDE0060
        {
            return "Thanks";
        }
    }
}
