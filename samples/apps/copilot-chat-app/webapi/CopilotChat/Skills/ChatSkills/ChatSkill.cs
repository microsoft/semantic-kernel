// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using SemanticKernel.Service.CopilotChat.Models;
using SemanticKernel.Service.CopilotChat.Options;
using SemanticKernel.Service.CopilotChat.Storage;

namespace SemanticKernel.Service.CopilotChat.Skills.ChatSkills;

/// <summary>
/// ChatSkill offers a more coherent chat experience by using memories
/// to extract conversation history and user intentions.
/// </summary>
public class ChatSkill
{
    /// <summary>
    /// A kernel instance to create a completion function since each invocation
    /// of the <see cref="ChatAsync"/> function will generate a new prompt dynamically.
    /// </summary>
    private readonly IKernel _kernel;

    /// <summary>
    /// A repository to save and retrieve chat messages.
    /// </summary>
    private readonly ChatMessageRepository _chatMessageRepository;

    /// <summary>
    /// A repository to save and retrieve chat sessions.
    /// </summary>
    private readonly ChatSessionRepository _chatSessionRepository;

    /// <summary>
    /// Settings containing prompt texts.
    /// </summary>
    private readonly PromptsOptions _promptOptions;

    /// <summary>
    /// Create a new instance of <see cref="ChatSkill"/>.
    /// </summary>
    public ChatSkill(
        IKernel kernel,
        ChatMessageRepository chatMessageRepository,
        ChatSessionRepository chatSessionRepository,
        IOptions<PromptsOptions> promptOptions,
        CopilotChatPlanner planner,
        ILogger logger)
    {
        this._kernel = kernel;
        this._chatMessageRepository = chatMessageRepository;
        this._chatSessionRepository = chatSessionRepository;
        this._promptOptions = promptOptions.Value;
    }

    /// <summary>
    /// Extract user intent from the conversation history.
    /// </summary>
    /// <param name="context">Contains the 'audience' indicating the name of the user.</param>
    [SKFunction("Extract user intent")]
    [SKFunctionName("ExtractUserIntent")]
    [SKFunctionContextParameter(Name = "chatId", Description = "Chat ID to extract history from")]
    [SKFunctionContextParameter(Name = "audience", Description = "The audience the chat bot is interacting with.")]
    public async Task<string> ExtractUserIntentAsync(SKContext context)
    {
        var tokenLimit = this._promptOptions.CompletionTokenLimit;
        var historyTokenBudget =
            tokenLimit -
            this._promptOptions.ResponseTokenLimit -
            Utilities.TokenCount(string.Join("\n", new string[]
                {
                    this._promptOptions.SystemDescription,
                    this._promptOptions.SystemIntent,
                    this._promptOptions.SystemIntentContinuation
                })
            );

        // Clone the context to avoid modifying the original context variables.
        var intentExtractionContext = Utilities.CopyContextWithVariablesClone(context);
        intentExtractionContext.Variables.Set("tokenLimit", historyTokenBudget.ToString(new NumberFormatInfo()));
        intentExtractionContext.Variables.Set("knowledgeCutoff", this._promptOptions.KnowledgeCutoffDate);

        var completionFunction = this._kernel.CreateSemanticFunction(
            this._promptOptions.SystemIntentExtraction,
            skillName: nameof(ChatSkill),
            description: "Complete the prompt.");

        var result = await completionFunction.InvokeAsync(
            intentExtractionContext,
            settings: this.CreateIntentCompletionSettings()
        );

        if (result.ErrorOccurred)
        {
            context.Log.LogError("{0}: {1}", result.LastErrorDescription, result.LastException);
            context.Fail(result.LastErrorDescription);
            return string.Empty;
        }

        return $"User intent: {result}";
    }

    /// <summary>
    /// Extract chat history.
    /// </summary>
    /// <param name="context">Contains the 'tokenLimit' controlling the length of the prompt.</param>
    [SKFunction("Extract chat history")]
    [SKFunctionName("ExtractChatHistory")]
    [SKFunctionContextParameter(Name = "chatId", Description = "Chat ID to extract history from")]
    [SKFunctionContextParameter(Name = "tokenLimit", Description = "Maximum number of tokens")]
    public async Task<string> ExtractChatHistoryAsync(SKContext context)
    {
        var chatId = context["chatId"];
        var tokenLimit = int.Parse(context["tokenLimit"], new NumberFormatInfo());

        var messages = await this._chatMessageRepository.FindByChatIdAsync(chatId);
        var sortedMessages = messages.OrderByDescending(m => m.Timestamp);

        var remainingToken = tokenLimit;
        string historyText = "";
        foreach (var chatMessage in sortedMessages)
        {
            var formattedMessage = chatMessage.ToFormattedString();
            var tokenCount = Utilities.TokenCount(formattedMessage);

            // Plan object is not meaningful content in generating chat response, exclude it
            if (remainingToken - tokenCount > 0 && !formattedMessage.Contains("proposedPlan\\\":", StringComparison.InvariantCultureIgnoreCase))
            {
                historyText = $"{formattedMessage}\n{historyText}";
                remainingToken -= tokenCount;
            }
            else
            {
                break;
            }
        }

        return $"Chat history:\n{historyText.Trim()}";
    }

