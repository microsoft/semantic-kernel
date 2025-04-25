// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Orchestration.Extensions;
using Microsoft.SemanticKernel.Agents.Runtime;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Handoff;

/// <summary>
/// An orchestration that provides the input message to the first agent
/// and Handoffly passes each agent result to the next agent.
/// </summary>
public class HandoffOrchestration<TInput, TOutput> : AgentOrchestration<TInput, HandoffMessages.InputTask, HandoffMessages.Result, TOutput>
{
    internal static readonly string OrchestrationName = typeof(HandoffOrchestration<,>).Name.Split('`').First();

    private readonly Dictionary<string, HandoffConnections> _handoffs;

    /// <summary>
    /// Initializes a new instance of the <see cref="HandoffOrchestration{TInput, TOutput}"/> class.
    /// </summary>
    /// <param name="runtime">The runtime associated with the orchestration.</param>
    /// <param name="handoffs">Defines the handoff connections for each agent.</param>
    /// <param name="agents">The agents participating in the orchestration.</param>
    public HandoffOrchestration(IAgentRuntime runtime, Dictionary<string, HandoffConnections> handoffs, params OrchestrationTarget[] agents)
        : base(OrchestrationName, runtime, agents)
    {
        this._handoffs = handoffs;
    }

    /// <inheritdoc />
    protected override async ValueTask StartAsync(TopicId topic, HandoffMessages.InputTask input, AgentType? entryAgent)
    {
        if (!entryAgent.HasValue)
        {
            throw new ArgumentException("Entry agent is not defined.", nameof(entryAgent));
        }
        await this.Runtime.PublishMessageAsync(new HandoffMessages.Response { Message = input.Message }, topic).ConfigureAwait(false);
        await this.Runtime.SendMessageAsync(new HandoffMessages.Request(), entryAgent.Value).ConfigureAwait(false);
    }

    /// <inheritdoc />
    protected override async ValueTask<AgentType?> RegisterMembersAsync(TopicId topic, AgentType orchestrationType, ILoggerFactory loggerFactory, ILogger logger)
    {
        // Each agent handsoff its result to the next agent.
        Dictionary<string, AgentType> agentMap = [];
        Dictionary<string, HandoffLookup> handoffMap = [];
        AgentType nextAgent = orchestrationType;
        for (int index = this.Members.Count - 1; index >= 0; --index)
        {
            OrchestrationTarget member = this.Members[index];

            if (member.IsAgent(out Agent? agent))
            {
                HandoffLookup map = [];
                handoffMap[agent.Name ?? agent.Id] = map;
                nextAgent = await RegisterAgentAsync(topic, nextAgent, index, agent, map).ConfigureAwait(false);
                agentMap[agent.Name ?? agent.Id] = nextAgent;
            }
            //else if (member.IsOrchestration(out Orchestratable? orchestration)) // %%% IS POSSIBLE ???
            //{
            //    nextAgent = await orchestration.RegisterAsync(topic, nextAgent, loggerFactory).ConfigureAwait(false);
            //}

            await this.SubscribeAsync(nextAgent, topic).ConfigureAwait(false);

            logger.LogRegisterActor(OrchestrationName, nextAgent, "MEMBER", index + 1);
        }

        // Complete the handoff model
        foreach ((string agentName, HandoffConnections handoffs) in this._handoffs)
        {
            // Retrieve the map for the agent (every agent had an empty map created)
            HandoffLookup agentHandoffs = handoffMap[agentName];
            foreach ((string handoffName, string description) in handoffs)
            {
                // name = (type,description)
                agentHandoffs[handoffName] = (agentMap[handoffName], description);
            }
        }

        return nextAgent;

        ValueTask<AgentType> RegisterAgentAsync(TopicId topic, AgentType nextAgent, int index, Agent agent, HandoffLookup handoffs)
        {
            return
                this.Runtime.RegisterAgentFactoryAsync(
                    this.GetAgentType(topic, index),
                    (agentId, runtime) => ValueTask.FromResult<IHostableAgent>(new HandoffActor(agentId, runtime, agent, handoffs, orchestrationType, topic, loggerFactory.CreateLogger<HandoffActor>())));
        }
    }

    private AgentType GetAgentType(TopicId topic, int index) => this.FormatAgentType(topic, $"Agent_{index + 1}");
}
