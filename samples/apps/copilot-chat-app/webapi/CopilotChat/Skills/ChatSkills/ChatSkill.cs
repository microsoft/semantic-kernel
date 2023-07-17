// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.TemplateEngine;
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
    /// A semantic chat memory skill instance to query semantic memories.
    /// </summary>
    private readonly SemanticChatMemorySkill _semanticChatMemorySkill;

    /// <summary>
    /// A document memory skill instance to query document memories.
    /// </summary>
    private readonly DocumentMemorySkill _documentMemorySkill;

    /// <summary>
    /// A skill instance to acquire external information.
    /// </summary>
    private readonly ExternalInformationSkill _externalInformationSkill;

    /// <summary>
    /// A dictionary of all the semantic chat skill functions
    /// </summary>
    private readonly IDictionary<string, ISKFunction> _chatPlugin;

    /// <summary>
    /// A dictionary mapping all of the semantic chat skill functions to the token counts of their prompts
    /// </summary>
    private readonly IDictionary<string, PluginPromptOptions> _chatPluginPromptOptions;

    /// <summary>
    /// Create a new instance of <see cref="ChatSkill"/>.
    /// </summary>
    public ChatSkill(
        IKernel kernel,
        ChatMessageRepository chatMessageRepository,
        ChatSessionRepository chatSessionRepository,
        IOptions<PromptsOptions> promptOptions,
        IOptions<DocumentMemoryOptions> documentImportOptions,
        CopilotChatPlanner planner)
    {
        this._kernel = kernel;
        this._chatMessageRepository = chatMessageRepository;
        this._chatSessionRepository = chatSessionRepository;
        this._promptOptions = promptOptions.Value;

        this._semanticChatMemorySkill = new SemanticChatMemorySkill(
            promptOptions);
        this._documentMemorySkill = new DocumentMemorySkill(
            promptOptions,
            documentImportOptions,
            kernel.Log);
        this._externalInformationSkill = new ExternalInformationSkill(
            promptOptions,
            planner);

        var projectDir = Path.GetFullPath(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, @"..\..\.."));
        var parentDir = Path.GetFullPath(Path.Combine(projectDir, "CopilotChat", "Skills"));
        this._chatPlugin = this._kernel.ImportSemanticSkillFromDirectory(parentDir, "SemanticSkills");

        var skillDir = Path.Combine(parentDir, "SemanticSkills");
        this._chatPluginPromptOptions = this.calcChatPluginTokens(this._chatPlugin, skillDir);
    }

    /// <summary>
    /// Extract chat history.
    /// </summary>
    [SKFunction, Description("Extract chat history")]
    public async Task<string> ExtractChatHistoryAsync(
        [Description("Chat ID to extract history from")] string chatId,
        [Description("Maximum number of tokens")] int tokenLimit)
    {
        var messages = await this._chatMessageRepository.FindByChatIdAsync(chatId);
        var sortedMessages = messages.OrderByDescending(m => m.Timestamp);

        var remainingToken = tokenLimit;

        string historyText = "";
        foreach (var chatMessage in sortedMessages)
        {
            var formattedMessage = chatMessage.ToFormattedString();

            // Plan object is not meaningful content in generating bot response, so shorten to intent only to save on tokens
            if (formattedMessage.Contains("proposedPlan\":", StringComparison.InvariantCultureIgnoreCase))
            {
                string pattern = @"(\[.*?\]).*User Intent:User intent: (.*)(?=""}})";
                Match match = Regex.Match(formattedMessage, pattern);
                if (match.Success)
                {
                    string timestamp = match.Groups[1].Value.Trim();
                    string userIntent = match.Groups[2].Value.Trim();

                    formattedMessage = $"{timestamp} Bot proposed plan to fulfill user intent: {userIntent}";
                }
                else
                {
                    formattedMessage = "Bot proposed plan";
                }
            }

            var tokenCount = Utilities.TokenCount(formattedMessage);

            if (remainingToken - tokenCount >= 0)
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
    [SKFunction, Description("Get chat response")]
    public async Task<SKContext> ChatAsync(
        [Description("The new message")] string message,
        [Description("Unique and persistent identifier for the user")] string userId,
        [Description("Name of the user")] string userName,
        [Description("Unique and persistent identifier for the chat")] string chatId,
        [Description("Type of the message")] string messageType,
        [Description("Previously proposed plan that is approved"), DefaultValue(null)] string? proposedPlan,
        [Description("ID of the response message for planner"), DefaultValue(null)] string? responseMessageId,
        SKContext context)
    {
        // Save this new message to memory such that subsequent chat responses can use it
        await this.SaveNewMessageAsync(message, userId, userName, chatId, messageType);

        // Clone the context to avoid modifying the original context variables.
        var chatContext = Utilities.CopyContextWithVariablesClone(context);
        chatContext.Variables.Set("chatId", context["chatId"]);
        chatContext.Variables.Set("knowledgeCutoff", this._promptOptions.KnowledgeCutoffDate);

        // Check if plan exists in ask's context variables.
        // If plan was returned at this point, that means it was approved or cancelled.
        // Update the response previously saved in chat history with state
        if (!string.IsNullOrWhiteSpace(proposedPlan) &&
            !string.IsNullOrEmpty(responseMessageId))
        {
            await this.UpdateResponseAsync(proposedPlan, responseMessageId);
        }

        var response = chatContext.Variables.ContainsKey("userCancelledPlan")
            ? "I am sorry the plan did not meet your goals."
            : await this.GetChatResponseAsync(chatId, chatContext);

        if (chatContext.ErrorOccurred)
        {
            context.Fail(chatContext.LastErrorDescription);
            return context;
        }

        // Retrieve the prompt used to generate the response
        // and return it to the caller via the context variables.
        chatContext.Variables.TryGetValue("prompt", out string? prompt);
        prompt ??= string.Empty;
        context.Variables.Set("prompt", prompt);

        // Save this response to memory such that subsequent chat responses can use it
        ChatMessage botMessage = await this.SaveNewResponseAsync(response, prompt, chatId);
        context.Variables.Set("messageId", botMessage.Id);
        context.Variables.Set("messageType", ((int)botMessage.Type).ToString(CultureInfo.InvariantCulture));

        // Extract semantic chat memory
        await SemanticChatMemoryExtractor.ExtractSemanticChatMemoryAsync(
            chatId,
            chatContext,
            this._promptOptions,
            this._chatPlugin,
            this._chatPluginPromptOptions);

        context.Variables.Update(response);
        return context;
    }

    #region Private

    /// <summary>
    /// Generate the necessary chat context to create a prompt then invoke the model to get a response.
    /// </summary>
    /// <param name="chatContext">The SKContext.</param>
    /// <returns>A response from the model.</returns>
    private async Task<string> GetChatResponseAsync(string chatId, SKContext chatContext)
    {
        // 0. Get the audience
        var audience = await this.GetAudienceAsync(chatContext);
        if (chatContext.ErrorOccurred)
        {
            return string.Empty;
        }

        // 1. Extract user intent from the conversation history.
        var userIntent = await this.GetUserIntentAsync(chatContext);
        if (chatContext.ErrorOccurred)
        {
            return string.Empty;
        }

        // 2. Calculate the remaining token budget.
        var remainingToken = this.GetChatContextTokenLimit(userIntent);

        // 3. Acquire external information from planner
        var externalInformationTokenLimit = (int)(remainingToken * this._promptOptions.ExternalInformationContextWeight);
        var planResult = await this.AcquireExternalInformationAsync(chatContext, userIntent, externalInformationTokenLimit);
        if (chatContext.ErrorOccurred)
        {
            return string.Empty;
        }

        // If plan is suggested, send back to user for approval before running
        if (this._externalInformationSkill.ProposedPlan != null)
        {
            return JsonSerializer.Serialize<ProposedPlan>(this._externalInformationSkill.ProposedPlan);
        }

        // 4. Query relevant semantic memories
        var chatMemoriesTokenLimit = (int)(remainingToken * this._promptOptions.MemoriesResponseContextWeight);
        var chatMemories = await this._semanticChatMemorySkill.QueryMemoriesAsync(chatContext, userIntent, chatId, chatMemoriesTokenLimit, chatContext.Memory);
        if (chatContext.ErrorOccurred)
        {
            return string.Empty;
        }

        // 5. Query relevant document memories
        var documentContextTokenLimit = (int)(remainingToken * this._promptOptions.DocumentContextWeight);
        var documentMemories = await this._documentMemorySkill.QueryDocumentsAsync(userIntent, chatId, documentContextTokenLimit, chatContext.Memory);
        if (chatContext.ErrorOccurred)
        {
            return string.Empty;
        }

        // 6. Fill in the chat history if there is any token budget left
        var chatContextComponents = new List<string>() { chatMemories, documentMemories, planResult };
        var chatContextText = string.Join("\n\n", chatContextComponents.Where(c => !string.IsNullOrEmpty(c)));
        var chatContextTextTokenCount = remainingToken - Utilities.TokenCount(chatContextText);
        if (chatContextTextTokenCount > 0)
        {
            var chatHistory = await this.ExtractChatHistoryAsync(chatId, chatContextTextTokenCount);
            if (chatContext.ErrorOccurred)
            {
                return string.Empty;
            }
            chatContextText = $"{chatContextText}\n{chatHistory}";
        }

        // Get the prompt.txt text
        var projectDir = Path.GetFullPath(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, @"..\..\.."));
        var skillDir = Path.GetFullPath(Path.Combine(projectDir, "CopilotChat", "Skills", "SemanticSkills"));
        var chatPromptText = this.GetPromptTemplateText(this._chatPlugin, skillDir, "Chat");

        // Invoke the model
        chatContext.Variables.Set("Audience", audience);
        chatContext.Variables.Set("UserIntent", userIntent);
        chatContext.Variables.Set("ChatContext", chatContextText);

        var promptRenderer = new PromptTemplateEngine();
        var renderedPrompt = await promptRenderer.RenderAsync(chatPromptText, chatContext);

        var result = await this._chatPlugin["Chat"].InvokeAsync(chatContext, this._chatPluginPromptOptions["Chat"].CompletionSettings);

        // Allow the caller to view the prompt used to generate the response
        chatContext.Variables.Set("prompt", renderedPrompt);

        if (chatContext.ErrorOccurred)
        {
            return string.Empty;
        }

        return chatContext.Result;
    }

    /// <summary>
    /// Helper function that creates the correct context variables to
    /// retrieve a list of participants from the conversation history.
    /// Calls the ExtractAudience semantic function
    /// Note that only those who have spoken will be included
    /// </summary>
    private async Task<string> GetAudienceAsync(SKContext context)
    {
        var audienceContext = Utilities.CopyContextWithVariablesClone(context);
        audienceContext.Variables.Set("tokenLimit", this.GetHistoryTokenBudgetForFunc("ExtractAudience"));

        var result = await this._chatPlugin["ExtractAudience"].InvokeAsync(audienceContext, this._chatPluginPromptOptions["ExtractAudience"].CompletionSettings);

        if (result.ErrorOccurred)
        {
            context.Log.LogError("{0}: {1}", result.LastErrorDescription, result.LastException);
            context.Fail(result.LastErrorDescription);
            return string.Empty;
        }

        return $"List of participants: {result}";
    }

    /// <summary>
    /// Helper function that creates the correct context variables to
    /// extract user intent from the conversation history.
    /// Calls the ExtractUserIntent semantic function
    /// </summary>
    private async Task<string> GetUserIntentAsync(SKContext context)
    {
        // TODO: Regenerate user intent if plan was modified
        if (!context.Variables.TryGetValue("planUserIntent", out string? userIntent))
        {
            var intentContext = Utilities.CopyContextWithVariablesClone(context);
            intentContext.Variables.Set("audience", context["userName"]);
            intentContext.Variables.Set("tokenLimit", this.GetHistoryTokenBudgetForFunc("ExtractUserIntent"));

            var result = await this._chatPlugin["ExtractUserIntent"].InvokeAsync(intentContext, this._chatPluginPromptOptions["ExtractUserIntent"].CompletionSettings);
            userIntent = $"User intent: {result}";

            if (result.ErrorOccurred)
            {
                context.Log.LogError("{0}: {1}", result.LastErrorDescription, result.LastException);
                context.Fail(result.LastErrorDescription);
                return string.Empty;
            }
        }

        return userIntent;
    }

    /// <summary>
    /// Helper function create the correct context variables to
    /// query chat memories from the chat memory store.
    /// </summary>
    private Task<string> QueryChatMemoriesAsync(SKContext context, string userIntent, int tokenLimit)
    {
        return this._semanticChatMemorySkill.QueryMemoriesAsync(context, userIntent, context["chatId"], tokenLimit, context.Memory);
    }

    /// <summary>
    /// Helper function create the correct context variables to
    /// query document memories from the document memory store.
    /// </summary>
    private Task<string> QueryDocumentsAsync(SKContext context, string userIntent, int tokenLimit)
    {
        return this._documentMemorySkill.QueryDocumentsAsync(userIntent, context["chatId"], tokenLimit, context.Memory);
    }

    /// <summary>
    /// Helper function create the correct context variables to acquire external information.
    /// </summary>
    private async Task<string> AcquireExternalInformationAsync(SKContext context, string userIntent, int tokenLimit)
    {
        var contextVariables = context.Variables.Clone();
        contextVariables.Set("tokenLimit", tokenLimit.ToString(new NumberFormatInfo()));

        var planContext = new SKContext(
            contextVariables,
            context.Memory,
            context.Skills,
            context.Log,
            context.CancellationToken
        );

        var plan = await this._externalInformationSkill.AcquireExternalInformationAsync(tokenLimit, userIntent, planContext);

        // Propagate the error
        if (planContext.ErrorOccurred)
        {
            context.Fail(planContext.LastErrorDescription);
        }

        return plan;
    }

    /// <summary>
    /// Save a new message to the chat history.
    /// </summary>
    /// <param name="message">The message</param>
    /// <param name="userId">The user ID</param>
    /// <param name="userName"></param>
    /// <param name="chatId">The chat ID</param>
    /// <param name="type">Type of the message</param>
    private async Task<ChatMessage> SaveNewMessageAsync(string message, string userId, string userName, string chatId, string type)
    {
        // Make sure the chat exists.
        if (!await this._chatSessionRepository.TryFindByIdAsync(chatId, v => _ = v))
        {
            throw new ArgumentException("Chat session does not exist.");
        }

        var chatMessage = new ChatMessage(
            userId,
            userName,
            chatId,
            message,
            "",
            ChatMessage.AuthorRoles.User,
            // Default to a standard message if the `type` is not recognized
            Enum.TryParse(type, out ChatMessage.ChatMessageType typeAsEnum) && Enum.IsDefined(typeof(ChatMessage.ChatMessageType), typeAsEnum)
                ? typeAsEnum
                : ChatMessage.ChatMessageType.Message);

        await this._chatMessageRepository.CreateAsync(chatMessage);
        return chatMessage;
    }

    /// <summary>
    /// Save a new response to the chat history.
    /// </summary>
    /// <param name="response">Response from the chat.</param>
    /// <param name="prompt">Prompt used to generate the response.</param>
    /// <param name="chatId">The chat ID</param>
    /// <returns>The created chat message.</returns>
    private async Task<ChatMessage> SaveNewResponseAsync(string response, string prompt, string chatId)
    {
        // Make sure the chat exists.
        if (!await this._chatSessionRepository.TryFindByIdAsync(chatId, v => _ = v))
        {
            throw new ArgumentException("Chat session does not exist.");
        }

        var chatMessage = ChatMessage.CreateBotResponseMessage(chatId, response, prompt);
        await this._chatMessageRepository.CreateAsync(chatMessage);

        return chatMessage;
    }

    /// <summary>
    /// Updates previously saved response in the chat history.
    /// </summary>
    /// <param name="updatedResponse">Updated response from the chat.</param>
    /// <param name="messageId">The chat message ID</param>
    private async Task UpdateResponseAsync(string updatedResponse, string messageId)
    {
        // Make sure the chat exists.
        var chatMessage = await this._chatMessageRepository.FindByIdAsync(messageId);
        chatMessage.Content = updatedResponse;

        await this._chatMessageRepository.UpsertAsync(chatMessage);
    }

    /// <summary>
    /// Create a dictionary mapping semantic functions for a skill to the number of tokens their prompts use/
    /// </summary>
    private Dictionary<string, PluginPromptOptions> calcChatPluginTokens(IDictionary<string, ISKFunction> skillPlugin, string skillDir)
    {
        var funcTokenCounts = new Dictionary<string, PluginPromptOptions>();

        foreach (KeyValuePair<string, ISKFunction> funcEntry in skillPlugin)
        {
            var promptPath = Path.Combine(skillDir, funcEntry.Key, Constants.PromptFileName);
            if (!File.Exists(promptPath)) { continue; }

            var configPath = Path.Combine(skillDir, funcEntry.Key, Constants.ConfigFileName);
            funcTokenCounts.Add(funcEntry.Key, new PluginPromptOptions(promptPath, configPath, this._kernel.Log));
        }

        return funcTokenCounts;
    }

    /// <summary>
    /// Get prompt template text from prompt.txt file
    /// </summary>
    private string GetPromptTemplateText(IDictionary<string, ISKFunction> skillPlugin, string skillDir, string funcName)
    {
        var promptText = "";
        var promptPath = Path.Combine(skillDir, funcName, Constants.PromptFileName);

        if (skillPlugin.ContainsKey("Chat") && File.Exists(promptPath))
        {
            promptText = File.ReadAllText(promptPath);
        }

        return promptText;
    }

    /// <summary>
    /// Calculate the remaining token budget for the chat response prompt.
    /// This is the token limit minus the token count of the user intent and the system commands.
    /// </summary>
    /// <param name="userIntent">The user intent returned by the model.</param>
    /// <returns>The remaining token limit.</returns>
    private int GetChatContextTokenLimit(string userIntent)
    {
        int maxTokenCount = this._chatPluginPromptOptions["Chat"].CompletionSettings.MaxTokens ?? 256;
        int remainingToken =
            this._promptOptions.CompletionTokenLimit -
            maxTokenCount -
            Utilities.TokenCount(userIntent) -
            this._chatPluginPromptOptions["Chat"].PromptTokenCount;

        return remainingToken;
    }

    /// <summary>
    /// Calculate the remaining token budget for the chat response that can be used by the ExtractChatHistory function
    /// </summary>
    private string GetHistoryTokenBudgetForFunc(string funcName)
    {
        int maxTokens = this._chatPluginPromptOptions[funcName].CompletionSettings.MaxTokens ?? 512;
        int historyTokenBudget =
                this._promptOptions.CompletionTokenLimit -
                maxTokens -
                this._chatPluginPromptOptions[funcName].PromptTokenCount;

        return historyTokenBudget.ToString(new NumberFormatInfo());
    }

    # endregion
}
