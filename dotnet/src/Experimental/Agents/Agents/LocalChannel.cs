// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Experimental.Agents.Agents;

/// <summary>
/// A <see cref="AgentChannel"/> specialization for use with local <see cref="ChatHistory"/>.
/// </summary>
public class LocalChannel<TAgent> : AgentChannel<TAgent> where TAgent : Agent
{
    /// <summary>
    /// Delegate for calling into an agent with locally managed chat-history.
    /// </summary>
    /// <param name="agent">The agent actively interacting with the nexus.</param>
    /// <param name="chat">The nexus history at the point the channel is created.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
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
        return this._chat.Reverse().ToAsyncEnumerable(); // $$$ PERF
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
