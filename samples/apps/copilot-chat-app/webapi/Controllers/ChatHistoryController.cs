// Copyright (c) Microsoft. All rights reserved.

using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using SemanticKernel.Service.Model;
using SemanticKernel.Service.Skills;
using SemanticKernel.Service.Storage;

namespace SemanticKernel.Service.Controllers;

/// <summary>
/// Controller for chat history.
/// </summary>
[ApiController]
public class ChatHistoryController : ControllerBase
{
    private readonly ILogger<SemanticKernelController> _logger;
    private readonly ChatSessionRepository _chatSessionRepository;
    private readonly ChatMessageRepository _chatMessageRepository;
    private readonly PromptSettings _promptSettings;

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatHistoryController"/> class.
    /// </summary>
    /// <param name="logger">The logger.</param>
    /// <param name="chatSessionRepository">The chat session repository.</param>
    /// <param name="chatMessageRepository">The chat message repository.</param>
    /// <param name="promptSettings">The prompt settings.</param>
    public ChatHistoryController(
        ILogger<SemanticKernelController> logger,
        ChatSessionRepository chatSessionRepository,
        ChatMessageRepository chatMessageRepository,
        PromptSettings promptSettings)
    {
        this._logger = logger;
        this._chatSessionRepository = chatSessionRepository;
        this._chatMessageRepository = chatMessageRepository;
        this._promptSettings = promptSettings;
    }

    /// <summary>
    /// Create a new chat session and populate the session with the initial bot message.
    /// </summary>
    /// <param name="chatParameters">Object that contains the parameters to create a new chat.</param>
    /// <returns>The HTTP action result.</returns>
    [Authorize]
    [HttpPost]
    [Route("chat/create")]
    [ProducesResponseType(StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> CreateChatAsync(
        [FromBody] ChatSession chatParameters)
    {
        var userId = chatParameters.UserId;
        var title = chatParameters.Title;

        var newChat = new ChatSession(userId, title);
        await this._chatSessionRepository.CreateAsync(newChat);

        var initialBotMessage = this._promptSettings.InitialBotMessage;
        await this.SaveResponseAsync(initialBotMessage, newChat.Id);

        this._logger.LogDebug($"Created chat session with id {newChat.Id} for user {userId}.");
        return this.CreatedAtAction(nameof(this.GetChatByIdAsync), new { chatId = newChat.Id }, newChat);
    }

    /// <summary>
    /// Get a chat session by id.
    /// </summary>
    /// <param name="chatId">The chat id.</param>
    [Authorize]
    [HttpGet]
    [ActionName("GetChatByIdAsync")]
    [Route("chat/getChat/{chatId:guid}")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetChatByIdAsync(Guid chatId)
    {
        var chat = await this._chatSessionRepository.FindByIdAsync(chatId.ToString());
        if (chat == null)
        {
            return this.NotFound($"Chat of id {chatId} not found.");
        }

        return this.Ok(chat);
    }

    /// <summary>
    /// Get all chat sessions associated with a user. Return an empty list if no chats are found.
    /// </summary>
    /// <param name="userId">The user id.</param>
    [Authorize]
    [HttpGet]
    [Route("chat/getAllChats/{userId:regex([[0-9]]+\\.[[0-9]]+)}")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetAllChatsAsync(string userId)
    {
        var chats = await this._chatSessionRepository.FindByUserIdAsync(userId);
        if (chats == null)
        {
            // Return an empty list if no chats are found
            return this.Ok(new List<ChatSession>());
        }

        return this.Ok(chats);
    }

    /// <summary>
    /// Get all chat messages for a chat session.
    /// The list will be ordered with the first entry being the most recent message.
    /// </summary>
    /// <param name="chatId">The chat id.</param>
    /// <param name="startIdx">The start index at which the first message will be returned.</param>
    /// <param name="count">The number of messages to return. -1 will return all messages starting from startIdx.</param>
    /// [Authorize]
    [HttpGet]
    [Route("chat/getChatMessages/{chatId:guid}")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetChatMessagesAsync(
        Guid chatId,
        [FromQuery] int startIdx = 0,
        [FromQuery] int count = -1)
    {
        var chatMessages = await this._chatMessageRepository.FindByChatIdAsync(chatId.ToString());
        if (chatMessages == null)
        {
            return this.NotFound($"No messages found for chat of id {chatId}.");
        }

        if (startIdx >= chatMessages.Count())
        {
            return this.BadRequest($"Start index {startIdx} is out of range.");
        }
        else if (startIdx + count > chatMessages.Count() || count == -1)
        {
            count = chatMessages.Count() - startIdx;
        }

        chatMessages = chatMessages.OrderByDescending(m => m.Timestamp).Skip(startIdx).Take(count);
        return this.Ok(chatMessages);
    }

    /// <summary>
    /// Edit a chat session.
    /// </summary>
    /// <param name="chatParameters">Object that contains the parameters to edit the chat.</param>
    [Authorize]
    [HttpPost]
    [Route("chat/edit")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> EditChatAsync([FromBody] ChatSession chatParameters)
    {
        var chatId = chatParameters.Id;
        Console.WriteLine(chatId);

        var chat = await this._chatSessionRepository.FindByIdAsync(chatId.ToString());
        if (chat == null)
        {
            return this.NotFound($"Chat of id {chatId} not found.");
        }

        chat.Title = chatParameters.Title;
        await this._chatSessionRepository.UpdateAsync(chat);

        return this.Ok(chat);
    }

    # region Private

    /// <summary>
    /// Save a bot response to the chat session.
    /// </summary>
    /// <param name="response">The bot response.</param>
    /// <param name="chatId">The chat id.</param>
    private async Task SaveResponseAsync(string response, string chatId)
    {
        // Make sure the chat session exists
        await this._chatSessionRepository.FindByIdAsync(chatId);

        var chatMessage = ChatMessage.CreateBotResponseMessage(chatId, response);
        await this._chatMessageRepository.CreateAsync(chatMessage);
    }

    # endregion
}