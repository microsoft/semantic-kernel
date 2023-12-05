// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Planning.Handlebars;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Represents a thread of conversation with an agent.
/// </summary>
public class Thread : IThread
{
    /// <summary>
    /// The agent.
    /// </summary>
    private readonly IAgent _agent;

    /// <summary>
    /// The chat history of this thread.
    /// </summary>
    private readonly ChatHistory _chatHistory;

    /// <summary>
    /// The prompt to use for extracting the user intent.
    /// </summary>
    private const string SystemIntentExtractionPrompt =
        "Rewrite the last messages to reflect the user's intents, taking into consideration the provided chat history. " +
        "The output should be rewritten sentences that describes the user's intent and is understandable outside of the context of the chat history, in a way that will be useful for executing an action. " +
        "Do not try to find an answer, just extract the user intent and all needed information to execute the goal.";

    /// <summary>
    /// The logger.
    /// </summary>
    private readonly ILogger _logger;

    /// <summary>
    /// The arguments to pass to the agent.
    /// </summary>
    private readonly Dictionary<string, object?> _arguments;

    /// <summary>
    /// The name of the caller.
    /// </summary>
    private readonly string _callerName;

    /// <summary>
    /// Gets the chat messages.
    /// </summary>
    public IReadOnlyList<ChatMessageContent> ChatMessages => this._chatHistory;

    /// <summary>
    /// Initializes a new instance of the <see cref="Thread"/> class.
    /// </summary>
    /// <param name="agent">The agent.</param>
    /// <param name="callerName">The caller name.</param>
    /// <param name="arguments">The arguments to pass.</param>
    internal Thread(IAgent agent,
        string callerName = "User",
        Dictionary<string, object?> arguments = null)
    {
        this._logger = agent.Kernel.LoggerFactory.CreateLogger<Thread>();
        this._agent = agent;
        this._callerName = callerName;
        this._arguments = arguments ?? new Dictionary<string, object?>();
        this._chatHistory = new ChatHistory(this._agent.Description!);

        this._chatHistory.AddSystemMessage(this._agent.Instructions);
    }

    /// <summary>
    /// Invoke the agent completion.
    /// </summary>
    /// <returns></returns>
    public async Task<string> InvokeAsync(string userMessage)
    {
        this._logger.LogInformation($"{this._callerName} > {userMessage}");

        await this.ExecutePlannerIfNeededAsync(userMessage).ConfigureAwait(false);

        this._chatHistory.AddUserMessage(userMessage);

        var agentAnswer = await this._agent.ChatCompletion.GetChatMessageContentAsync(this._chatHistory)
                                        .ConfigureAwait(false);

        this._chatHistory.Add(agentAnswer);
        this._logger.LogInformation(message: $"{this._agent.Name!} > {agentAnswer.Content}");

        return agentAnswer.Content;
    }

    /// <summary>
    /// Extracts the user intent from the chat history.
    /// </summary>
    /// <param name="userMessage">The user message.</param>
    /// <returns></returns>
    private async Task<string> ExtractUserIntentAsync(string userMessage)
    {
        var chat = new ChatHistory(SystemIntentExtractionPrompt);

        foreach (var item in this._chatHistory)
        {
            if (item.Role == AuthorRole.User)
            {
                chat.AddUserMessage(item.Content);
            }
            else if (item.Role == AuthorRole.Assistant)
            {
                chat.AddAssistantMessage(item.Content);
            }
        }

        chat.AddUserMessage(userMessage);

        var chatResult = await this._agent.ChatCompletion.GetChatMessageContentAsync(chat).ConfigureAwait(false);

        return chatResult.Content;
    }

    private async Task ExecutePlannerIfNeededAsync(string userMessage)
    {


        if (string.IsNullOrEmpty(this._agent.Planner))
        {
            return;
        }

        var userIntent = await this.ExtractUserIntentAsync(userMessage)
                                .ConfigureAwait(false);

        var result = await this.ExecutePlannerAsync(userIntent).ConfigureAwait(false);

        this._chatHistory.AddFunctionMessage(result!.Trim(), this._agent.Name!);

    }

    private async Task<string?> ExecutePlannerAsync(string userIntent)
    {
        var goal = $"{this._agent.Instructions}\n" +
                            $"Given the following context, accomplish the user intent.\n" +
                            $"{userIntent}";

        switch (this._agent.Planner)
        {
            case "Handlebars":
                return await this.ExecuteHandleBarsPlannerAsync(goal).ConfigureAwait(false);
            case "Stepwise":
                return await this.ExecuteStepwisePlannerAsync(goal).ConfigureAwait(false);
            default:
                throw new NotImplementedException($"Planner {this._agent.Planner} is not implemented.");
        }
    }

    private async Task<string> ExecuteHandleBarsPlannerAsync(string goal, int maxTries = 3)
    {
        HandlebarsPlan? lastPlan = null;
        Exception? lastError = null;

        while (maxTries > 0)
        {
            try
            {
                var planner = new HandlebarsPlanner(new()
                {
                    LastPlan = lastPlan, // Pass in the last plan in case we want to try again
                    LastError = lastError?.Message // Pass in the last error to avoid trying the same thing again
                });

                var plan = await planner.CreatePlanAsync(this._agent.Kernel, goal).ConfigureAwait(false);
                lastPlan = plan;

                var result = plan.Invoke(this._agent.Kernel, new KernelArguments(this._arguments));

                return result;
            }
            catch (Exception e)
            {
                // If we get an error, try again
                lastError = e;
                this._logger.LogWarning(e.Message);
            }
            maxTries--;
        }

        this._logger.LogError(lastError!, lastError!.Message);
        this._logger.LogError(lastPlan!.ToString());

        throw lastError;
    }

    private async Task<string> ExecuteStepwisePlannerAsync(string goal)
    {
        var config = new FunctionCallingStepwisePlannerConfig
        {
            MaxIterations = 15,
            MaxTokens = 4000,
        };

        var planner = new FunctionCallingStepwisePlanner(config);

        var result = await planner.ExecuteAsync(this._agent.Kernel, goal).ConfigureAwait(false);

        return result.FinalAnswer;
    }
}
