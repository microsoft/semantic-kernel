// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Orchestration.Chat;
using Microsoft.SemanticKernel.Agents.Runtime;

namespace Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;

/// <summary>
/// An <see cref="ChatManagerActor"/> used to manage a <see cref="GroupChatOrchestration{TInput, TOutput}"/>.
/// </summary>
internal sealed class GroupChatManagerActor : ChatManagerActor
{
    private readonly GroupChatStrategy _strategy;

    /// <summary>
    /// Initializes a new instance of the <see cref="GroupChatManagerActor"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="team">The team of agents being orchestrated</param>
    /// <param name="orchestrationType">Identifies the orchestration agent.</param>
    /// <param name="groupTopic">The unique topic used to broadcast to the entire chat.</param>
    /// <param name="strategy">The strategy that determines how the chat shall proceed.</param>
    /// <param name="handoff">Defines how the group-chat is translated into a singular response.</param>
    /// <param name="logger">The logger to use for the actor</param>
    public GroupChatManagerActor(AgentId id, IAgentRuntime runtime, ChatGroup team, AgentType orchestrationType, TopicId groupTopic, GroupChatStrategy strategy, ChatHandoff handoff, ILogger<GroupChatManagerActor>? logger = null)
        : base(id, runtime, team, orchestrationType, groupTopic, handoff, logger)
    {
        this._strategy = strategy;
    }

    /// <inheritdoc/>
    protected override Task<AgentType?> PrepareTaskAsync()
    {
        return this.SelectAgentAsync();
    }

    /// <inheritdoc/>
    protected override async Task<AgentType?> SelectAgentAsync()
    {
        GroupChatContext context = new(this.Team, this.Chat);
        await this._strategy.SelectAsync(context).ConfigureAwait(false);
        return context.HasSelection ? context.Selection! : (AgentType?)null;
    }
}
