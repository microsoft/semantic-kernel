// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// A <see cref="AgentChannel"/> specialization for use with local <see cref="ChatHistory"/>.
/// </summary>
public class LocalChannel<TAgent> : AgentChannel<TAgent> where TAgent : Agent
{
    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="agent"></param>
    /// <param name="chat"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public delegate IAsyncEnumerable<ChatMessageContent> AgentInvocationAsync(TAgent agent, ChatHistory chat, CancellationToken cancellationToken);

    private readonly ChatHistory _chat;
    private readonly AgentInvocationAsync _agentInvoker;

    /// <inheritdoc/>
    protected override IAsyncEnumerable<ChatMessageContent> InvokeAsync(TAgent agent, ChatMessageContent? input, CancellationToken cancellationToken)
    {
        return this._agentInvoker.Invoke(agent, new ChatHistory(this._chat), cancellationToken);
    }

    /// <inheritdoc/>
    public override Task RecieveAsync(IEnumerable<ChatMessageContent> history, CancellationToken cancellationToken)
    {
        return Task.CompletedTask;
    }

    /// <inheritdoc/>
    public override IAsyncEnumerable<ChatMessageContent> GetHistoryAsync(CancellationToken cancellationToken)
    {
        return this._chat.Reverse().ToAsyncEnumerable();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="LocalChannel{TAgent}"/> class.
    /// </summary>
    public LocalChannel(AgentNexus nexus, AgentInvocationAsync agentInvoker)
    {
        this._chat = nexus.History;
        this._agentInvoker = agentInvoker;
    }
}
