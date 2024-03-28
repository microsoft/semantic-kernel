// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Experimental.Agents;

#pragma warning disable IDE0290 // Use primary constructor

/// <summary>
/// A <see cref="AgentChannel"/> specialization for use with local <see cref="ChatHistory"/>.
/// </summary>
//public class LocalChannel<TAgent> : AgentChannel<TAgent> where TAgent : Agent, ILocalAgent
public class LocalChannel : AgentChannel
{
    private readonly ChatHistory _chat;
    private readonly ILocalAgent _agent;

    /// <inheritdoc/>
    protected internal override async IAsyncEnumerable<ChatMessageContent> InvokeAsync(Agent agent, ChatMessageContent? input, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (input != null)
        {
            this._chat.Add(input);
        }

        await foreach (var message in this._agent.InvokeAsync(this._chat, cancellationToken))
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
        return this._chat.Reverse().ToAsyncEnumerable(); // $$$ PERF
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="LocalChannel"/> class.
    /// </summary>
    public LocalChannel(ILocalAgent agent)
    {
        this._chat = new();
        this._agent = agent;
    }
}
