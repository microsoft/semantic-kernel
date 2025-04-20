// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Concurrent;

/// <summary>
/// An orchestration that broadcasts the input message to each agent.
/// </summary>
public class ConcurrentOrchestration<TInput, TOutput>
    : AgentOrchestration<TInput, ConcurrentMessages.Request, ConcurrentMessages.Result[], TOutput>
{
    internal static readonly string OrchestrationName = typeof(ConcurrentOrchestration<,>).Name.Split('`').First();

    /// <summary>
    /// Initializes a new instance of the <see cref="ConcurrentOrchestration{TInput, TOutput}"/> class.
    /// </summary>
    /// <param name="runtime">The runtime associated with the orchestration.</param>
    /// <param name="agents">The agents participating in the orchestration.</param>
    public ConcurrentOrchestration(IAgentRuntime runtime, params OrchestrationTarget[] agents)
        : base(OrchestrationName, runtime, agents)
    {
    }

    /// <inheritdoc />
    protected override ValueTask StartAsync(TopicId topic, ConcurrentMessages.Request input, AgentType? entryAgent)
    {
        return this.Runtime.PublishMessageAsync(input, topic);
    }

    /// <inheritdoc />
    protected override async ValueTask<AgentType?> RegisterMembersAsync(TopicId topic, AgentType orchestrationType, ILoggerFactory loggerFactory, ILogger logger)
    {
        // Register result actor
        AgentType resultType = this.FormatAgentType(topic, "Results");
        await this.Runtime.RegisterAgentFactoryAsync(
            resultType,
            (agentId, runtime) =>
                ValueTask.FromResult<IHostableAgent>(
                    new ConcurrentResultActor(agentId, runtime, orchestrationType, this.Members.Count, loggerFactory.CreateLogger<ConcurrentResultActor>()))).ConfigureAwait(false);
        logger.LogRegisterActor(OrchestrationName, resultType, "RESULTS");

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
                memberType = await orchestration.RegisterAsync(topic, resultType, loggerFactory).ConfigureAwait(false);
            }

            logger.LogRegisterActor(OrchestrationName, memberType, "MEMBER", agentCount);

            await this.SubscribeAsync(memberType, topic).ConfigureAwait(false);
        }

        return null;

        ValueTask<AgentType> RegisterAgentAsync(Agent agent)
        {
            return
                this.Runtime.RegisterAgentFactoryAsync(
                    this.FormatAgentType(topic, $"Agent_{agentCount}"),
                    (agentId, runtime) =>
                        ValueTask.FromResult<IHostableAgent>(new ConcurrentActor(agentId, runtime, agent, resultType, loggerFactory.CreateLogger<ConcurrentActor>())));
        }
    }
}
