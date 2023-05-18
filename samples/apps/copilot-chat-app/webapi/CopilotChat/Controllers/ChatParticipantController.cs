// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using SemanticKernel.Service.CopilotChat.Models;
using SemanticKernel.Service.CopilotChat.Storage;

namespace SemanticKernel.Service.CopilotChat.Controllers;

/// <summary>
/// Controller for chat invitations.
/// This controller is responsible for:
/// 1. Creating invitation links.
/// 2. Accepting/rejecting invitation links.
/// 3. Managing participants in a chat session.
/// </summary>
[ApiController]
[Authorize]
public class ChatParticipantController : ControllerBase
{
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
    /// <param name="chatParticipantParam">Contains the user id and chat id.</param>
    [HttpPost]
    [Route("chatParticipant/join")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> JoinChatAsync([FromBody] ChatParticipant chatParticipantParam)
    {
        string userId = chatParticipantParam.UserId;
        string chatId = chatParticipantParam.ChatId;

        // Make sure the chat session exists.
        try
        {
            await this._chatSessionRepository.FindByIdAsync(chatId);
        }
        catch (Exception ex) when (ex is KeyNotFoundException || ex is ArgumentOutOfRangeException)
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

        return this.Ok(chatParticipant);
    }
}
