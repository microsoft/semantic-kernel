// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Orchestration.Chat;
using Microsoft.SemanticKernel.Agents.Runtime;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Magentic;

/// <summary>
/// An <see cref="ChatManagerActor"/> used to manage a <see cref="MagenticOrchestration{TInput, TOutput}"/>.
/// </summary>
internal sealed class MagenticManagerActor : ChatManagerActor
{
    private int _index;

    /// <summary>
    /// Initializes a new instance of the <see cref="MagenticManagerActor"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="team">The team of agents being orchestrated</param>
    /// <param name="orchestrationType">Identifies the orchestration agent.</param>
    /// <param name="groupTopic">The unique topic used to broadcast to the entire chat.</param>
    /// <param name="logger">The logger to use for the actor</param>
    public MagenticManagerActor(AgentId id, IAgentRuntime runtime, ChatGroup team, AgentType orchestrationType, TopicId groupTopic, ILogger<MagenticManagerActor>? logger = null)
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
        if (this._index >= 2)
        {
            return Task.FromResult<AgentType?>(null);
        }
        AgentType[] agentTypes = [.. this.Team.Keys.Select(value => new AgentType(value))];
        AgentType? agentType = agentTypes[this._index % this.Team.Count];
        ++this._index;
        return Task.FromResult(agentType);
    }
}
