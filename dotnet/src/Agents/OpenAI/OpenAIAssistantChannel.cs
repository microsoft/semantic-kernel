// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI.Assistants;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// A <see cref="AgentChannel"/> specialization for use with <see cref="OpenAIAssistantAgent"/>.
/// </summary>
internal sealed class OpenAIAssistantChannel(AssistantsClient client, string threadId, OpenAIAssistantConfiguration.PollingConfiguration pollingConfiguration)
    : AgentChannel<OpenAIAssistantAgent>
{
    private readonly AssistantsClient _client = client;
    private readonly string _threadId = threadId;

    /// <inheritdoc/>
    protected override async Task ReceiveAsync(IEnumerable<ChatMessageContent> history, CancellationToken cancellationToken)
    {
        foreach (ChatMessageContent message in history)
        {
            await AssistantThreadActions.CreateMessageAsync(this._client, this._threadId, message, cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    protected override IAsyncEnumerable<(bool IsVisible, ChatMessageContent Message)> InvokeAsync(
        OpenAIAssistantAgent agent,
        CancellationToken cancellationToken)
    {
        agent.ThrowIfDeleted();

        return AssistantThreadActions.InvokeAsync(agent, this._client, this._threadId, pollingConfiguration, this.Logger, agent.Kernel, agent.Arguments, cancellationToken);
    }

    /// <inheritdoc/>
    protected override IAsyncEnumerable<ChatMessageContent> GetHistoryAsync(CancellationToken cancellationToken)
    {
        return AssistantThreadActions.GetMessagesAsync(this._client, this._threadId, cancellationToken);
    }
}
