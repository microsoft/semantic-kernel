// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.Projects;
using Microsoft.SemanticKernel.Agents.AzureAI.Internal;

namespace Microsoft.SemanticKernel.Agents.AzureAI;

/// <summary>
/// A <see cref="AgentChannel"/> specialization for use with <see cref="AzureAIAgent"/>.
/// </summary>
internal sealed class AzureAIChannel(AgentsClient client, string threadId)
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
        return AgentThreadActions.InvokeAsync(agent, client, threadId, invocationOptions: null, this.Logger, agent.Kernel, agent.Arguments, cancellationToken);
    }

    /// <inheritdoc/>
    protected override IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(AzureAIAgent agent, IList<ChatMessageContent> messages, CancellationToken cancellationToken = default)
    {
        return AgentThreadActions.InvokeStreamingAsync(agent, client, threadId, messages, invocationOptions: null, this.Logger, agent.Kernel, agent.Arguments, cancellationToken);
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
