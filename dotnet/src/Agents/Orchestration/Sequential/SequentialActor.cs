//// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;
using Microsoft.AgentRuntime.Core;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Sequential;

/// <summary>
/// An actor used with the <see cref="SequentialOrchestration{TInput,TOutput}"/>.
/// </summary>
internal sealed class SequentialActor : AgentActor, IHandle<SequentialMessage>
{
    private readonly AgentType _nextAgent;

    /// <summary>
    /// Initializes a new instance of the <see cref="SequentialActor"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="agent">An <see cref="Agent"/>.</param>
    /// <param name="nextAgent">The identifier of the next agent for which to handoff the result</param>
    public SequentialActor(AgentId id, IAgentRuntime runtime, Agent agent, AgentType nextAgent)
        : base(id, runtime, agent, noThread: true)
    {
        this._nextAgent = nextAgent;
    }

    /// <inheritdoc/>
    public async ValueTask HandleAsync(SequentialMessage item, MessageContext messageContext)
    {
        Trace.WriteLine($"> SEQUENTIAL ACTOR: {this.Id.Type} INPUT - {item.Content}");

        ChatMessageContent response = await this.InvokeAsync(item.Content, messageContext.CancellationToken).ConfigureAwait(false);

        Trace.WriteLine($"> SEQUENTIAL ACTOR: {this.Id.Type} OUTPUT - {response}");

        await this.SendMessageAsync(SequentialMessage.FromChat(response), this._nextAgent, messageContext.CancellationToken).ConfigureAwait(false);
    }
}
