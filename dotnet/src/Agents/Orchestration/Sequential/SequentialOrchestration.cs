// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Orchestration.Extensions;
using Microsoft.SemanticKernel.Agents.Runtime;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Sequential;

/// <summary>
/// An orchestration that provides the input message to the first agent
/// and sequentially passes each agent result to the next agent.
/// </summary>
public class SequentialOrchestration<TInput, TOutput> : AgentOrchestration<TInput, SequentialMessage, SequentialMessage, TOutput>
{
    internal static readonly string OrchestrationName = typeof(SequentialOrchestration<,>).Name.Split('`').First();

    /// <summary>
    /// Initializes a new instance of the <see cref="SequentialOrchestration{TInput, TOutput}"/> class.
    /// </summary>
    /// <param name="runtime">The runtime associated with the orchestration.</param>
    /// <param name="agents">The agents participating in the orchestration.</param>
    public SequentialOrchestration(IAgentRuntime runtime, params OrchestrationTarget[] agents)
        : base(OrchestrationName, runtime, agents)
    {
    }

    /// <inheritdoc />
    protected override async ValueTask StartAsync(TopicId topic, SequentialMessage input, AgentType? entryAgent)
    {
        if (!entryAgent.HasValue)
        {
            throw new ArgumentException("Entry agent is not defined.", nameof(entryAgent));
        }
        await this.Runtime.SendMessageAsync(input, entryAgent.Value).ConfigureAwait(false);
    }

    /// <inheritdoc />
    protected override async ValueTask<AgentType?> RegisterMembersAsync(TopicId topic, AgentType orchestrationType, ILoggerFactory loggerFactory, ILogger logger)
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
                nextAgent = await orchestration.RegisterAsync(topic, nextAgent, loggerFactory).ConfigureAwait(false);
            }
            logger.LogRegisterActor(OrchestrationName, nextAgent, "MEMBER", index + 1);
        }

        return nextAgent;

        ValueTask<AgentType> RegisterAgentAsync(TopicId topic, AgentType nextAgent, int index, Agent agent)
        {
            return
                this.Runtime.RegisterAgentFactoryAsync(
                    this.GetAgentType(topic, index),
                    (agentId, runtime) => ValueTask.FromResult<IHostableAgent>(new SequentialActor(agentId, runtime, agent, nextAgent, loggerFactory.CreateLogger<SequentialActor>())));
        }
    }

    private AgentType GetAgentType(TopicId topic, int index) => this.FormatAgentType(topic, $"Agent_{index + 1}");
}
