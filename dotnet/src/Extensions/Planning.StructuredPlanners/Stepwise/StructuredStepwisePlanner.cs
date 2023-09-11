// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Planning.Structured.Stepwise;

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Globalization;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using AI.ChatCompletion;
using Azure.AI.OpenAI;
using Connectors.AI.OpenAI.FunctionCalling;
using Connectors.AI.OpenAI.FunctionCalling.Extensions;
using Diagnostics;
using Microsoft.Extensions.Logging;
using Orchestration;
using SkillDefinition;
using TemplateEngine.Prompt;


/// <summary>
///  Stepwise planner that uses the OpenAI chat completion function calling API to achieve a goal in a step by step manner. 
/// </summary>
public class StructuredStepwisePlanner : IStructuredPlanner
{

    /// <summary>
    ///  Create a new instance of the StepwisePlanner
    /// </summary>
    /// <param name="kernel"></param>
    /// <param name="config"></param>
    /// <param name="prompt"></param>
    public StructuredStepwisePlanner(
        IKernel kernel,
        StructuredPlannerConfig? config = null,
        string? prompt = null)
    {
        Verify.NotNull(kernel);
        _kernel = kernel;

        Config = config ?? new StructuredPlannerConfig();
        Config.ExcludedSkills.Add(RestrictedSkillName);

        _promptTemplate = prompt ?? EmbeddedResource.Read("Prompts.Stepwise.skprompt.txt");

        _executeFunction = _kernel.ImportSkill(this, RestrictedSkillName);

        _context = _kernel.CreateNewContext();
        _logger = _kernel.LoggerFactory.CreateLogger(nameof(StructuredStepwisePlanner));

    }


    /// <inheritdoc />
    public Task<Plan> CreatePlanAsync(string goal, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrEmpty(goal))
        {
            throw new SKException("The goal specified is empty");
        }
        Plan planStep = new(_executeFunction["ExecutePlan"]);

        planStep.Parameters.Set("problem", goal);

        planStep.Outputs.Add("stepCount");
        planStep.Outputs.Add("skillCount");
        planStep.Outputs.Add("stepsTaken");

        Plan plan = new(goal);

        plan.AddSteps(planStep);

