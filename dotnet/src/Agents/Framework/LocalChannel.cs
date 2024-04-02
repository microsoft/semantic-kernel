// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Extensions;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// A <see cref="AgentChannel"/> specialization for managing local message history.
/// </summary>
public class LocalChannel : AgentChannel
{
    private readonly ChatHistory _chat;

    /// <inheritdoc/>
    protected internal sealed override async IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        Agent agent,
        ChatMessageContent? input,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        if (agent is not ILocalAgent localAgent)
        {
            throw new AgentException($"Invalid channel binding for agent: {agent.Id} ({agent.GetType().FullName})");
        }

        if (input.HasContent())
        {
            this._chat.Add(input!);
        }

        IAsyncEnumerable<ChatMessageContent> messages = localAgent.InvokeAsync(this._chat, cancellationToken);
        if (messages != null)
        {
            await foreach (var message in messages)
            {
                this._chat.Add(message);

                yield return message;
            }
        }
    }

    /// <inheritdoc/>
    protected internal sealed override Task ReceiveAsync(IEnumerable<ChatMessageContent> history, CancellationToken cancellationToken)
    {
        this._chat.AddRange(history);

        return Task.CompletedTask;
    }

    /// <inheritdoc/>
    protected internal sealed override IAsyncEnumerable<ChatMessageContent> GetHistoryAsync(CancellationToken cancellationToken)
    {
        return this._chat.ToDescendingAsync();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="LocalChannel"/> class.
    /// </summary>
    public LocalChannel()
    {
        this._chat = new();
    }
}
