// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.SignalR;
using Microsoft.Extensions.Logging;
using SemanticKernel.Service.CopilotChat.Hubs;
using SemanticKernel.Service.CopilotChat.Models;
using SemanticKernel.Service.CopilotChat.Storage;

namespace SemanticKernel.Service.CopilotChat.Controllers;

/// <summary>
/// Controller for managing invitations and participants in a chat session.
/// This controller is responsible for:
/// 1. Creating invitation links.
/// 2. Accepting/rejecting invitation links.
/// 3. Managing participants in a chat session.
/// </summary>
[ApiController]
[Authorize]
public class ChatParticipantController : ControllerBase
{
    private const string UserJoinedClientCall = "UserJoined";
    private readonly ILogger<ChatParticipantController> _logger;
    private readonly ChatParticipantRepository _chatParticipantRepository;
    private readonly ChatSessionRepository _chatSessionRepository;

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatParticipantController"/> class.
    /// </summary>
    /// <param name="logger">The logger.</param>
    /// <param name="chatParticipantRepository">The chat participant repository.</param>
    /// <param name="chatSessionRepository">The chat session repository.</param>
    public ChatParticipantController(
        ILogger<ChatParticipantController> logger,
        ChatParticipantRepository chatParticipantRepository,
        ChatSessionRepository chatSessionRepository)
    {
        this._logger = logger;
        this._chatParticipantRepository = chatParticipantRepository;
        this._chatSessionRepository = chatSessionRepository;
    }

    /// <summary>
    /// Join a use to a chat session given a chat id and a user id.
    /// </summary>
    /// <param name="messageRelayHubContext">Message Hub that performs the real time relay service.</param>
    /// <param name="chatParticipantParam">Contains the user id and chat id.</param>
    [HttpPost]
    [Route("chatParticipant/join")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> JoinChatAsync(
        [FromServices] IHubContext<MessageRelayHub> messageRelayHubContext,
        [FromBody] ChatParticipant chatParticipantParam)
    {
        string userId = chatParticipantParam.UserId;
        string chatId = chatParticipantParam.ChatId;

        // Make sure the chat session exists.
        if (!await this._chatSessionRepository.TryFindByIdAsync(chatId, v => _ = v))
        {
            return this.BadRequest("Chat session does not exist.");
        }

        // Make sure the user is not already in the chat session.
        if (await this._chatParticipantRepository.IsUserInChatAsync(userId, chatId))
        {
            return this.BadRequest("User is already in the chat session.");
        }

        var chatParticipant = new ChatParticipant(userId, chatId);
        await this._chatParticipantRepository.CreateAsync(chatParticipant);

        // Broadcast the user joined event to all the connected clients.
        // Note that the client who initiated the request may not have joined the group.
        await messageRelayHubContext.Clients.Group(chatId).SendAsync(UserJoinedClientCall, chatId, userId);

        return this.Ok(chatParticipant);
    }

    /// <summary>
    /// Get a list of chat participants that have the same chat id.
    /// </summary>
    /// <param name="chatId">The Id of the chat to get all the participants from.</param>
    [HttpGet]
    [Route("chatParticipant/getAllParticipants/{chatId:guid}")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetAllParticipantsAsync(Guid chatId)
    {
        // Make sure the chat session exists.
        if (!await this._chatSessionRepository.TryFindByIdAsync(chatId.ToString(), v => _ = v))
        {
            return this.NotFound("Chat session does not exist.");
        }

        var chatParticipants = await this._chatParticipantRepository.FindByChatIdAsync(chatId.ToString());
        return this.Ok(chatParticipants);
    }
}
