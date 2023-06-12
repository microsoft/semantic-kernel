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
using Microsoft.SemanticKernel;
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
[Authorize]
public class ChatHistoryController : ControllerBase
{
    private readonly ILogger<ChatHistoryController> _logger;
    private readonly ChatSessionRepository _sessionRepository;
    private readonly ChatMessageRepository _messageRepository;
    private readonly PromptsOptions _promptOptions;
    private readonly ChatMemorySourceRepository _sourceRepository;

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatHistoryController"/> class.
    /// </summary>
    /// <param name="logger">The logger.</param>
    /// <param name="sessionRepository">The chat session repository.</param>
    /// <param name="messageRepository">The chat message repository.</param>
    /// <param name="sourceRepository">The chat memory resource repository.</param>
    /// <param name="promptsOptions">The prompts options.</param>
    public ChatHistoryController(
        ILogger<ChatHistoryController> logger,
        ChatSessionRepository sessionRepository,
        ChatMessageRepository messageRepository,
        ChatMemorySourceRepository sourceRepository,
        IOptions<PromptsOptions> promptsOptions)
    {
        this._logger = logger;
        this._sessionRepository = sessionRepository;
        this._messageRepository = messageRepository;
        this._sourceRepository = sourceRepository;
        this._promptOptions = promptsOptions.Value;
    }

    /// <summary>
    /// Create a new chat session and populate the session with the initial bot message.
    /// </summary>
    /// <param name="chatParameters">Object that contains the parameters to create a new chat.</param>
    /// <returns>The HTTP action result.</returns>
    [HttpPost]
    [Route("chatSession/create")]
    [ProducesResponseType(StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> CreateChatSessionAsync(
        [FromBody] ChatSession chatParameters)
    {
        var userId = chatParameters.UserId;
        var title = chatParameters.Title;

        var newChat = new ChatSession(userId, title);
        await this._sessionRepository.CreateAsync(newChat);

        var initialBotMessage = this._promptOptions.InitialBotMessage;
        // The initial bot message doesn't need a prompt.
        await this.SaveResponseAsync(initialBotMessage, string.Empty, newChat.Id);

        this._logger.LogDebug("Created chat session with id {0} for user {1}", newChat.Id, userId);
        return this.CreatedAtAction(nameof(this.GetChatSessionByIdAsync), new { chatId = newChat.Id }, newChat);
    }

    /// <summary>
    /// Get a chat session by id.
    /// </summary>
    /// <param name="chatId">The chat id.</param>
    [HttpGet]
    [ActionName("GetChatSessionByIdAsync")]
    [Route("chatSession/getChat/{chatId:guid}")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetChatSessionByIdAsync(Guid chatId)
    {
        ChatSession? chat = null;
        try
        {
            // Make sure the chat session exists
            chat = await this._sessionRepository.FindByIdAsync(chatId.ToString());
        }
        catch (KeyNotFoundException)
        {
            return this.NotFound($"No chat session found for chat id '{chatId}'.");
        }

        return this.Ok(chat);
    }

    /// <summary>
    /// Get all chat sessions associated with a user. Return an empty list if no chats are found.
    /// The regex pattern that is used to match the user id will match the following format:
    ///    - 2 period separated groups of one or more hyphen-delimited alphanumeric strings.
    /// The pattern matches two GUIDs in canonical textual representation separated by a period.
    /// </summary>
    /// <param name="userId">The user id.</param>
    [HttpGet]
    [Route("chatSession/getAllChats/{userId:regex(([[a-z0-9]]+-)+[[a-z0-9]]+\\.([[a-z0-9]]+-)+[[a-z0-9]]+)}")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetAllChatSessionsAsync(string userId)
    {
        var chats = await this._sessionRepository.FindByUserIdAsync(userId);
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
    [Route("chatSession/getChatMessages/{chatId:guid}")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetChatMessagesAsync(
        Guid chatId,
        [FromQuery] int startIdx = 0,
        [FromQuery] int count = -1)
    {
        // TODO: the code mixes strings and Guid without being explicit about the serialization format
        var chatMessages = await this._messageRepository.FindByChatIdAsync(chatId.ToString());
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
    /// <param name="chatParameters">Object that contains the parameters to edit the chat.</param>
    [HttpPost]
    [Route("chatSession/edit")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> EditChatSessionAsync([FromBody] ChatSession chatParameters)
    {
        string chatId = chatParameters.Id;

        ChatSession? chat = null;
        try
        {
            // Make sure the chat session exists
            chat = await this._sessionRepository.FindByIdAsync(chatId);
        }
        catch (KeyNotFoundException)
        {
            return this.NotFound($"No chat session found for chat id '{chatId}'.");
        }

        chat.Title = chatParameters.Title;
        await this._sessionRepository.UpsertAsync(chat);

        return this.Ok(chat);
    }

    /// <summary>
    /// Service API to get a list of imported sources.
    /// </summary>
    [Authorize]
    [Route("chatSession/{chatId:guid}/sources")]
    [HttpGet]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<IEnumerable<MemorySource>>> GetSourcesAsync(
        [FromServices] IKernel kernel,
        Guid chatId)
    {
        this._logger.LogInformation("Get imported sources of chat session {0}", chatId);

        try
        {
            // Make sure the chat session exists
            await this._sessionRepository.FindByIdAsync(chatId.ToString());
        }
        catch (KeyNotFoundException)
        {
            return this.NotFound($"No chat session found for chat id '{chatId}'.");
        }

        return this.Ok(await this._sourceRepository.FindByChatIdAsync(chatId.ToString()));
    }

    # region Private

    /// <summary>
    /// Save a bot response to the chat session.
    /// </summary>
    /// <param name="response">The bot response.</param>
    /// <param name="prompt">The prompt that was used to generate the response.</param>
    /// <param name="chatId">The chat id.</param>
    private async Task SaveResponseAsync(string response, string prompt, string chatId)
    {
        // Make sure the chat session exists
        await this._sessionRepository.FindByIdAsync(chatId);

        var chatMessage = ChatMessage.CreateBotResponseMessage(chatId, response, prompt);
        await this._messageRepository.CreateAsync(chatMessage);
    }

    # endregion
}
