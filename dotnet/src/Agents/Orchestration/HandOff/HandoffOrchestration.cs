// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Handoff;

/// <summary>
/// An orchestration that provides the input message to the first agent
/// and sequentially passes each agent result to the next agent.
/// </summary>
public class HandoffOrchestration<TInput, TOutput> : AgentOrchestration<TInput, HandoffMessage, HandoffMessage, TOutput>
{
    /// <summary>
    /// Initializes a new instance of the <see cref="HandoffOrchestration{TInput, TOutput}"/> class.
    /// </summary>
    /// <param name="runtime">The runtime associated with the orchestration.</param>
    /// <param name="agents">The agents participating in the orchestration.</param>
    public HandoffOrchestration(IAgentRuntime runtime, params OrchestrationTarget[] agents)
        : base(runtime, agents)
    {
    }

    /// <inheritdoc />
    protected override async ValueTask StartAsync(TopicId topic, HandoffMessage input, AgentType? entryAgent)
    {
        Trace.WriteLine($"> HANDOFF START: {topic} [{entryAgent}]");

        await this.Runtime.SendMessageAsync(input, new AgentId(entryAgent!, AgentId.DefaultKey)).ConfigureAwait(false); // %%% AGENTID & NULL OVERRIDE
    }

    /// <inheritdoc />
    protected override async ValueTask<AgentType?> RegisterMembersAsync(TopicId topic, AgentType orchestrationType)
    {
        // Each agent handsoff its result to the next agent.
        AgentType nextAgent = orchestrationType;
        for (int index = this.Members.Count - 1; index >= 0; --index)
        {
            Trace.WriteLine($"> HANDOFF NEXT #{index}: {nextAgent}");
            OrchestrationTarget member = this.Members[index];
            switch (member.TargetType)
            {
                case OrchestrationTargetType.Agent:
                    nextAgent = await RegisterAgentAsync(topic, nextAgent, index, member).ConfigureAwait(false);
                    break;
                case OrchestrationTargetType.Orchestratable:
                    nextAgent = await member.Orchestration!.RegisterAsync(topic, nextAgent).ConfigureAwait(false); // %%% NULL OVERIDE
                    break;
                default:
                    throw new InvalidOperationException($"Unsupported target type: {member.TargetType}"); // %%% EXCEPTION TYPE
            }
            Trace.WriteLine($"> HANDOFF MEMBER #{index}: {nextAgent}");
        }

        return nextAgent;

        async Task<AgentType> RegisterAgentAsync(TopicId topic, AgentType nextAgent, int index, OrchestrationTarget member)
        {
            AgentType agentType = this.GetAgentType(topic, index);
            return await this.Runtime.RegisterAgentFactoryAsync(
                agentType,
                (agentId, runtime) => ValueTask.FromResult<IHostableAgent>(new HandoffActor(agentId, runtime, member.Agent!, nextAgent))).ConfigureAwait(false); // %%% NULL OVERRIDE
        }
    }

    private AgentType GetAgentType(TopicId topic, int index) => this.FormatAgentType(topic, $"Agent_{index + 1}");
}