    /// <summary>
    /// This is the entry point for getting a chat response. It manages the token limit, saves
    /// messages to memory, and fill in the necessary context variables for completing the
    /// prompt that will be rendered by the template engine.
    /// </summary>
    /// <param name="message"></param>
    /// <param name="context">Contains the 'tokenLimit' and the 'contextTokenLimit' controlling the length of the prompt.</param>
    [SKFunction("Get chat response")]
    [SKFunctionName("Chat")]
    [SKFunctionInput(Description = "The new message")]
    [SKFunctionContextParameter(Name = "userId", Description = "Unique and persistent identifier for the user")]
    [SKFunctionContextParameter(Name = "userName", Description = "Name of the user")]
    [SKFunctionContextParameter(Name = "chatId", Description = "Unique and persistent identifier for the chat")]
    public async Task<SKContext> ChatAsync(string message, SKContext context)
    {
        // Log exception and strip it from the context, leaving the error description.
        static SKContext RemoveExceptionFromContext(SKContext chatContext)
        {
            chatContext.Log.LogError("{0}: {1}", chatContext.LastErrorDescription, chatContext.LastException);
            chatContext.Fail(chatContext.LastErrorDescription);
            return chatContext;
        }

        string response;
        var chatId = context["chatId"];

        // Clone the context to avoid modifying the original context variables.
        var chatContext = Utilities.CopyContextWithVariablesClone(context);

        var userId = context["userId"];
        var userName = context["userName"];

        // TODO: check if user has access to the chat

        // Save this new message to memory such that subsequent chat responses can use it
        try
        {
            await this.SaveNewMessageAsync(message, userId, userName, chatId);
        }
        catch (Exception ex) when (!ex.IsCriticalException())
        {
            context.Log.LogError("Unable to save new message: {0}", ex.Message);
            context.Fail($"Unable to save new message: {ex.Message}", ex);
            return context;
        }

        if (chatContext.Variables.Get("userCancelledPlan", out var userCancelledPlan))
        {
            response = "I am sorry the plan did not meet your goals.";
        }
        else
        {
            // Normal response generation flow
            var tokenLimit = this._promptOptions.CompletionTokenLimit;
            var remainingToken =
                tokenLimit -
                this._promptOptions.ResponseTokenLimit -
                Utilities.TokenCount(string.Join("\n", new string[]
                    {
                        this._promptOptions.SystemDescription,
                        this._promptOptions.SystemResponse,
                        this._promptOptions.SystemChatContinuation
                    })
                );
            var contextTokenLimit = remainingToken;

            chatContext.Variables.Set("knowledgeCutoff", this._promptOptions.KnowledgeCutoffDate);
            chatContext.Variables.Set("audience", userName);

            // If user approved plan, use the user intent determined on initial pass
            if (!chatContext.Variables.Get("planUserIntent", out string? userIntent))
            {
                // Extract user intent and update remaining token count
                userIntent = await this.ExtractUserIntentAsync(chatContext);
                if (chatContext.ErrorOccurred)
                {
                    return RemoveExceptionFromContext(chatContext);
                }
            }

            userIntent ??= "";
            chatContext.Variables.Set("userIntent", userIntent);

            // Update remaining token count
            remainingToken -= Utilities.TokenCount(userIntent);
            chatContext.Variables.Set("contextTokenLimit", contextTokenLimit.ToString(new NumberFormatInfo()));
            chatContext.Variables.Set("tokenLimit", remainingToken.ToString(new NumberFormatInfo()));

            var completionFunction = this._kernel.CreateSemanticFunction(
                this._promptOptions.SystemChatPrompt,
                skillName: nameof(ChatSkill),
                description: "Complete the prompt.");

            chatContext = await completionFunction.InvokeAsync(
                context: chatContext,
                settings: this.CreateChatResponseCompletionSettings()
            );

            // If the completion function failed, return the context containing the error.
            if (chatContext.ErrorOccurred)
            {
                return RemoveExceptionFromContext(chatContext);
            }

            response = chatContext.Result;

            // If plan is suggested, send back to user for approval before running
            if (this._proposedPlan != null)
            {
                var proposedPlanJson = JsonSerializer.Serialize<ProposedPlan>(new ProposedPlan(this._proposedPlan));

                // Override generated response with plan object to show user for approval
                response = proposedPlanJson;
            }
        }

        // Save this response to memory such that subsequent chat responses can use it
        try
        {
            await this.SaveNewResponseAsync(response, chatId);
        }
        catch (Exception ex) when (!ex.IsCriticalException())
        {
            context.Log.LogError("Unable to save new response: {0}", ex.Message);
            context.Fail($"Unable to save new response: {ex.Message}");
            return context;
        }

        // Extract semantic memory
        await this.ExtractSemanticMemoryAsync(chatId, chatContext);

        context.Variables.Update(response);
        context.Variables.Set("userId", "Bot");
        return context;
    }

