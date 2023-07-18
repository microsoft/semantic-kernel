// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Memory;
using SemanticKernel.Service.CopilotChat.Options;
using SemanticKernel.Service.CopilotChat.Skills.ChatSkills;
using SemanticKernel.Service.CopilotChat.Storage;

namespace SemanticKernel.Service.CopilotChat.Controllers;

/// <summary>
/// Controller for getting chat session semantic memory data.
/// </summary>
[ApiController]
[Authorize]
public class ChatMemoryController : ControllerBase
{
    private readonly ILogger<ChatMemoryController> _logger;

    private readonly PromptsOptions _promptOptions;

    private readonly ChatSessionRepository _chatSessionRepository;

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatMemoryController"/> class.
    /// </summary>
    /// <param name="logger">The logger.</param>
    /// <param name="promptsOptions">The prompts options.</param>
    /// <param name="chatParticipantRepository">The chat participant repository.</param>
    public ChatMemoryController(
        ILogger<ChatMemoryController> logger,
        IOptions<PromptsOptions> promptsOptions,
        ChatSessionRepository chatSessionRepository)
    {
        this._logger = logger;
        this._promptOptions = promptsOptions.Value;
        this._chatSessionRepository = chatSessionRepository;
    }

    /// <summary>
    /// Join a use to a chat session given a chat id and a user id.
    /// </summary>
    /// <param name="messageRelayHubContext">Message Hub that performs the real time relay service.</param>
    /// <param name="chatParticipantParam">Contains the user id and chat id.</param>
    [HttpGet]
    [Route("chatMemory/{chatId:guid}/{memoryName}")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> GetSemanticMemoriesAsync(
        [FromServices] ISemanticTextMemory semanticTextMemory,
        [FromRoute] string chatId,
        [FromRoute] string memoryName)
    {
        // Make sure the chat session exists.
        if (!await this._chatSessionRepository.TryFindByIdAsync(chatId, v => _ = v))
        {
            return this.BadRequest("Chat session does not exist.");
        }

        // Make sure the memory name is valid.
        if (!this.ValidateMemoryName(memoryName))
        {
            return this.BadRequest("Memory name is invalid.");
        }

        // Gather the requested semantic memory.
        List<string> memories = new();
        var results = semanticTextMemory.SearchAsync(
            SemanticChatMemoryExtractor.MemoryCollectionName(chatId, memoryName),
            "abc", // dummy query since we don't care about relevance. An empty string will cause exception.
            limit: 100,
            minRelevanceScore: 0.0);
        await foreach (var memory in results)
        {
            memories.Add(memory.Metadata.Text);
        }

        Console.WriteLine($"Found {memories.Count} memories for {memoryName}.");

        return this.Ok(memories);
    }

    #region Private

    /// <summary>
    /// Validates the memory name.
    /// </summary>
    /// <param name="memoryName">Name of the memory requested.</param>
    /// <returns>True if the memory name is valid.</returns>
    private bool ValidateMemoryName(string memoryName)
    {
        return this._promptOptions.MemoryMap.ContainsKey(memoryName);
    }

    # endregion
}
