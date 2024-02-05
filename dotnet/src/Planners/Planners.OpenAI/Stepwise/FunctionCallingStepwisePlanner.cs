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
    /// <param name="config">The planner configuration.</param>
    public FunctionCallingStepwisePlanner(
        FunctionCallingStepwisePlannerConfig? config = null)
    {
        this.Config = config ?? new();
        this._generatePlanYaml = this.Config.GetPromptTemplate?.Invoke() ?? EmbeddedResource.Read("Stepwise.GeneratePlan.yaml");
        this._stepPrompt = this.Config.GetStepPromptTemplate?.Invoke() ?? EmbeddedResource.Read("Stepwise.StepPrompt.txt");
        this.Config.ExcludedPlugins.Add(StepwisePlannerPluginName);
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
        var stepExecutionSettings = this.Config.ExecutionSettings ?? new OpenAIPromptExecutionSettings();

        // Clone the kernel so that we can add planner-specific plugins without affecting the original kernel instance
        var clonedKernel = kernel.Clone();

        // The final answer variables are set when the UserInteraction plugin is invoked
        bool finalAnswerFound = false;
        string finalAnswer = string.Empty;

        // Import the UserInteraction plugin to the kernel
        var userInteraction = new UserInteraction((answer) => { finalAnswerFound = true; finalAnswer = answer; });
        clonedKernel.ImportPluginFromObject(userInteraction);

        // Create and invoke a kernel function to generate the initial plan
        var initialPlan = await this.GeneratePlanAsync(question, clonedKernel, logger, cancellationToken).ConfigureAwait(false);

        var chatHistoryForSteps = await this.BuildChatHistoryForStepAsync(question, initialPlan, clonedKernel, promptTemplateFactory, cancellationToken).ConfigureAwait(false);

        for (int iteration = 0; iteration < this.Config.MaxIterations; /* iteration is incremented within the loop */)
        {
            // sleep for a bit to avoid rate limiting
            if (iteration > 0)
            {
                await Task.Delay(this.Config.MinIterationTimeMs, cancellationToken).ConfigureAwait(false);
            }

            // For each step, request another completion to select a function for that step
            chatHistoryForSteps.AddUserMessage(StepwiseUserMessage);
            var chatResult = await this.GetCompletionWithFunctionsAsync(iteration, chatHistoryForSteps, clonedKernel, chatCompletion, stepExecutionSettings, logger, cancellationToken).ConfigureAwait(false);
            chatHistoryForSteps.Add(chatResult);

            // Increment iteration based on the number of model round trips that occurred as a result of the request
            object? value = null;
            chatResult.Metadata?.TryGetValue("ModelIterations", out value); // TODO: implement this, and also ToolInvocations?
            if (value is not null and int)
            {
                iteration += (int)value;
            }
            else
            {
                // Could not find iterations in metadata, so assume just one
                iteration++;
            }

            // Check for final answer
            if (finalAnswerFound)
            {
                // Success! we found a final answer, so return the planner result
                return new FunctionCallingStepwisePlannerResult
                {
                    FinalAnswer = finalAnswer,
                    ChatHistory = chatHistoryForSteps,
                    Iterations = iteration,
                };
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

    private async Task<ChatMessageContent> GetCompletionWithFunctionsAsync(
        int iterationsCompleted,
        ChatHistory chatHistory,
        Kernel kernel,
        IChatCompletionService chatCompletion,
        OpenAIPromptExecutionSettings openAIExecutionSettings,
        ILogger logger,
        CancellationToken cancellationToken)
    {
        openAIExecutionSettings.ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions;

        // TODO: set filters
        // int iterationsRemaining = this.Config.MaxIterations - iterationsCompleted;
        // openAIExecutionSettings.ToolCallBehavior.PreInvokeCallback = (iteration, _, _) => { return (iteration < iterationsRemaining); };
        // openAIExecutionSettings.ToolCallBehavior.Filters.Add(new FinalAnswerFilter());

        await this.ValidateTokenCountAsync(chatHistory, kernel, logger, openAIExecutionSettings, cancellationToken).ConfigureAwait(false);
        return await chatCompletion.GetChatMessageContentAsync(chatHistory, openAIExecutionSettings, kernel, cancellationToken).ConfigureAwait(false);
    }

    private async Task<string> GetFunctionsManualAsync(Kernel kernel, ILogger logger, CancellationToken cancellationToken)
    {
        return await kernel.Plugins.GetJsonSchemaFunctionsManualAsync(this.Config, null, logger, false, cancellationToken).ConfigureAwait(false);
    }

    // Create and invoke a kernel function to generate the initial plan
    private async Task<string> GeneratePlanAsync(string question, Kernel kernel, ILogger logger, CancellationToken cancellationToken)
    {
        var generatePlanFunction = kernel.CreateFunctionFromPromptYaml(this._generatePlanYaml);
        string functionsManual = await this.GetFunctionsManualAsync(kernel, logger, cancellationToken).ConfigureAwait(false);
        var generatePlanArgs = new KernelArguments
        {
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

    private async Task ValidateTokenCountAsync(
        ChatHistory chatHistory,
        Kernel kernel,
        ILogger logger,
        OpenAIPromptExecutionSettings openAIExecutionSettings,
        CancellationToken cancellationToken)
    {
        string functionManual = string.Empty;

        // If using functions, get the functions manual to include in token count estimate
        if (openAIExecutionSettings.ToolCallBehavior == ToolCallBehavior.EnableKernelFunctions)
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
        private readonly Action<string> _setCompleted;

        /// <summary>
        /// Constructs the <see cref="UserInteraction"/> object with a specified callback to indicate the plan completion.
        /// </summary>
        /// <param name="setCompleted">Delegate to tell the planner that the plan is completed and a final answer has been found.</param>
        public UserInteraction(Action<string> setCompleted)
        {
            this._setCompleted = setCompleted;
        }

        /// <summary>
        /// This function is used by the <see cref="FunctionCallingStepwisePlanner"/> to indicate when the final answer has been found.
        /// </summary>
        /// <param name="answer">The final answer for the plan.</param>
        [KernelFunction]
        [Description("This function is used to send the final answer of a plan to the user.")]
        public string SendFinalAnswer([Description("The final answer")] string answer)
        {
            this._setCompleted(answer);
            return "Thanks";
        }
    }

    public sealed class FinalAnswerFilter : IToolFilter
    {
        public void OnToolInvoked(ToolInvokedContext context)
        {
            throw new NotImplementedException();
        }

        public void OnToolInvoking(ToolInvokingContext context)
        {
            throw new NotImplementedException();
        }
    }
}