        return Task.FromResult(plan);
    }


    [SKFunction] [SKName("ExecutePlan")] [Description("Execute a plan")]
    public async Task<SKContext> ExecutePlanAsync(
        [Description("The problem to solve")] string problem,
        SKContext context,
        CancellationToken token)
    {

        if (string.IsNullOrEmpty(problem))
        {
            context.Variables.Update("Question not found.");
            return context;
        }

        List<StepwiseFunctionCallResult> stepsTaken = new();
        var lastStep = new StepwiseFunctionCallResult();

        _chatHistory = await InitializeChatHistoryAsync(_chatHistory, problem).ConfigureAwait(false);

        for (var i = 0; i < Config.MaxIterations; i++)
        {
            var chatCompletion = _kernel.GetService<IChatCompletion>();

            if (i > 0)
            {
                await Task.Delay(Config.MinIterationTimeMs, token).ConfigureAwait(false);
            }

            context.Variables.Set("stepsTaken", string.Join("\n", stepsTaken.Select((result, step) => result.ToStepResult(step + 1))));
            var nextStep = await StepAsync(context, stepsTaken, _chatHistory, chatCompletion, token).ConfigureAwait(false);

            if (nextStep == null)
            {
                throw new InvalidOperationException("Failed to parse step from response text.");
            }

            var finalContext = TryGetFinalAnswer(nextStep, context, stepsTaken);

            if (finalContext is not null)
            {
                return finalContext;
            }

            nextStep = AddNextStep(stepsTaken, nextStep, lastStep, _chatHistory, _chatHistory.Messages.Count);
            await Task.Delay(Config.MinIterationTimeMs, token).ConfigureAwait(false); // A
            lastStep = nextStep;
        }

        context.Variables.Update($"Result not found, review _stepsTaken to see what happened.\n{JsonSerializer.Serialize(stepsTaken)}");

        return context;
    }


    private async Task<StepwiseFunctionCallResult?> StepAsync(SKContext context, List<StepwiseFunctionCallResult> stepsTaken, ChatHistory chatHistory, IChatCompletion chatCompletion, CancellationToken token)
    {
        var tokenCount = GetChatHistoryTokens(chatHistory);

        if (tokenCount >= Config.MaxTokens)
        {
            chatHistory = await TrimChatHistoryAsync(tokenCount, chatHistory, chatCompletion, stepsTaken).ConfigureAwait(false);
        }
        var requestSettings = GetRequestSettings(context);
        return await GetNextStepAsync(chatHistory, chatCompletion, requestSettings, token).ConfigureAwait(false);
    }


    private Task<ChatHistory> TrimChatHistoryAsync(int tokenCount, ChatHistory chatHistory, IChatCompletion chatCompletion, List<StepwiseFunctionCallResult> stepsTaken)
    {
        _logger?.LogInformation("Trimming chat history");
        var removalIndex = chatHistory.Messages.Count;
        List<ChatMessageBase> userMessages = chatHistory.Messages.Where(m => m.Role == AuthorRole.User).ToList();
        Queue<ChatMessageBase> stepwiseFunctionResults = new(chatHistory.Messages.Where(m => m.Role == AuthorRole.Assistant));

        List<(ChatMessageBase AssistantMessage, ChatMessageBase UserMessage)> stepPairs =
            Enumerable.Range(0, userMessages.Count).Select(i => (stepwiseFunctionResults.ElementAt(i), userMessages.ElementAt(i))).ToList();

        var messagesRemoved = 0;

        while (tokenCount >= Config.MaxTokens && chatHistory.Messages.Count > removalIndex)
        {
            // Check if a new step can be added
            if (tokenCount + stepsTaken[stepsTaken.Count - 1].ToString().Length / 4 <= Config.MaxTokens)
            {
                // Add new stepwise function result to chat history
                chatHistory.Messages.RemoveAt(removalIndex);
                chatHistory.AddAssistantMessage(stepsTaken[stepsTaken.Count - 1].ToString());
            }
            else if (stepPairs.Count > 0)
            {
                // Check if the pair can be added without exceeding token limit
                var pair = stepPairs.First();
                stepPairs.RemoveAt(0);

                if (tokenCount + pair.AssistantMessage.Content.Length / 4 + pair.UserMessage.Content.Length / 4 <= Config.MaxTokens)
                {
                    // If pair fits, insert both
                    chatHistory.Messages.Insert(removalIndex, pair.AssistantMessage);
                    chatHistory.Messages.Insert(removalIndex + 1, pair.UserMessage);
                }
                else
                {
                    // If pair doesn't fit, just insert user message
                    chatHistory.Messages.Insert(removalIndex, pair.UserMessage);
                }

                // Update token count   
                tokenCount = GetChatHistoryTokens(chatHistory);
            }

            // Removal during every cycle for next iteration
            if (chatHistory.Messages.Count <= removalIndex)
            {
                continue;
            }
            chatHistory.Messages.RemoveAt(removalIndex);
            messagesRemoved++; // Increment messages removed
            tokenCount = GetChatHistoryTokens(chatHistory);
        }

        return Task.FromResult(chatHistory);
    }


    private async Task<StepwiseFunctionCallResult> GetNextStepAsync(ChatHistory chatHistory, IChatCompletion chatCompletion, FunctionCallRequestSettings requestSettings, CancellationToken token)
    {

        var nextStep = await chatCompletion.GenerateResponseAsync<StepwiseFunctionCallResult>(
                chatHistory,
                requestSettings,
                Config.SerializerOptions,
                s => s.ToFunctionCallResult(), token)
            .ConfigureAwait(false);

        if (nextStep == null)
        {
            throw new InvalidOperationException("Failed to parse step from response text.");
        }

        var assistantMessage = nextStep.ToString();
        _logger?.LogInformation("Assistant message: {AssistantMessage}", assistantMessage);
        Console.WriteLine(assistantMessage);
        _chatHistory.AddAssistantMessage(assistantMessage);

        if (nextStep.FunctionCall == null)
        {
            return nextStep;
        }

        var actionResult = await InvokeActionAsync(nextStep.FunctionCall).ConfigureAwait(false);
        nextStep.FunctionResult = actionResult;
        var userMessage = $"Observation: {actionResult}";
        Console.WriteLine(userMessage);
        chatHistory.AddUserMessage("Observation: " + actionResult);
        return nextStep;
    }


    private SKContext? TryGetFinalAnswer(StepwiseFunctionCallResult step, SKContext context, List<StepwiseFunctionCallResult> stepsTaken)
    {
        if (!string.IsNullOrEmpty(step.FinalAnswer))
        {
            _logger?.LogInformation("Final Answer: {FinalAnswer}", step.FinalAnswer);
            context.Variables.Update(step.FinalAnswer);
            stepsTaken.Add(step);
            AddExecutionStatsToContext(stepsTaken, context, stepsTaken.Count);
            return context;
        }
        return null;
    }


    private StepwiseFunctionCallResult AddNextStep(List<StepwiseFunctionCallResult> stepsTaken, StepwiseFunctionCallResult step, StepwiseFunctionCallResult lastStep, ChatHistory chatHistory, int startingMessageCount)
    {
        if (lastStep.FunctionCall == null)
        {
            stepsTaken.Add(step);
            return step;
        }

        if (step.FunctionCall != null
            && step.FunctionCall.Function.Equals(lastStep.FunctionCall.Function, StringComparison.Ordinal)
            && step.FunctionCall.Parameters.Equals(lastStep.FunctionCall.Parameters))
        {
            lastStep.FunctionCall = step.FunctionCall;
            lastStep.FunctionResult += step.FunctionResult;

            if (chatHistory.Messages.Count > startingMessageCount)
            {
                chatHistory.Messages.RemoveAt(chatHistory.Messages.Count - 1);
            }

            step = lastStep;
        }

        else
        {
            _logger.LogInformation("Thought: {Thought}", step.Thought);
            stepsTaken.Add(step);
        }

        return step;
    }


    private async Task<string> InvokeActionAsync(FunctionCallResult functionCall)
    {
        _context.Skills.TryGetFunction(functionCall, out var targetFunction);

        if (targetFunction == null)
        {
            throw new SKException($"The function '{functionCall.Function}' was not found.");
        }

        try
        {
            var result = await targetFunction.InvokeAsync(functionCall.FunctionParameters()).ConfigureAwait(false);

            _logger.LogTrace("Invoked {FunctionName}. Result: {Result}", targetFunction.Name, result.Result);

            return result.Result;
        }
        catch (Exception e) when (!e.IsCriticalException())
        {
            this._logger?.LogError(e, "Something went wrong in system step: {Plugin}.{Function}. Error: {Error}", targetFunction.SkillName, targetFunction.Name, e.Message);
            throw;
        }
    }


    private async Task<ChatHistory> InitializeChatHistoryAsync(ChatHistory chatHistory, string request)
    {

        var systemContext = this._kernel.CreateNewContext();
        string systemMessage = await this.GetSystemMessage(systemContext).ConfigureAwait(false);

        chatHistory.AddSystemMessage(systemMessage);
        chatHistory.AddUserMessage(request);

        return chatHistory;
    }


    private int GetChatHistoryTokens(ChatHistory chatHistory)
    {
        var messages = string.Join("\n", chatHistory.Messages);
        var tokenCount = messages.Length / 4;
        return tokenCount;
    }


    private Task<string> GetSystemMessage(SKContext context) => _promptRenderer.RenderAsync(_promptTemplate, context);


    private static void AddExecutionStatsToContext(List<StepwiseFunctionCallResult> stepsTaken, SKContext context, int iteration)
    {
        context.Variables.Set("stepCount", stepsTaken.Count.ToString(CultureInfo.InvariantCulture));
        context.Variables.Set("stepsTaken", string.Join("\n", stepsTaken.Select((result, step) => result.ToStepResult(step + 1))));
        context.Variables.Set("iterations", iteration.ToString(CultureInfo.InvariantCulture));

        Dictionary<string, int> functionCounts = new();

        foreach (var step in stepsTaken.Where(step => !string.IsNullOrEmpty(step.FunctionCall?.Function)))
        {
            if (!functionCounts.TryGetValue(step.FunctionCall!.Function, out var currentCount))
            {
                currentCount = 0;
            }
            functionCounts[step.FunctionCall.Function] = currentCount + 1;
        }

        var functionCallListWithCounts = string.Join(", ", functionCounts.Keys.Select(func =>
            $"{func}({functionCounts[func]})"));

        var functionCallsStr = functionCounts.Values.Sum().ToString(CultureInfo.InvariantCulture);

        context.Variables.Set("functionCount", $"{functionCallsStr} ({functionCallListWithCounts})");
        Console.WriteLine(string.Join("\n", context.Variables.Select(v => $"{v.Key}: {v.Value}")));
    }


    private FunctionCallRequestSettings GetRequestSettings(SKContext context)
    {
        List<FunctionDefinition> callableFunctions = context.Skills.GetFunctionDefinitions(Config.ExcludedSkills, Config.ExcludedFunctions).ToList();
        callableFunctions.Add(StepwisePlan);
        return new FunctionCallRequestSettings
        {
            CallableFunctions = callableFunctions,
            FunctionCall = StepwisePlan,
            MaxTokens = Config.MaxTokens,
            Temperature = 0.0,
            StopSequences = new List<string>()
            {
                "Observation:",
                "Thought:"
            }
        };
    }


    /// <summary>
    /// The configuration for the StepwisePlanner
    /// </summary>
    private StructuredPlannerConfig Config { get; }

    // Context used to access the list of functions in the kernel
    private readonly SKContext _context;
    private readonly IKernel _kernel;
    private readonly ILogger _logger;
    private readonly IDictionary<string, ISKFunction> _executeFunction;
    private readonly PromptTemplateEngine _promptRenderer = new();

    private ChatHistory _chatHistory = new();
    private readonly string _promptTemplate;

    /// <summary>
    /// The name to use when creating semantic functions that are restricted from plan creation
    /// </summary>
    private const string RestrictedSkillName = "StepwisePlanner_Excluded";

    private static FunctionDefinition StepwisePlan => new()
    {
        Name = "stepwise_function_call",
        Description = "Take the next step to solve the problem",
        Parameters = BinaryData.FromObjectAsJson(
            new
            {
                Type = "object",
                Properties = new
                {
                    Step = new
                    {
                        Type = "object",
                        Description = "Step data structure",
                        Properties = new
                        {
                            Function_Call = new
                            {
                                Type = "object",
                                Description = "the function call to make",
                                Properties = new
                                {
                                    Function = new
                                    {
                                        Type = "string",
                                        Description = "Name of the function chosen"
                                    },
                                    Parameters = new
                                    {
                                        Type = "array",
                                        Description = "Parameter values",
                                        Items = new
                                        {
                                            Type = "object",
                                            Description = "Parameter value",
                                            Properties = new
                                            {
                                                Name = new
                                                {
                                                    Type = "string",
                                                    Description = "Parameter name"
                                                },
                                                Value = new
                                                {
                                                    Type = "string",
                                                    Description = "Parameter value"
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            Thought = new
                            {
                                Type = "string",
                                Description = "Current thought context"
                            },
                            Final_Answer = new
                            {
                                Type = "string",
                                Description = "Final answer if found"
                            }
                        }
                    }
                }
            },
            new JsonSerializerOptions() { PropertyNamingPolicy = JsonNamingPolicy.CamelCase })
    };
}
