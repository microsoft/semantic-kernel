// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;
using Microsoft.AgentRuntime.Core;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Concurrent;

/// <summary>
/// An <see cref="AgentActor"/> used with the <see cref="ConcurrentOrchestration{TInput, TOutput}"/>.
/// </summary>
internal sealed class ConcurrentActor : AgentActor, IHandle<ConcurrentMessages.Request>
{
    private readonly AgentType _orchestrationType;

    /// <summary>
    /// Initializes a new instance of the <see cref="ConcurrentActor"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="agent">An <see cref="Agent"/>.</param>
    /// <param name="orchestrationType">Identifies the orchestration agent.</param>
    public ConcurrentActor(AgentId id, IAgentRuntime runtime, Agent agent, AgentType orchestrationType) :
        base(id, runtime, agent, noThread: true)
    {
        this._orchestrationType = orchestrationType;
    }

    /// <inheritdoc/>
    public async ValueTask HandleAsync(ConcurrentMessages.Request item, MessageContext messageContext)
    {
        Trace.WriteLine($"> CONCURRENT ACTOR: {this.Id.Type} INPUT - {item.Message}");

        ChatMessageContent response = await this.InvokeAsync(item.Message, messageContext.CancellationToken).ConfigureAwait(false);

        Trace.WriteLine($"> CONCURRENT ACTOR: {this.Id.Type} OUTPUT - {response}");

        await this.SendMessageAsync(response.ToResult(), this._orchestrationType, messageContext.CancellationToken).ConfigureAwait(false);
    }
}
