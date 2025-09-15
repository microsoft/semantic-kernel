// Copyright (c) Microsoft. All rights reserved.

using System;
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
        ValidateChatHistory(request.ChatHistory);

        // Add the "question" argument used in the agent template.
        var arguments = new KernelArguments
        {
            ["question"] = request.Prompt
        };

        request.ChatHistory.AddUserMessage(request.Prompt);

        if (request.IsStreaming)
        {
            return this.Ok(this.CompleteSteamingAsync(request.ChatHistory, arguments, cancellationToken));
        }

        return this.Ok(this.CompleteAsync(request.ChatHistory, arguments, cancellationToken));
    }

    /// <summary>
    /// Completes the agent request.
    /// </summary>
    /// <param name="chatHistory">The chat history.</param>
    /// <param name="arguments">The kernel arguments.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The completion result.</returns>
    private async IAsyncEnumerable<ChatMessageContent> CompleteAsync(ChatHistory chatHistory, KernelArguments arguments, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        var thread = new ChatHistoryAgentThread(chatHistory);
        IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> content =
            this._agent.InvokeAsync(thread, options: new() { KernelArguments = arguments }, cancellationToken: cancellationToken);

        await foreach (ChatMessageContent item in content.ConfigureAwait(false))
        {
            yield return item;
        }
    }

    /// <summary>
    /// Completes the agent request with streaming.
    /// </summary>
    /// <param name="chatHistory">The chat history.</param>
    /// <param name="arguments">The kernel arguments.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The completion result.</returns>
    private async IAsyncEnumerable<StreamingChatMessageContent> CompleteSteamingAsync(ChatHistory chatHistory, KernelArguments arguments, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        var thread = new ChatHistoryAgentThread(chatHistory);
        IAsyncEnumerable<AgentResponseItem<StreamingChatMessageContent>> content =
            this._agent.InvokeStreamingAsync(thread, options: new() { KernelArguments = arguments }, cancellationToken: cancellationToken);

        await foreach (StreamingChatMessageContent item in content.ConfigureAwait(false))
        {
            yield return item;
        }
    }

    /// <summary>
    /// Validates the chat history.
    /// </summary>
    /// <param name="chatHistory">The chat history to validate.</param>
    private static void ValidateChatHistory(ChatHistory chatHistory)
    {
        foreach (ChatMessageContent content in chatHistory)
        {
            if (content.Role == AuthorRole.System)
            {
                throw new ArgumentException("A system message is provided by the agent and should not be included in the chat history.");
            }
        }
    }
}
