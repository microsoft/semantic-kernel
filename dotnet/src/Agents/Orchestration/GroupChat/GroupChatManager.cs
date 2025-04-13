// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;

namespace Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;

/// <summary>
/// An <see cref="ChatManager"/> used to manage a <see cref="GroupChatOrchestration{TInput, TOutput}"/>.
/// </summary>
internal sealed class GroupChatManager : ChatManager
{
    /// <summary>
    /// Initializes a new instance of the <see cref="GroupChatManager"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="team">The team of agents being orchestrated</param>
    /// <param name="orchestrationType">Identifies the orchestration agent.</param>
    public GroupChatManager(AgentId id, IAgentRuntime runtime, ChatGroup team, AgentType orchestrationType)
        : base(id, runtime, team, orchestrationType)
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
#pragma warning disable CA5394 // Do not use insecure randomness
        int index = Random.Shared.Next(this.Team.Count + 1);
#pragma warning restore CA5394 // Do not use insecure randomness
        AgentType[] agentTypes = [.. this.Team.Keys.Select(value => new AgentType(value))];
        AgentType? agentType = null;
        if (index < this.Team.Count)
        {
            agentType = agentTypes[index];
        }
        return Task.FromResult(agentType);
    }
}
