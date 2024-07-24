// Copyright (c) Microsoft. All rights reserved.
using System.Runtime.CompilerServices;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;

namespace AgentWithHistoryTruncation;

internal class TruncatingChatChannel : ChatHistoryChannel
{
    // Capture history by truncation strategy (allows agents within a chat to have mix of same, different or no strategy).
    private readonly Dictionary<object, ChatHistory> _truncatedHistory = [];

    protected override async IAsyncEnumerable<(bool IsVisible, ChatMessageContent Message)> InvokeAsync(Agent agent, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        if (agent is not TruncatingChatAgent truncatingAgent)
        {
            throw new KernelException($"Invalid channel binding for agent: {agent.Id} ({agent.GetType().FullName})");
        }

        ChatHistory truncatedHistory = await this.GetTruncatedHistoryAsync(truncatingAgent.TruncationStrategy, cancellationToken);

        await foreach ((bool isVisible, ChatMessageContent content) in base.InvokeAsync(agent, truncatedHistory, cancellationToken))
        {
            yield return (isVisible, content);
        }
    }

    private async Task<ChatHistory> GetTruncatedHistoryAsync(TruncationStrategy? truncationStrategy, CancellationToken cancellationToken)
    {
        if (truncationStrategy == null)
        {
            return this.History;
        }

        if (!this._truncatedHistory.TryGetValue(truncationStrategy, out ChatHistory? truncatedHistory))
        {
            truncatedHistory = this.History;
        }

        if (truncationStrategy.RequiresTruncation(truncatedHistory))
        {
            // Truncate using the truncated-history or full history? (how to avoid summarizing the summary?)
            truncatedHistory = [.. truncationStrategy.TruncateAsync(truncatedHistory, cancellationToken).ToEnumerable()];

            this._truncatedHistory[truncationStrategy] = truncatedHistory;
        }

        return truncatedHistory;
    }
}
