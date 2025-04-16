// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;
using Microsoft.AgentRuntime.Core;
using Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Chat;

/// <summary>
/// An <see cref="AgentActor"/> used with the <see cref="GroupChatOrchestration{TInput, TOutput}"/>.
/// </summary>
internal sealed class ChatAgentActor :
    AgentActor,
    IHandle<ChatMessages.Group>,
    IHandle<ChatMessages.Reset>,
    IHandle<ChatMessages.Speak>
{
    private readonly List<ChatMessageContent> _cache;
    private readonly TopicId _groupTopic;

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatAgentActor"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="agent">An <see cref="Agent"/>.</param>
    /// <param name="groupTopic">The unique topic used to broadcast to the entire chat.</param>
    public ChatAgentActor(AgentId id, IAgentRuntime runtime, Agent agent, TopicId groupTopic)
        : base(id, runtime, agent)
    {
        this._cache = [];
        this._groupTopic = groupTopic;
    }

    /// <inheritdoc/>
    public ValueTask HandleAsync(ChatMessages.Group item, MessageContext messageContext)
    {
        this._cache.Add(item.Message);

        return ValueTask.CompletedTask;
    }

    /// <inheritdoc/>
    public async ValueTask HandleAsync(ChatMessages.Reset item, MessageContext messageContext)
    {
        await this.DeleteThreadAsync(messageContext.CancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async ValueTask HandleAsync(ChatMessages.Speak item, MessageContext messageContext)
    {
        this.Logger.LogChatAgentInvoke(this.Id);

        ChatMessageContent response = await this.InvokeAsync(this._cache, messageContext.CancellationToken).ConfigureAwait(false);

        this.Logger.LogChatAgentResult(this.Id, response.Content);

        this._cache.Clear();
        await this.PublishMessageAsync(response.ToGroup(), this._groupTopic).ConfigureAwait(false);
    }
}
