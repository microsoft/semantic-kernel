// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.AgentRuntime;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Orchestration.Extensions;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Sequential;

/// <summary>
/// An orchestration that provides the input message to the first agent
/// and sequentially passes each agent result to the next agent.
/// </summary>
public class SequentialOrchestration<TInput, TOutput> : AgentOrchestration<TInput, SequentialMessage, SequentialMessage, TOutput>
{
    /// <summary>
    /// Initializes a new instance of the <see cref="SequentialOrchestration{TInput, TOutput}"/> class.
    /// </summary>
    /// <param name="runtime">The runtime associated with the orchestration.</param>
    /// <param name="agents">The agents participating in the orchestration.</param>
    public SequentialOrchestration(IAgentRuntime runtime, params OrchestrationTarget[] agents)
        : base(runtime, agents)
    {
    }

    /// <inheritdoc />
    protected override async ValueTask StartAsync(TopicId topic, SequentialMessage input, AgentType? entryAgent)
    {
        await this.Runtime.SendMessageAsync(input, entryAgent!.Value).ConfigureAwait(false); // NULL OVERRIDE
    }

    /// <inheritdoc />
    protected override async ValueTask<AgentType?> RegisterMembersAsync(TopicId topic, AgentType orchestrationType, ILogger logger)
    {
        // Each agent handsoff its result to the next agent.
        AgentType nextAgent = orchestrationType;
        for (int index = this.Members.Count - 1; index >= 0; --index)
        {
            OrchestrationTarget member = this.Members[index];

            if (member.IsAgent(out Agent? agent))
            {
                nextAgent = await RegisterAgentAsync(topic, nextAgent, index, agent).ConfigureAwait(false);
            }
            else if (member.IsOrchestration(out Orchestratable? orchestration))
            {
                nextAgent = await orchestration.RegisterAsync(topic, nextAgent, logger).ConfigureAwait(false);
            }
            logger.LogConcurrentRegistration(nextAgent, "MEMBER", index);
        }

        return nextAgent;

        async Task<AgentType> RegisterAgentAsync(TopicId topic, AgentType nextAgent, int index, Agent agent)
        {
            AgentType agentType = this.GetAgentType(topic, index);
            return await this.Runtime.RegisterAgentFactoryAsync(
                agentType,
                (agentId, runtime) => ValueTask.FromResult<IHostableAgent>(new SequentialActor(agentId, runtime, agent, nextAgent))).ConfigureAwait(false);
        }
    }

    private AgentType GetAgentType(TopicId topic, int index) => this.FormatAgentType(topic, $"Agent_{index + 1}");
}