    #region Private

    /// <summary>
    /// Save a new message to the chat history.
    /// </summary>
    /// <param name="message">The message</param>
    /// <param name="userId">The user ID</param>
    /// <param name="userName"></param>
    /// <param name="chatId">The chat ID</param>
    private async Task SaveNewMessageAsync(string message, string userId, string userName, string chatId)
    {
        // Make sure the chat exists.
        await this._chatSessionRepository.FindByIdAsync(chatId);

        var chatMessage = new ChatMessage(userId, userName, chatId, message);
        await this._chatMessageRepository.CreateAsync(chatMessage);
    }

    /// <summary>
    /// Save a new response to the chat history.
    /// </summary>
    /// <param name="response">Response from the chat.</param>
    /// <param name="chatId">The chat ID</param>
    private async Task SaveNewResponseAsync(string response, string chatId)
    {
        // Make sure the chat exists.
        await this._chatSessionRepository.FindByIdAsync(chatId);

        var chatMessage = ChatMessage.CreateBotResponseMessage(chatId, response);
        await this._chatMessageRepository.CreateAsync(chatMessage);
    }

    /// <summary>
    /// Extract and save semantic memory.
    /// </summary>
    /// <param name="chatId">The Chat ID.</param>
    /// <param name="context">The context containing the memory.</param>
    private async Task ExtractSemanticMemoryAsync(string chatId, SKContext context)
    {
        foreach (var memoryName in this._promptOptions.MemoryMap.Keys)
        {
            try
            {
                var semanticMemory = await SemanticChatMemoryExtractor.ExtractCognitiveMemoryAsync(
                    memoryName,
                    this._kernel,
                    context,
                    this._promptOptions
                );
                foreach (var item in semanticMemory.Items)
                {
                    await this.CreateMemoryAsync(item, chatId, context, memoryName);
                }
            }
            catch (Exception ex) when (!ex.IsCriticalException())
            {
                // Skip semantic memory extraction for this item if it fails.
                // We cannot rely on the model to response with perfect Json each time.
                context.Log.LogInformation("Unable to extract semantic memory for {0}: {1}. Continuing...", memoryName, ex.Message);
                continue;
            }
        }
    }

    /// <summary>
    /// Create a memory item in the memory collection.
    /// </summary>
    /// <param name="item">A SemanticChatMemoryItem instance</param>
    /// <param name="chatId">The ID of the chat the memories belong to</param>
    /// <param name="context">The context that contains the memory</param>
    /// <param name="memoryName">Name of the memory</param>
    private async Task CreateMemoryAsync(SemanticChatMemoryItem item, string chatId, SKContext context, string memoryName)
    {
        var memoryCollectionName = SemanticChatMemoryExtractor.MemoryCollectionName(chatId, memoryName);

        var memories = await context.Memory.SearchAsync(
                collection: memoryCollectionName,
                query: item.ToFormattedString(),
                limit: 1,
                minRelevanceScore: this._promptOptions.SemanticMemoryMinRelevance,
                cancellationToken: context.CancellationToken
            )
            .ToListAsync(context.CancellationToken)
            .ConfigureAwait(false);

        if (memories.Count == 0)
        {
            await context.Memory.SaveInformationAsync(
                collection: memoryCollectionName,
                text: item.ToFormattedString(),
                id: Guid.NewGuid().ToString(),
                description: memoryName,
                cancellationToken: context.CancellationToken
            );
        }
    }

    /// <summary>
    /// Create a completion settings object for chat response. Parameters are read from the PromptSettings class.
    /// </summary>
    private CompleteRequestSettings CreateChatResponseCompletionSettings()
    {
        var completionSettings = new CompleteRequestSettings
        {
            MaxTokens = this._promptOptions.ResponseTokenLimit,
            Temperature = this._promptOptions.ResponseTemperature,
            TopP = this._promptOptions.ResponseTopP,
            FrequencyPenalty = this._promptOptions.ResponseFrequencyPenalty,
            PresencePenalty = this._promptOptions.ResponsePresencePenalty
        };

        return completionSettings;
    }

    /// <summary>
    /// Create a completion settings object for intent response. Parameters are read from the PromptSettings class.
    /// </summary>
    private CompleteRequestSettings CreateIntentCompletionSettings()
    {
        var completionSettings = new CompleteRequestSettings
        {
            MaxTokens = this._promptOptions.ResponseTokenLimit,
            Temperature = this._promptOptions.IntentTemperature,
            TopP = this._promptOptions.IntentTopP,
            FrequencyPenalty = this._promptOptions.IntentFrequencyPenalty,
            PresencePenalty = this._promptOptions.IntentPresencePenalty,
            StopSequences = new string[] { "] bot:" }
        };

        return completionSettings;
    }

    # endregion
}
