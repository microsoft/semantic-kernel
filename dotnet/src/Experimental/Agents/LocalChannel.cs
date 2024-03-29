// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Experimental.Agents.Exceptions;
using Microsoft.SemanticKernel.Experimental.Agents.Extensions;

namespace Microsoft.SemanticKernel.Experimental.Agents;

#pragma warning disable IDE0290 // Use primary constructor

/// <summary>
/// A <see cref="AgentChannel"/> specialization for use with local <see cref="ChatHistory"/>.
/// </summary>
//public class LocalChannel<TAgent> : AgentChannel<TAgent> where TAgent : Agent, ILocalAgent
public class LocalChannel : AgentChannel
{
    private readonly ChatHistory _chat;

    /// <inheritdoc/>
    protected internal override async IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        Agent agent,
        ChatMessageContent? input,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        if (agent is not ILocalAgent localAgent)
        {
            throw new AgentException($"Invalid channel binding for agent: {agent.Id} ({agent.GetType().FullName})");
        }

        if (input.TryGetContent(out var _))
        {
            this._chat.Add(input!);
        }

        await foreach (var message in localAgent.InvokeAsync(this._chat, cancellationToken))
        {
            this._chat.Add(message);

            yield return message;
        }
    }

    /// <inheritdoc/>
    protected internal override Task RecieveAsync(IEnumerable<ChatMessageContent> history, CancellationToken cancellationToken)
    {
        this._chat.AddRange(history);

        return Task.CompletedTask;
    }

    /// <inheritdoc/>
    protected internal override IAsyncEnumerable<ChatMessageContent> GetHistoryAsync(CancellationToken cancellationToken)
    {
        return this._chat.ToDescending();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="LocalChannel"/> class.
    /// </summary>
    public LocalChannel()
    {
        this._chat = [];
    }
}
