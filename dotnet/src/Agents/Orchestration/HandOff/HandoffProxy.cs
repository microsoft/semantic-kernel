// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;
using Microsoft.SemanticKernel.Agents.Orchestration.Handoff;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// A <see cref="ManagedAgent"/> built around a <see cref="Agent"/>.
/// </summary>
internal sealed class HandoffProxy : AgentProxy
{
    private readonly AgentType _nextAgent;

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentProxy"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="agent">An <see cref="Agent"/>.</param>
    /// <param name="nextAgent">// %%%</param>
    public HandoffProxy(AgentId id, IAgentRuntime runtime, Agent agent, AgentType nextAgent)
        : base(id, runtime, agent)
    {
        this.RegisterHandler<HandoffMessages.Input>(this.OnHandoffAsync);
        this._nextAgent = nextAgent;
    }

    /// <inheritdoc/>
    private async ValueTask OnHandoffAsync(HandoffMessages.Input message, MessageContext context)
    {
        AgentResponseItem<ChatMessageContent>[] responses = await this.Agent.InvokeAsync([message.Task]).ToArrayAsync().ConfigureAwait(false);
        AgentResponseItem<ChatMessageContent> response = responses.First();
        await this.SendMessageAsync(message.Forward(response), this._nextAgent).ConfigureAwait(false); // %% CARDINALITY
        await response.Thread.DeleteAsync().ConfigureAwait(false);
    }
}
