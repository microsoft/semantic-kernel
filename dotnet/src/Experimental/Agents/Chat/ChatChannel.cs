// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Experimental.Agents.Chat;

/// <summary>
/// $$$
/// </summary>
public sealed class ChatChannel : AgentChannel
{
    private ChatHistory? _chat;

    /// <inheritdoc/>
    public override void Init(AgentNexus nexus)
    {
        this._chat = nexus.AgentHistory;
    }

    /// <inheritdoc/>
    public override async Task<IEnumerable<ChatMessageContent>> InvokeAsync(KernelAgent agent, ChatMessageContent? message, CancellationToken cancellationToken)
    {
        var chatCompletionService = agent.Kernel.GetRequiredService<IChatCompletionService>();

        var chatMessageContent =
            await chatCompletionService.GetChatMessageContentsAsync(
                this._chat!,
                executionSettings: null, // $$$
                agent.Kernel,
                cancellationToken).ConfigureAwait(false);

        return chatMessageContent;
    }

    /// <inheritdoc/>
    public override Task RecieveAsync(IEnumerable<ChatMessageContent> content, CancellationToken cancellationToken)
    {
        return Task.CompletedTask;
    }

    ///// <summary>
    ///// $$$
    ///// </summary>
    //public ChatChannel()
    //{
    //}
}
