// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;
using Microsoft.SemanticKernel.Agents.Orchestration.Broadcast;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// A <see cref="ManagedAgent"/> built around a <see cref="Agent"/>.
/// </summary>
internal sealed class BroadcastProxy : AgentProxy
{
    private readonly AgentType _recieverType;

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentProxy"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="agent">An <see cref="Agent"/>.</param>
    /// <param name="recieverType">// %%%</param>
    public BroadcastProxy(AgentId id, IAgentRuntime runtime, Agent agent, AgentType recieverType)
        : base(id, runtime, agent)
    {
        this.RegisterHandler<BroadcastMessages.Task>(this.OnTaskAsync);
        this._recieverType = recieverType;
    }

    /// <inheritdoc/>
    private async ValueTask OnTaskAsync(BroadcastMessages.Task message, MessageContext context)
    {
        // %%% TODO: Input
        AgentResponseItem<ChatMessageContent>[] responses = await this.Agent.InvokeAsync([]).ToArrayAsync().ConfigureAwait(false);
        AgentResponseItem<ChatMessageContent> response = responses.First();
        await this.SendMessageAsync(response.Message, this._recieverType).ConfigureAwait(false); // %% CARDINALITY
        await response.Thread.DeleteAsync().ConfigureAwait(false);
    }
}
