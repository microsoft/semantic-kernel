// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.AzureAI.Internal;
using AzureAIP = Azure.AI.Projects;

namespace Microsoft.SemanticKernel.Agents.AzureAI;

/// <summary>
/// A <see cref="AgentChannel"/> specialization for use with <see cref="AzureAIAgent"/>.
/// </summary>
internal sealed class AzureAIChannel(AzureAIP.AgentsClient client, string threadId)
    : AgentChannel<AzureAIAgent>
{
    /// <inheritdoc/>
    protected override async Task ReceiveAsync(IEnumerable<ChatMessageContent> history, CancellationToken cancellationToken)
    {
        foreach (ChatMessageContent message in history)
        {
            await AgentThreadActions.CreateMessageAsync(client, threadId, message, cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    protected override IAsyncEnumerable<(bool IsVisible, ChatMessageContent Message)> InvokeAsync(
        AzureAIAgent agent,
        CancellationToken cancellationToken)
    {
        agent.ThrowIfDeleted();

        // %%%
        //return AgentThreadActions.InvokeAsync(agent, client, threadId, invocationOptions: null, this.Logger, agent.Kernel, agent.Arguments, cancellationToken);
        return Array.Empty<(bool, ChatMessageContent)>().ToAsyncEnumerable();
    }

    /// <inheritdoc/>
    protected override IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(AzureAIAgent agent, IList<ChatMessageContent> messages, CancellationToken cancellationToken = default)
    {
        agent.ThrowIfDeleted();

        // %%%
        //return AgentThreadActions.InvokeStreamingAsync(agent, client, threadId, messages, invocationOptions: null, this.Logger, agent.Kernel, agent.Arguments, cancellationToken);
        return Array.Empty<StreamingChatMessageContent>().ToAsyncEnumerable();
    }

    /// <inheritdoc/>
    protected override IAsyncEnumerable<ChatMessageContent> GetHistoryAsync(CancellationToken cancellationToken)
    {
        return AgentThreadActions.GetMessagesAsync(client, threadId, cancellationToken);
    }

    /// <inheritdoc/>
    protected override Task ResetAsync(CancellationToken cancellationToken = default)
    {
        return client.DeleteThreadAsync(threadId, cancellationToken);
    }

    /// <inheritdoc/>
    protected override string Serialize() { return threadId; }
}
