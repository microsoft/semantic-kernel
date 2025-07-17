// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Orchestration.Extensions;
using Microsoft.SemanticKernel.Agents.Runtime;

namespace Microsoft.SemanticKernel.Agents.Magentic;

/// <summary>
/// An orchestration that coordinates a group-chat.
/// </summary>
public class MagenticOrchestration<TInput, TOutput> :
    AgentOrchestration<TInput, TOutput>
{
    internal const string DefaultAgentDescription = "A helpful agent.";

    private readonly MagenticManager _manager;

    /// <summary>
    /// Initializes a new instance of the <see cref="MagenticOrchestration{TInput, TOutput}"/> class.
    /// </summary>
    /// <param name="manager">The manages the flow of the group-chat.</param>
    /// <param name="agents">The agents participating in the orchestration.</param>
    public MagenticOrchestration(MagenticManager manager, params Agent[] agents)
        : base(agents)
    {
        Verify.NotNull(manager, nameof(manager));

        this._manager = manager;
    }

    /// <inheritdoc />
    protected override ValueTask StartAsync(IAgentRuntime runtime, TopicId topic, IEnumerable<ChatMessageContent> input, AgentType? entryAgent)
    {
        if (!entryAgent.HasValue)
        {
            throw new ArgumentException("Entry agent is not defined.", nameof(entryAgent));
        }
        return runtime.PublishMessageAsync(input.AsInputTaskMessage(), entryAgent.Value);
    }

    /// <inheritdoc />
    protected override async ValueTask<AgentType?> RegisterOrchestrationAsync(IAgentRuntime runtime, OrchestrationContext context, RegistrationContext registrar, ILogger logger)
    {
        AgentType outputType = await registrar.RegisterResultTypeAsync<MagenticMessages.Result>(response => [response.Message]).ConfigureAwait(false);

        int agentCount = 0;
        MagenticTeam team = [];
        foreach (Agent agent in this.Members)
        {
            ++agentCount;
            AgentType agentType = await RegisterAgentAsync(agent, agentCount).ConfigureAwait(false);
            string name = agent.Name ?? agent.Id ?? agentType;
            string? description = agent.Description;

            team[name] = (agentType, description ?? DefaultAgentDescription);

            logger.LogRegisterActor(this.OrchestrationLabel, agentType, "MEMBER", agentCount);

            await runtime.SubscribeAsync(agentType, context.Topic).ConfigureAwait(false);
        }

        AgentType managerType =
            await runtime.RegisterOrchestrationAgentAsync(
                this.FormatAgentType(context.Topic, "Manager"),
                (agentId, runtime) =>
                {
                    MagenticManagerActor actor = new(agentId, runtime, context, this._manager, team, outputType, context.LoggerFactory.CreateLogger<MagenticManagerActor>());
#if !NETCOREAPP
                    return actor.AsValueTask<IHostableAgent>();
#else
                    return ValueTask.FromResult<IHostableAgent>(actor);
#endif
                }).ConfigureAwait(false);
        logger.LogRegisterActor(this.OrchestrationLabel, managerType, "MANAGER");

        await runtime.SubscribeAsync(managerType, context.Topic).ConfigureAwait(false);

        return managerType;

        ValueTask<AgentType> RegisterAgentAsync(Agent agent, int agentCount) =>
            runtime.RegisterOrchestrationAgentAsync(
                this.FormatAgentType(context.Topic, $"Agent_{agentCount}"),
                (agentId, runtime) =>
                {
                    MagenticAgentActor actor = new(agentId, runtime, context, agent, context.LoggerFactory.CreateLogger<MagenticAgentActor>());
#if !NETCOREAPP
                    return actor.AsValueTask<IHostableAgent>();
#else
                    return ValueTask.FromResult<IHostableAgent>(actor);
#endif
                });
    }
}
