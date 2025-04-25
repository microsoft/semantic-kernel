// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Runtime;
using Microsoft.SemanticKernel.Agents.Runtime.Core;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Concurrent;

/// <summary>
/// An <see cref="AgentActor"/> used with the <see cref="ConcurrentOrchestration{TInput, TOutput}"/>.
/// </summary>
internal sealed class ConcurrentActor : AgentActor, IHandle<ConcurrentMessages.Request>
{
    private readonly AgentType _handoffActor;

    /// <summary>
    /// Initializes a new instance of the <see cref="ConcurrentActor"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="agent">An <see cref="Agent"/>.</param>
    /// <param name="resultActor">Identifies the actor collecting results.</param>
    /// <param name="logger">The logger to use for the actor</param>
    public ConcurrentActor(AgentId id, IAgentRuntime runtime, Agent agent, AgentType resultActor, ILogger<ConcurrentActor>? logger = null) :
        base(id, runtime, agent, noThread: true, logger)
    {
        this._handoffActor = resultActor;
    }

    /// <inheritdoc/>
    public async ValueTask HandleAsync(ConcurrentMessages.Request item, MessageContext messageContext)
    {
        this.Logger.LogConcurrentAgentInvoke(this.Id, item.Message.Content);

        ChatMessageContent response = await this.InvokeAsync(item.Message, messageContext.CancellationToken).ConfigureAwait(false);

        this.Logger.LogConcurrentAgentResult(this.Id, response.Content);

        await this.SendMessageAsync(response.ToResult(), this._handoffActor, messageContext.CancellationToken).ConfigureAwait(false);
    }
}
