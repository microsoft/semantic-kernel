// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;
using Microsoft.AgentRuntime.Core;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Broadcast;

/// <summary>
/// An <see cref="AgentActor"/> used with the <see cref="BroadcastOrchestration{TInput, TOutput}"/>.
/// </summary>
internal sealed class BroadcastActor : AgentActor, IHandle<BroadcastMessages.Task>
{
    private readonly AgentType _orchestrationType;

    /// <summary>
    /// Initializes a new instance of the <see cref="BroadcastActor"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="agent">An <see cref="Agent"/>.</param>
    /// <param name="orchestrationType">Identifies the orchestration agent.</param>
    public BroadcastActor(AgentId id, IAgentRuntime runtime, Agent agent, AgentType orchestrationType) :
        base(id, runtime, agent, noThread: true)
    {
        this._orchestrationType = orchestrationType;
    }

    /// <inheritdoc/>
    public async ValueTask HandleAsync(BroadcastMessages.Task item, MessageContext messageContext)
    {
        Trace.WriteLine($"> BROADCAST ACTOR: {this.Id.Type} INPUT - {item.Message}");

        ChatMessageContent response = await this.InvokeAsync(item.Message, messageContext.CancellationToken).ConfigureAwait(false);

        Trace.WriteLine($"> BROADCAST ACTOR: {this.Id.Type} OUTPUT - {response}");

        await this.SendMessageAsync(response.ToBroadcastResult(), this._orchestrationType, messageContext.CancellationToken).ConfigureAwait(false);
    }
}
