// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Runtime;
using Microsoft.SemanticKernel.Agents.Runtime.Core;

namespace Microsoft.SemanticKernel.Agents.Magentic;

/// <summary>
/// An <see cref="AgentActor"/> used with the <see cref="MagenticOrchestration{TInput, TOutput}"/>.
/// </summary>
internal sealed class MagenticAgentActor :
    AgentActor,
    IHandle<MagenticMessages.Group>,
    IHandle<MagenticMessages.Reset>,
    IHandle<MagenticMessages.Speak>
{
    private readonly List<ChatMessageContent> _cache;

    /// <summary>
    /// Initializes a new instance of the <see cref="MagenticAgentActor"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="context">The orchestration context.</param>
    /// <param name="agent">An <see cref="Agent"/>.</param>
    /// <param name="logger">The logger to use for the actor</param>
    public MagenticAgentActor(AgentId id, IAgentRuntime runtime, OrchestrationContext context, Agent agent, ILogger<MagenticAgentActor>? logger = null)
        : base(id, runtime, context, agent, logger)
    {
        this._cache = [];
    }

    /// <inheritdoc/>
    public ValueTask HandleAsync(MagenticMessages.Group item, MessageContext messageContext)
    {
        this._cache.AddRange(item.Messages);

#if !NETCOREAPP
        return Task.CompletedTask.AsValueTask();
#else
        return ValueTask.CompletedTask;
#endif
    }

    /// <inheritdoc/>
    public async ValueTask HandleAsync(MagenticMessages.Reset item, MessageContext messageContext)
    {
        this._cache.Clear();
        await this.DeleteThreadAsync(messageContext.CancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async ValueTask HandleAsync(MagenticMessages.Speak item, MessageContext messageContext)
    {
        try
        {
            this.Logger.LogMagenticAgentInvoke(this.Id);

            ChatMessageContent response = await this.InvokeAsync(this._cache, messageContext.CancellationToken).ConfigureAwait(false);

            this.Logger.LogMagenticAgentResult(this.Id, response.Content);

            this._cache.Clear();
            await this.PublishMessageAsync(response.AsGroupMessage(), this.Context.Topic).ConfigureAwait(false);
        }
        catch (Exception exception)
        {
            Debug.WriteLine($"ACTOR EXCEPTION: {exception.Message}\n{exception.StackTrace}");
            throw;
        }
    }
}
