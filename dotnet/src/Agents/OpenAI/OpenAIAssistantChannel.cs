﻿// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.OpenAI.Internal;
using OpenAI.Assistants;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// A <see cref="AgentChannel"/> specialization for use with <see cref="OpenAIAssistantAgent"/>.
/// </summary>
internal sealed class OpenAIAssistantChannel(AssistantClient client, string threadId)
    : AgentChannel<OpenAIAssistantAgent>
{
    private readonly AssistantClient _client = client;
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

        return AssistantThreadActions.InvokeAsync(agent, this._client, this._threadId, invocationOptions: null, this.Logger, agent.Kernel, agent.Arguments, cancellationToken);
    }

    /// <inheritdoc/>
    protected override IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(OpenAIAssistantAgent agent, IList<ChatMessageContent> messages, CancellationToken cancellationToken = default)
    {
        return AssistantThreadActions.InvokeStreamingAsync(agent, this._client, this._threadId, messages, invocationOptions: null, this.Logger, agent.Kernel, agent.Arguments, cancellationToken);
    }

    /// <inheritdoc/>
    protected override IAsyncEnumerable<ChatMessageContent> GetHistoryAsync(CancellationToken cancellationToken)
    {
        return AssistantThreadActions.GetMessagesAsync(this._client, this._threadId, cancellationToken);
    }

    /// <inheritdoc/>
    protected override Task ResetAsync(CancellationToken cancellationToken = default) =>
        this._client.DeleteThreadAsync(this._threadId, cancellationToken);
}
