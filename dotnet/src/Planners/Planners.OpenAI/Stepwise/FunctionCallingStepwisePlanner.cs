// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Json.More;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI;
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
        // Set up Config and prompt templates
        this.Config = config ?? new();
        this._initialPlanPrompt = this.Config.GetPromptTemplate?.Invoke() ?? EmbeddedResource.Read("Stepwise.InitialPlanPrompt.txt");
        this._stepPrompt = this.Config.GetStepPromptTemplate?.Invoke() ?? EmbeddedResource.Read("Stepwise.StepPrompt.txt");
        this.Config.ExcludedPlugins.Add(RestrictedPluginName);
    }

    /// <summary>
    /// Execute a plan
    /// </summary>
    /// <param name="question">The question to answer</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Result containing the model's response message and chat history.</returns>
    public async Task<FunctionCallingStepwisePlannerResult> ExecuteAsync(
        string question,
        Kernel kernel,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(question);
        Verify.NotNull(kernel);
        IChatCompletion chatCompletion = kernel.GetService<IChatCompletion>();
        ILoggerFactory loggerFactory = kernel.GetService<ILoggerFactory>();
        ILogger logger = loggerFactory.CreateLogger(this.GetType());

        var promptTemplateFactory = new KernelPromptTemplateFactory(loggerFactory);

        // TODO: confirm openai or throw

        //var openAIExecutionSettings = executionSettings as OpenAIPromptExecutionSettings ?? new OpenAIPromptExecutionSettings();
        var openAIExecutionSettings = OpenAIPromptExecutionSettings.FromRequestSettings(executionSettings);

        // Set max tokens on request settings. Should be minimum of model settings max tokens and planner config max completion tokens
        //this._executionSettings.MaxTokens = Math.Min(this.Config.MaxCompletionTokens, this._executionSettings.MaxTokens ?? int.MaxValue);

        // Add the final answer function
        var clonedKernel = kernel.Clone();
        clonedKernel.ImportPluginFromObject(new UserInteraction(), "UserInteraction");

        var executeStepFunction = kernel.CreateFunctionFromMethod(this.ExecuteNextStepAsync);


        // Create and invoke a kernel function to generate the initial plan
        var generatePlanFunction = clonedKernel.CreateFunctionFromPromptYaml(this._yaml);
        //var generatePlanFunction = clonedKernel.CreateFunctionFromPromptYaml(EmbeddedResource.Read("Stepwise.GeneratePlan.yaml"));
        //var generatePlanFunction = clonedKernel.CreateFunctionFromPromptYamlResource("Stepwise.GeneratePlan.yaml");
        var args = new KernelFunctionArguments();
        string functionsManual = await this.GetFunctionsManualAsync(kernel, logger, cancellationToken).ConfigureAwait(false);
        args[AvailableFunctionsKey] = functionsManual;
        args[GoalKey] = question;
        var generatePlanResult = await clonedKernel.InvokeAsync(generatePlanFunction, args, cancellationToken).ConfigureAwait(false);

        var initialPlan = generatePlanResult.GetValue<string>() ?? string.Empty; //  TODO: throw if empty?

        // Request completion for initial plan
        //var chatHistoryForPlan = await this.BuildChatHistoryForInitialPlanAsync(question, clonedKernel, chatCompletion, logger, promptTemplateFactory, cancellationToken).ConfigureAwait(false);
        //openAIExecutionSettings.FunctionCall = OpenAIPromptExecutionSettings.FunctionCallNone;
        //await this.ValidateTokenCountAsync(chatHistoryForPlan, clonedKernel, logger, openAIExecutionSettings, cancellationToken).ConfigureAwait(false);
        //string initialPlan = (await chatCompletion.GenerateMessageAsync(chatHistoryForPlan, openAIExecutionSettings, cancellationToken).ConfigureAwait(false));

        
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
            var chatResult = await this.GetCompletionWithFunctionsAsync(chatHistoryForSteps, clonedKernel, chatCompletion, openAIExecutionSettings, logger, cancellationToken).ConfigureAwait(false);
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
            if (clonedKernel.Plugins.TryGetFunctionAndArguments(functionResponse, out KernelFunction? pluginFunction, out KernelFunctionArguments? arguments))
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

    // PerformStepAsync / ExecuteStepAsync
    [KernelFunction]
    public async Task<IChatResult> ExecuteNextStepAsync(
        [Description("The goal or question to answer")] string question,
        [Description("The step-by-step plan to satisfy the goal")] string initialPlan,
        [Description("The chat history for plan execution")] string chatHistory,
        Kernel kernel,
        //PromptExecutionSettings? executionSettings,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(question);
        Verify.NotNull(kernel);
        IChatCompletion chatCompletion = kernel.GetService<IChatCompletion>();
        ILoggerFactory loggerFactory = kernel.GetService<ILoggerFactory>();
        ILogger logger = loggerFactory.CreateLogger(this.GetType());

        //var openAIExecutionSettings = executionSettings as OpenAIPromptExecutionSettings ?? new OpenAIPromptExecutionSettings();
        //var openAIExecutionSettings = OpenAIPromptExecutionSettings.FromRequestSettings(executionSettings);

        // TODO: get execution settings from kernel?
        var openAIExecutionSettings = new OpenAIPromptExecutionSettings();
        return await this.GetCompletionWithFunctionsAsync(new ChatHistory(), kernel, chatCompletion, openAIExecutionSettings, logger, cancellationToken).ConfigureAwait(false);
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
        openAIExecutionSettings.FunctionCall = OpenAIPromptExecutionSettings.FunctionCallAuto;
        openAIExecutionSettings.Functions = kernel.Plugins.GetFunctionsMetadata().Select(f => f.ToOpenAIFunction()).ToList();

        await this.ValidateTokenCountAsync(chatHistory, kernel, logger, openAIExecutionSettings, cancellationToken).ConfigureAwait(false);
        return (await chatCompletion.GetChatCompletionsAsync(chatHistory, openAIExecutionSettings, cancellationToken).ConfigureAwait(false))[0];
    }

    private async Task<string> GetFunctionsManualAsync(Kernel kernel, ILogger logger, CancellationToken cancellationToken)
    {
        return await kernel.Plugins.GetJsonSchemaFunctionsManualAsync(this.Config, null, logger, false, cancellationToken).ConfigureAwait(false);
    }

    private async Task<ChatHistory> BuildChatHistoryForInitialPlanAsync(
        string goal,
        Kernel kernel,
        IChatCompletion chatCompletion,
        ILogger logger,
        KernelPromptTemplateFactory promptTemplateFactory,
        CancellationToken cancellationToken)
    {
        var chatHistory = chatCompletion.CreateNewChat();

        var arguments = new Dictionary<string, string>();
        string functionsManual = await this.GetFunctionsManualAsync(kernel, logger, cancellationToken).ConfigureAwait(false);
        arguments[AvailableFunctionsKey] = functionsManual;
        string systemMessage = await promptTemplateFactory.Create(new PromptTemplateConfig(this._initialPlanPrompt)).RenderAsync(kernel, arguments, cancellationToken).ConfigureAwait(false);

        chatHistory.AddSystemMessage(systemMessage);
        chatHistory.AddUserMessage(goal);

        return chatHistory;
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
        var arguments = new Dictionary<string, string>();
        arguments[GoalKey] = goal;
        arguments[InitialPlanKey] = initialPlan;
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
        if (openAIExecutionSettings.FunctionCall == OpenAIPromptExecutionSettings.FunctionCallAuto)
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

    // Context used to access the list of functions in the kernel
    //private readonly Kernel _kernel;
    //private readonly IChatCompletion _chatCompletion;
    //private readonly ILogger? _logger;
    //private readonly OpenAIPromptExecutionSettings _executionSettings;

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
    //private readonly KernelPromptTemplateFactory _promptTemplateFactory;

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

    private readonly string _yaml = @"
    template_format: semantic-kernel
    template: |
      <message role=""system"">
      You are an expert at generating plans from a given GOAL. Think step by step and determine a plan to satisfy the specified GOAL using only the FUNCTIONS provided to you. You can also make use of your own knowledge while forming an answer but you must not use functions that are not provided. Once you have come to a final answer, use the UserInteraction_SendFinalAnswer function to communicate this back to the user.

      [FUNCTIONS]

      {{$available_functions}}

      [END FUNCTIONS]

      To create the plan, follow these steps:
      0. Each step should be something that is capable of being done by the list of available functions.
      1. Steps can use output from one or more previous steps as input, if appropriate.
      2. The plan should be as short as possible.
      </message>
      <message role=""user"">{{$goal}}</message>
    description:     Generate a step-by-step plan to satisfy a given goal
    name:            GeneratePlan
    input_parameters:
      - name:          available_functions
        description:   A list of functions that can be used to generate the plan
      - name:          goal
        description:   The goal to satisfy
    execution_settings:
      - model_id:          gpt-4
        temperature:       1.0
        top_p:             0.0
        presence_penalty:  0.0
        frequency_penalty: 0.0
        max_tokens:        256
        stop_sequences:    []
      - model_id:          gpt-3.5
        temperature: 0.0
        top_p:             0.0
        presence_penalty:  0.0
        frequency_penalty: 0.0
        max_tokens:        256
        stop_sequences:    []
";

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
