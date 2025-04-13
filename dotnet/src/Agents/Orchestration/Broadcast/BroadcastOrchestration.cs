// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Broadcast;

/// <summary>
/// An orchestration that broadcasts the input message to each agent.
/// </summary>
public class BroadcastOrchestration<TInput, TOutput>
    : AgentOrchestration<TInput, BroadcastMessages.Task, BroadcastMessages.Result[], TOutput>
{
    /// <summary>
    /// Initializes a new instance of the <see cref="BroadcastOrchestration{TInput, TOutput}"/> class.
    /// </summary>
    /// <param name="runtime">The runtime associated with the orchestration.</param>
    /// <param name="agents">The agents participating in the orchestration.</param>
    public BroadcastOrchestration(IAgentRuntime runtime, params OrchestrationTarget[] agents)
        : base(runtime, agents)
    {
    }

    /// <inheritdoc />
    protected override ValueTask StartAsync(TopicId topic, BroadcastMessages.Task input, AgentType? entryAgent)
    {
        Trace.WriteLine($"> BROADCAST START: {topic}");
        return this.Runtime.PublishMessageAsync(input, topic);
    }

    /// <inheritdoc />
    protected override async ValueTask<AgentType?> RegisterMembersAsync(TopicId topic, AgentType orchestrationType)
    {
        // Register result actor
        AgentType resultType = this.FormatAgentType(topic, "Results");
        await this.Runtime.RegisterAgentFactoryAsync(
            resultType,
            (agentId, runtime) =>
                ValueTask.FromResult<IHostableAgent>(
                    new BroadcastResultActor(agentId, runtime, orchestrationType, this.Members.Count))).ConfigureAwait(false);
        Trace.WriteLine($"> BROADCAST RESULTS: {resultType}");

        // Register member actors - All agents respond to the same message.
        int agentCount = 0;
        foreach (OrchestrationTarget member in this.Members)
        {
            ++agentCount;

            AgentType memberType = default;

            if (member.IsAgent(out Agent? agent))
            {
                memberType = await RegisterAgentAsync(agent).ConfigureAwait(false);
            }
            else if (member.IsOrchestration(out Orchestratable? orchestration))
            {
                memberType = await orchestration.RegisterAsync(topic, resultType).ConfigureAwait(false);
            }

            Trace.WriteLine($"> BROADCAST MEMBER #{agentCount}: {memberType}");

            await this.SubscribeAsync(memberType, topic).ConfigureAwait(false);
        }

        return null;

        async ValueTask<AgentType> RegisterAgentAsync(Agent agent)
        {
            AgentType agentType = this.FormatAgentType(topic, $"Agent_{agentCount}");
            await this.Runtime.RegisterAgentFactoryAsync(
                agentType,
                (agentId, runtime) =>
                    ValueTask.FromResult<IHostableAgent>(new BroadcastActor(agentId, runtime, agent, resultType))).ConfigureAwait(false);

            return agentType;
        }
    }
}
