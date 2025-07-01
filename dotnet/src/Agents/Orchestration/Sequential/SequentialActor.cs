// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Runtime;
using Microsoft.SemanticKernel.Agents.Runtime.Core;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Sequential;

/// <summary>
/// An actor used with the <see cref="SequentialOrchestration{TInput,TOutput}"/>.
/// </summary>
internal sealed class SequentialActor :
    AgentActor,
    IHandle<SequentialMessages.Request>,
    IHandle<SequentialMessages.Response>
{
    private readonly AgentType _nextAgent;

    /// <summary>
    /// Initializes a new instance of the <see cref="SequentialActor"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="context">The orchestration context.</param>
    /// <param name="agent">An <see cref="Agent"/>.</param>
    /// <param name="nextAgent">The identifier of the next agent for which to handoff the result</param>
    /// <param name="logger">The logger to use for the actor</param>
    public SequentialActor(AgentId id, IAgentRuntime runtime, OrchestrationContext context, Agent agent, AgentType nextAgent, ILogger<SequentialActor>? logger = null)
        : base(id, runtime, context, agent, logger)
    {
        logger?.LogInformation("ACTOR {ActorId} {NextAgent}", this.Id, nextAgent);
        this._nextAgent = nextAgent;
    }

    /// <inheritdoc/>
    public async ValueTask HandleAsync(SequentialMessages.Request item, MessageContext messageContext)
    {
        await this.InvokeAgentAsync(item.Messages, messageContext).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async ValueTask HandleAsync(SequentialMessages.Response item, MessageContext messageContext)
    {
        await this.InvokeAgentAsync([item.Message], messageContext).ConfigureAwait(false);
    }

    private async ValueTask InvokeAgentAsync(IList<ChatMessageContent> input, MessageContext messageContext)
    {
        this.Logger.LogInformation("INVOKE {ActorId} {NextAgent}", this.Id, this._nextAgent);

        this.Logger.LogSequentialAgentInvoke(this.Id);

        ChatMessageContent response = await this.InvokeAsync(input, messageContext.CancellationToken).ConfigureAwait(false);

        this.Logger.LogSequentialAgentResult(this.Id, response.Content);

        await this.PublishMessageAsync(response.AsResponseMessage(), this._nextAgent, messageContext.CancellationToken).ConfigureAwait(false);
    }
}
