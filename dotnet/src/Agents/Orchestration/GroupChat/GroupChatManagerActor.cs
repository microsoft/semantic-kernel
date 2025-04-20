// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Orchestration.Chat;

namespace Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;

/// <summary>
/// An <see cref="ChatManagerActor"/> used to manage a <see cref="GroupChatOrchestration{TInput, TOutput}"/>.
/// </summary>
internal sealed class GroupChatManagerActor : ChatManagerActor // %%% ABSTRACT
{
    private int _count = 0;

    /// <summary>
    /// Initializes a new instance of the <see cref="GroupChatManagerActor"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="team">The team of agents being orchestrated</param>
    /// <param name="orchestrationType">Identifies the orchestration agent.</param>
    /// <param name="groupTopic">The unique topic used to broadcast to the entire chat.</param>
    /// <param name="logger">The logger to use for the actor</param>
    public GroupChatManagerActor(AgentId id, IAgentRuntime runtime, ChatGroup team, AgentType orchestrationType, TopicId groupTopic, ILogger<GroupChatManagerActor>? logger = null)
        : base(id, runtime, team, orchestrationType, groupTopic, logger)
    {
    }

    /// <inheritdoc/>
    protected override Task<AgentType?> PrepareTaskAsync()
    {
        return this.SelectAgentAsync();
    }

    /// <inheritdoc/>
    protected override Task<AgentType?> SelectAgentAsync()
    {
        // %%% PLACEHOLDER SELECTION LOGIC
        if (this._count >= 2)
        {
            return Task.FromResult<AgentType?>(null);
        }
        AgentType[] agentTypes = [.. this.Team.Keys.Select(value => new AgentType(value))];
        AgentType? agentType = agentTypes[this._count % this.Team.Count];
        ++this._count;
        return Task.FromResult(agentType);
    }
}
