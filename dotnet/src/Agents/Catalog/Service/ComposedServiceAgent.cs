// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.Service;

/// <summary>
/// A <see cref="ServiceAgent"/> specialiation that is generates responses
/// via an inner agent.
/// </summary>
public abstract class ComposedServiceAgent : ServiceAgent
{
    private Agent? _agent;

    /// <summary>
    /// Factory for initializing the agent.
    /// </summary>
    protected abstract Task<Agent> CreateAgentAsync();

    /// <inheritdoc/>
    public override async IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> InvokeAsync(
        ICollection<ChatMessageContent> messages,
        AgentThread? thread = null,
        AgentInvokeOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        messages ??= [];

        Agent agent = await this.GetAgentAsync().ConfigureAwait(false);

        IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> responses = agent.InvokeAsync(messages, thread, options, cancellationToken);
        await foreach (AgentResponseItem<ChatMessageContent> response in responses.ConfigureAwait(false))
        {
            yield return response;
        }
    }

    /// <inheritdoc/>
    public override async IAsyncEnumerable<AgentResponseItem<StreamingChatMessageContent>> InvokeStreamingAsync(
        ICollection<ChatMessageContent> messages,
        AgentThread? thread = null,
        AgentInvokeOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        messages ??= [];

        Agent agent = await this.GetAgentAsync().ConfigureAwait(false);

        IAsyncEnumerable<AgentResponseItem<StreamingChatMessageContent>> responses =
            agent.InvokeStreamingAsync(messages, thread, options, cancellationToken);
        await foreach (AgentResponseItem<StreamingChatMessageContent> response in responses.ConfigureAwait(false))
        {
            yield return response;
        }
    }

    private async Task<Agent> GetAgentAsync()
    {
        this._agent ??= await this.CreateAgentAsync().ConfigureAwait(false);
        return this._agent;
    }
}
