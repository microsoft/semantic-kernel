// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;

namespace ChatWithAgent.ApiService;

/// <summary>
/// Controller for agent completions.
/// </summary>
[ApiController]
[Route("agent/completions")]
public sealed class AgentCompletionsController : ControllerBase
{
    private readonly ChatCompletionAgent _agent;
    private readonly ILogger<AgentCompletionsController> _logger;

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentCompletionsController"/> class.
    /// </summary>
    /// <param name="agent">The agent.</param>
    /// <param name="logger">The logger.</param>
    public AgentCompletionsController(ChatCompletionAgent agent, ILogger<AgentCompletionsController> logger)
    {
        this._agent = agent;
        this._logger = logger;
    }

    /// <summary>
    /// Completes the agent request.
    /// </summary>
    /// <param name="request">The request.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    [HttpPost]
    public async Task<IActionResult> CompleteAsync([FromBody] AgentCompletionRequest request, CancellationToken cancellationToken)
    {
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage(request.Prompt);

        if (request.IsStreaming)
        {
            return this.Ok(this.CompleteSteamingAsync(chatHistory, cancellationToken));
        }

        return this.Ok(this.CompleteAsync(chatHistory, cancellationToken));
    }

    /// <summary>
    /// Completes the agent request.
    /// </summary>
    /// <param name="chatHistory">The chat history.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The completion result.</returns>
    private async IAsyncEnumerable<ChatMessageContent> CompleteAsync(ChatHistory chatHistory, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        IAsyncEnumerable<ChatMessageContent> content = this._agent.InvokeAsync(chatHistory, cancellationToken: cancellationToken);

        await foreach (ChatMessageContent item in content.ConfigureAwait(false))
        {
            yield return item;
        }
    }

    /// <summary>
    /// Completes the agent request with streaming.
    /// </summary>
    /// <param name="chatHistory">The chat history.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The completion result.</returns>
    private async IAsyncEnumerable<StreamingChatMessageContent> CompleteSteamingAsync(ChatHistory chatHistory, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        IAsyncEnumerable<StreamingChatMessageContent> content = this._agent.InvokeStreamingAsync(chatHistory, cancellationToken: cancellationToken);

        await foreach (StreamingChatMessageContent item in content.ConfigureAwait(false))
        {
            yield return item;
        }
    }
}
