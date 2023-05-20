// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using SemanticKernel.Service.Auth;
using SemanticKernel.Service.CopilotChat.Auth;
using SemanticKernel.Service.CopilotChat.Models;
using SemanticKernel.Service.CopilotChat.Options;
using SemanticKernel.Service.CopilotChat.Storage;

namespace SemanticKernel.Service.CopilotChat.Controllers;

/// <summary>
/// Controller for chat history.
/// This controller is responsible for creating new chat sessions, retrieving chat sessions,
/// retrieving chat messages, and editing chat sessions.
/// </summary>
[ApiController]
public class ChatHistoryController : ControllerBase
{
    private readonly ILogger<ChatHistoryController> _logger;
    private readonly ChatSessionRepository _chatSessionRepository;
    private readonly ChatMessageRepository _chatMessageRepository;
    private readonly IAuthInfo _authInfo;
    private readonly PromptsOptions _promptOptions;

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatHistoryController"/> class.
    /// </summary>
    /// <param name="logger">The logger.</param>
    /// <param name="chatSessionRepository">The chat session repository.</param>
    /// <param name="chatMessageRepository">The chat message repository.</param>
    /// <param name="promptsOptions">The prompts options.</param>
    /// <param name="authInfo">The auth info for the current request.</param>
    public ChatHistoryController(
        ILogger<ChatHistoryController> logger,
        ChatSessionRepository chatSessionRepository,
        ChatMessageRepository chatMessageRepository,
        IOptions<PromptsOptions> promptsOptions,
        IAuthInfo authInfo)
    {
        this._logger = logger;
        this._chatSessionRepository = chatSessionRepository;
        this._chatMessageRepository = chatMessageRepository;
        this._authInfo = authInfo;
        this._promptOptions = promptsOptions.Value;
    }

    /// <summary>
    /// Create a new chat session and populate the session with the initial bot message.
    /// </summary>
    /// <param name="chatParameters">Object that contains the parameters to create a new chat.</param>
    /// <returns>The HTTP action result.</returns>
    [HttpPost]
    [Route("chatSessions")]
    [ProducesResponseType(StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> CreateChatSessionAsync(
        [FromBody] ChatSessionCreationOptions chatParameters)
    {
        var userId = _authInfo.UserId;
        var title = chatParameters.Title;

        var newChat = new ChatSession(userId, title);
        await this._chatSessionRepository.CreateAsync(newChat);

        var initialBotMessage = this._promptOptions.InitialBotMessage;
        await this.SaveResponseAsync(initialBotMessage, newChat.Id);

        this._logger.LogDebug("Created chat session with id {0} for user {1}", newChat.Id, userId);
        return this.CreatedAtAction(nameof(this.GetChatSessionByIdAsync), new { chatId = newChat.Id }, newChat);
    }

    /// <summary>
    /// Get a chat session by id.
    /// </summary>
    /// <param name="chatId">The chat id.</param>
    [HttpGet]
    [ActionName("GetChatSessionByIdAsync")]
    [Route("chatSessions/{chatId:guid}")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [Authorize(Policy = AuthPolicyName.RequireChatOwner)]
    public async Task<IActionResult> GetChatSessionByIdAsync(Guid chatId)
    {
        var chat = await this._chatSessionRepository.FindByIdAsync(chatId.ToString());
        if (chat == null)
        {
            return this.NotFound($"Chat of id {chatId} not found.");
        }

        return this.Ok(chat);
    }

    /// <summary>
    /// Get all chat sessions associated with the logged in user. Return an empty list if no chats are found.
    /// </summary>
    [HttpGet]
    [Route("chatSessions")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetAllChatSessionsAsync()
    {
        var userId = this._authInfo.UserId;
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
    [Route("chatSessions/{chatId:guid}/messages")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [Authorize(Policy = AuthPolicyName.RequireChatOwner)]
    public async Task<IActionResult> GetChatMessagesAsync(
        Guid chatId,
        [FromQuery] int startIdx = 0,
        [FromQuery] int count = -1)
    {
        // TODO: the code mixes strings and Guid without being explicit about the serialization format
        var chatMessages = await this._chatMessageRepository.FindByChatIdAsync(chatId.ToString());
        if (chatMessages == null)
        {
            return this.NotFound($"No messages found for chat id '{chatId}'.");
        }

        chatMessages = chatMessages.OrderByDescending(m => m.Timestamp).Skip(startIdx);
        if (count >= 0) { chatMessages = chatMessages.Take(count); }

        return this.Ok(chatMessages);
    }

    /// <summary>
    /// Edit a chat session.
    /// </summary>
    /// <param name="chatId">Chat id from the url.</param>
    /// <param name="chatParameters">Object that contains the parameters to edit the chat.</param>
    [HttpPatch]
    [Route("chatSessions/{chatId:guid}")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [Authorize(Policy = AuthPolicyName.RequireChatOwner)]
    public async Task<IActionResult> EditChatSessionAsync(Guid chatId, [FromBody] ChatSessionEditOptions chatParameters)
    {
        ChatSession? chat = await this._chatSessionRepository.FindByIdAsync(chatId.ToString());
        if (chat == null)
        {
            return this.NotFound($"Chat with id {chatId} not found.");
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
