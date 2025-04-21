//// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Runtime;
using Microsoft.SemanticKernel.Agents.Runtime.Core;

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
    /// <param name="logger">The logger to use for the actor</param>
    public SequentialActor(AgentId id, IAgentRuntime runtime, Agent agent, AgentType nextAgent, ILogger<SequentialActor>? logger = null)
        : base(id, runtime, agent, noThread: true, logger)
    {
        this._nextAgent = nextAgent;
    }

    /// <inheritdoc/>
    public async ValueTask HandleAsync(SequentialMessage item, MessageContext messageContext)
    {
        this.Logger.LogSequentialAgentInvoke(this.Id, item.Message.Content);

        ChatMessageContent response = await this.InvokeAsync(item.Message, messageContext.CancellationToken).ConfigureAwait(false);

        this.Logger.LogSequentialAgentResult(this.Id, response.Content);

        await this.SendMessageAsync(SequentialMessage.FromChat(response), this._nextAgent, messageContext.CancellationToken).ConfigureAwait(false);
    }
}
