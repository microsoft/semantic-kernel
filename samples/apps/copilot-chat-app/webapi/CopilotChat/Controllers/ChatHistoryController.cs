// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.SignalR;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Microsoft.SemanticKernel;
using SemanticKernel.Service.CopilotChat.Hubs;
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
    private readonly ChatParticipantRepository _participantRepository;
    private readonly ChatMemorySourceRepository _sourceRepository;
    private readonly PromptsOptions _promptOptions;
    private const string ChatEditedClientCall = "ChatEdited";

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatHistoryController"/> class.
    /// </summary>
    /// <param name="logger">The logger.</param>
    /// <param name="sessionRepository">The chat session repository.</param>
    /// <param name="messageRepository">The chat message repository.</param>
    /// <param name="participantRepository">The chat participant repository.</param>
    /// <param name="sourceRepository">The chat memory resource repository.</param>
    /// <param name="promptsOptions">The prompts options.</param>
    public ChatHistoryController(
        ILogger<ChatHistoryController> logger,
        ChatSessionRepository sessionRepository,
        ChatMessageRepository messageRepository,
        ChatParticipantRepository participantRepository,
        ChatMemorySourceRepository sourceRepository,
        IOptions<PromptsOptions> promptsOptions)
    {
        this._logger = logger;
        this._sessionRepository = sessionRepository;
        this._messageRepository = messageRepository;
        this._participantRepository = participantRepository;
        this._sourceRepository = sourceRepository;
        this._promptOptions = promptsOptions.Value;
    }

    /// <summary>
    /// Create a new chat session and populate the session with the initial bot message.
    /// </summary>
    /// <param name="chatParameter">Contains the title of the chat.</param>
    /// <returns>The HTTP action result.</returns>
    [HttpPost]
    [Route("chatSession/create")]
    [ProducesResponseType(StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> CreateChatSessionAsync([FromBody] CreateChatParameters chatParameter)
    {
        if (chatParameter.UserId == null || chatParameter.Title == null)
        {
            return this.BadRequest("Chat session parameters cannot be null.");
        }

        // Create a new chat session
        var newChat = new ChatSession(chatParameter.Title);
        await this._sessionRepository.CreateAsync(newChat);

        var initialBotMessage = this._promptOptions.InitialBotMessage;
        // The initial bot message doesn't need a prompt.
        var chatMessage = ChatMessage.CreateBotResponseMessage(
            newChat.Id,
            initialBotMessage,
            string.Empty);
        await this._messageRepository.CreateAsync(chatMessage);

        // Add the user to the chat session
        await this._participantRepository.CreateAsync(new ChatParticipant(chatParameter.UserId, newChat.Id));

        this._logger.LogDebug("Created chat session with id {0}.", newChat.Id);
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
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetChatSessionByIdAsync(Guid chatId)
    {
        ChatSession? chat = null;
        if (await this._sessionRepository.TryFindByIdAsync(chatId.ToString(), v => chat = v))
        {
            return this.Ok(chat);
        }

        return this.NotFound($"No chat session found for chat id '{chatId}'.");
    }

    /// <summary>
    /// Get all chat sessions associated with a user. Return an empty list if no chats are found.
    /// The regex pattern that is used to match the user id will match the following format:
    ///    - 2 period separated groups of one or more hyphen-delimited alphanumeric strings.
    /// The pattern matches two GUIDs in canonical textual representation separated by a period.
    /// </summary>
    /// <param name="userId">The user id.</param>
    /// <returns>A list of chat sessions. An empty list if the user is not in any chat session.</returns>
    [HttpGet]
    [Route("chatSession/getAllChats/{userId:regex(([[a-z0-9]]+-)+[[a-z0-9]]+\\.([[a-z0-9]]+-)+[[a-z0-9]]+)}")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetAllChatSessionsAsync(string userId)
    {
        // Get all participants that belong to the user.
        // Then get all the chats from the list of participants.
        var chatParticipants = await this._participantRepository.FindByUserIdAsync(userId);

        var chats = new List<ChatSession>();
        foreach (var chatParticipant in chatParticipants)
        {
            ChatSession? chat = null;
            if (await this._sessionRepository.TryFindByIdAsync(chatParticipant.ChatId, v => chat = v))
            {
                chats.Add(chat!);
            }
            else
            {
                this._logger.LogDebug(
                    "Failed to find chat session with id {0} for participant {1}", chatParticipant.ChatId, chatParticipant.Id);
                return this.NotFound(
                    $"Failed to find chat session with id {chatParticipant.ChatId} for participant {chatParticipant.Id}");
            }
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
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetChatMessagesAsync(
        Guid chatId,
        [FromQuery] int startIdx = 0,
        [FromQuery] int count = -1)
    {
        // TODO: the code mixes strings and Guid without being explicit about the serialization format
        var chatMessages = await this._messageRepository.FindByChatIdAsync(chatId.ToString());
        if (!chatMessages.Any())
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
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> EditChatSessionAsync(
        [FromServices] IHubContext<MessageRelayHub> messageRelayHubContext,
        [FromBody] ChatSession chatParameters)
    {
        string chatId = chatParameters.Id;

        ChatSession? chat = null;
        if (await this._sessionRepository.TryFindByIdAsync(chatId, v => chat = v))
        {
            chat!.Title = chatParameters.Title;
            await this._sessionRepository.UpsertAsync(chat);
            await messageRelayHubContext.Clients.Group(chatId).SendAsync(ChatEditedClientCall, chat);
            return this.Ok(chat);
        }

        return this.NotFound($"No chat session found for chat id '{chatId}'.");
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

        if (await this._sessionRepository.TryFindByIdAsync(chatId.ToString(), v => _ = v))
        {
            var sources = await this._sourceRepository.FindByChatIdAsync(chatId.ToString());
            return this.Ok(sources);
        }

        return this.NotFound($"No chat session found for chat id '{chatId}'.");
    }
}
