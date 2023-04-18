// Copyright (c) Microsoft. All rights reserved.

using System.Globalization;
using System.Text.Json;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using SemanticKernel.Service.Storage;

namespace SemanticKernel.Service.Skills;

/// <summary>
/// ChatHistorySkill provides functions to store and retrieve chat information in memory,
/// as well as functions to extract memories from context.
/// </summary>
public class ChatHistorySkill
{
    private readonly ChatMessageRepository _chatMessageRepository;
    private readonly ChatSessionRepository _chatSessionRepository;
    private readonly PromptSettings _promptSettings;

    public ChatHistorySkill(
        ChatMessageRepository chatMessageRepository,
        ChatSessionRepository chatSessionRepository,
        PromptSettings promptSettings)
    {
        this._chatMessageRepository = chatMessageRepository;
        this._chatSessionRepository = chatSessionRepository;
        this._promptSettings = promptSettings;
    }

    /// <summary>
    /// Create a new chat session in memory.
    /// </summary>
    /// <param name="title">The title of the chat.</param>
    /// <param name="context">Contains the memory, "userId", and "userName".</param>
    /// <returns>An unique chat ID.</returns>
    /// <returns>The initial chat message in a serialized json string.</returns>
    [SKFunction("Create a new chat session in memory.")]
    [SKFunctionName("CreateChat")]
    [SKFunctionInput(Description = "The title of the chat.")]
    [SKFunctionContextParameter(Name = "userId", Description = "Unique and persistent identifier for a user.")]
    [SKFunctionContextParameter(Name = "userName", Description = "Name of the user.")]
    public async Task<SKContext> CreateChatAsync(string title, SKContext context)
    {
        var userId = context["userId"];
        var userName = context["userName"];

        // Create a new chat.
        var newChat = new ChatSession(userId, title);
        await this._chatSessionRepository.CreateAsync(newChat);

        // Create the initial bot message.
        try
        {
            var initialBotMessage = await this.CreateAndSaveInitialBotMessageAsync(newChat.Id, userName);
            // Update the context variables for outputs.
            context.Variables.Update(newChat.Id);
            context.Variables.Set("initialBotMessage", initialBotMessage.ToString());
        }
        catch (Exception ex) when (!ex.IsCriticalException())
        {
            context.Log.LogError("Failed to create the initial bot message for chat {0}: {1}.", newChat.Id, ex.Message);
            context.Fail($"Failed to create the initial bot message for chat: {ex.Message}.", ex);
        }

        return context;
    }

    /// <summary>
    /// Edit a chat session in memory.
    /// </summary>
    /// <param name="chatId">Chat ID that is persistent and unique.</param>
    /// <param name="context">Contains 'title'.</param>
    [SKFunction("Edit a chat session in memory.")]
    [SKFunctionName("EditChat")]
    [SKFunctionInput(Description = "Chat ID that is persistent and unique.")]
    [SKFunctionContextParameter(Name = "title", Description = "The title of the chat.")]
    public async Task EditChatAsync(string chatId, SKContext context)
    {
        ChatSession chat = await this._chatSessionRepository.FindByIdAsync(chatId);
        chat.Title = context["title"];

        await this._chatSessionRepository.UpdateAsync(chat);
    }

    /// <summary>
    /// Get all chat sessions associated with a user.
    /// </summary>
    /// <param name="userId">The user ID</param>
    /// <param name="context">A SKContext</param>
    /// <returns>The list of chat sessions as a serialized Json string.</returns>
    [SKFunction("Get all chat sessions associated with a user.")]
    [SKFunctionName("GetAllChats")]
    [SKFunctionInput(Description = "The user id")]
    public async Task<SKContext> GetAllChatsAsync(string userId, SKContext context)
    {
        var chats = await this._chatSessionRepository.FindByUserIdAsync(userId);
        context.Variables.Update(JsonSerializer.Serialize(chats));

        return context;
    }

    /// <summary>
    /// Get all chat messages by chat ID The list will be ordered with the first entry being the most recent message.
    /// </summary>
    /// <param name="chatId">The chat ID</param>
    /// <param name="context">Contains "startIdx" and "count".</param>
    /// <returns>The list of chat messages as a serialized Json string.</returns>
    [SKFunction("Get all chat messages by chat ID.")]
    [SKFunctionName("GetAllChatMessages")]
    [SKFunctionInput(Description = "The chat id")]
    [SKFunctionContextParameter(Name = "startIdx",
        Description = "The index of the first message to return. Lower values are more recent messages.",
        DefaultValue = "0")]
    [SKFunctionContextParameter(Name = "count",
        Description = "The number of messages to return. -1 will return all messages starting from startIdx.",
        DefaultValue = "-1")]
    public async Task<SKContext> GetChatMessagesAsync(string chatId, SKContext context)
    {
        var startIdx = 0;
        var count = -1;
        try
        {
            startIdx = Math.Max(startIdx, int.Parse(context["startIdx"], new NumberFormatInfo()));
            count = Math.Max(count, int.Parse(context["count"], new NumberFormatInfo()));
        }
        catch (FormatException)
        {
            context.Log.LogError("Unable to parse startIdx: {0} or count: {1}.", context["startIdx"], context["count"]);
            context.Fail($"Unable to parse startIdx: {context["startIdx"]} or count: {context["count"]}.");
            return context;
        }

        var chatMessages = await this._chatMessageRepository.FindByChatIdAsync(chatId);
        if (startIdx > chatMessages.Count())
        {
            context.Variables.Update(JsonSerializer.Serialize<List<ChatMessage>>(new List<ChatMessage>()));
            return context;
        }
        else if (startIdx + count > chatMessages.Count() || count == -1)
        {
            count = chatMessages.Count() - startIdx;
        }

        var messages = chatMessages.OrderByDescending(m => m.Timestamp).Skip(startIdx).Take(count).ToList();
        context.Variables.Update(JsonSerializer.Serialize(messages));
        return context;
    }

    #region Internal

    /// <summary>
    /// Get the latest chat message by chat ID.
    /// </summary>
    /// <param name="chatId">The chat ID</param>
    /// <returns>The latest message as a ChatMessage object.</returns>
    internal async Task<ChatMessage> GetLatestChatMessageAsync(string chatId)
    {
        return await this._chatMessageRepository.FindLastByChatIdAsync(chatId);
    }

    #endregion

    #region Private

    /// <summary>
    /// Save a new response to the chat history.
    /// </summary>
    /// <param name="response">The new response</param>
    /// <param name="chatId">The chat ID</param>
    private async Task SaveNewResponseAsync(string response, string chatId)
    {
        // Make sure the chat exists.
        await this._chatSessionRepository.FindByIdAsync(chatId);

        var chatMessage = ChatMessage.CreateBotResponseMessage(chatId, response);
        await this._chatMessageRepository.CreateAsync(chatMessage);
    }

    /// <summary>
    /// Create and save the initial bot message.
    /// </summary>
    /// <param name="chatId">Chat ID of the chat session.</param>
    /// <param name="userName">Name of the user.</param>
    /// <returns>The initial message in a serialize json string.</returns>
    private async Task<ChatMessage> CreateAndSaveInitialBotMessageAsync(string chatId, string userName)
    {
        var initialBotMessage = string.Format(CultureInfo.CurrentCulture, this._promptSettings.InitialBotMessage, userName);
        await this.SaveNewResponseAsync(initialBotMessage, chatId);

        var latestMessage = await this.GetLatestChatMessageAsync(chatId);
        return latestMessage;
    }

    #endregion
}
