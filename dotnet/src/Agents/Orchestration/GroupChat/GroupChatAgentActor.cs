// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Runtime;
using Microsoft.SemanticKernel.Agents.Runtime.Core;

namespace Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;

/// <summary>
/// An <see cref="AgentActor"/> used with the <see cref="GroupChatOrchestration{TInput, TOutput}"/>.
/// </summary>
internal sealed class GroupChatAgentActor :
    AgentActor,
    IHandle<GroupChatMessages.Group>,
    IHandle<GroupChatMessages.Reset>,
    IHandle<GroupChatMessages.Speak>
{
    private readonly List<ChatMessageContent> _cache;

    /// <summary>
    /// Initializes a new instance of the <see cref="GroupChatAgentActor"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="context">The orchestration context.</param>
    /// <param name="agent">An <see cref="Agent"/>.</param>
    /// <param name="logger">The logger to use for the actor</param>
    public GroupChatAgentActor(AgentId id, IAgentRuntime runtime, OrchestrationContext context, Agent agent, ILogger<GroupChatAgentActor>? logger = null)
        : base(id, runtime, context, agent, logger)
    {
        this._cache = [];
    }

    /// <inheritdoc/>
    public ValueTask HandleAsync(GroupChatMessages.Group item, MessageContext messageContext)
    {
        this._cache.AddRange(item.Messages);

#if !NETCOREAPP
        return Task.CompletedTask.AsValueTask();
#else
        return ValueTask.CompletedTask;
#endif
    }

    /// <inheritdoc/>
    public async ValueTask HandleAsync(GroupChatMessages.Reset item, MessageContext messageContext)
    {
        await this.DeleteThreadAsync(messageContext.CancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async ValueTask HandleAsync(GroupChatMessages.Speak item, MessageContext messageContext)
    {
        this.Logger.LogChatAgentInvoke(this.Id);

        ChatMessageContent response = await this.InvokeAsync(this._cache, messageContext.CancellationToken).ConfigureAwait(false);

        this.Logger.LogChatAgentResult(this.Id, response.Content);

        this._cache.Clear();
        await this.PublishMessageAsync(response.AsGroupMessage(), this.Context.Topic).ConfigureAwait(false);
    }
}
