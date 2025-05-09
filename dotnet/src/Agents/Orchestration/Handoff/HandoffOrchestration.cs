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
public class HandoffOrchestration<TInput, TOutput> : AgentOrchestration<TInput, TOutput>
{
    internal static readonly string OrchestrationName = FormatOrchestrationName(typeof(HandoffOrchestration<,>));

    private readonly OrchestrationHandoffs _handoffs;

    /// <summary>
    /// Initializes a new instance of the <see cref="HandoffOrchestration{TInput, TOutput}"/> class.
    /// </summary>
    /// <param name="handoffs">Defines the handoff connections for each agent.</param>
    /// <param name="agents">The agents participating in the orchestration.</param>
    public HandoffOrchestration(OrchestrationHandoffs handoffs, params Agent[] agents)
        : base(OrchestrationName, agents)
    {
        HashSet<string> agentNames = agents.Select(a => a.Name ?? a.Id).ToHashSet(StringComparer.OrdinalIgnoreCase);
        string[] badNames = [.. handoffs.Keys.Concat(handoffs.Values.SelectMany(h => h.Keys)).Where(name => !agentNames.Contains(name))];
        if (badNames.Length > 0)
        {
            throw new ArgumentException($"The following agents are not defined in the orchestration: {string.Join(", ", badNames)}", nameof(handoffs));
        }

        this._handoffs = handoffs;
    }

    /// <summary>
    /// Gets or sets the callback to be invoked for interactive input.
    /// </summary>
    public OrchestrationInteractiveCallback? InteractiveCallback { get; init; }

    /// <inheritdoc />
    protected override async ValueTask StartAsync(IAgentRuntime runtime, TopicId topic, IEnumerable<ChatMessageContent> input, AgentType? entryAgent)
    {
        if (!entryAgent.HasValue)
        {
            throw new ArgumentException("Entry agent is not defined.", nameof(entryAgent));
        }
        await runtime.PublishMessageAsync(input.AsInputTaskMessage(), topic).ConfigureAwait(false);
        await runtime.SendMessageAsync(new HandoffMessages.Request(), entryAgent.Value).ConfigureAwait(false);
    }

    /// <inheritdoc />
    protected override async ValueTask<AgentType?> RegisterOrchestrationAsync(IAgentRuntime runtime, OrchestrationContext context, RegistrationContext registrar, ILogger logger)
    {
        AgentType outputType = await registrar.RegisterResultTypeAsync<HandoffMessages.Result>(response => [response.Message]).ConfigureAwait(false);

        // Each agent handsoff its result to the next agent.
        Dictionary<string, AgentType> agentMap = [];
        Dictionary<string, HandoffLookup> handoffMap = [];
        AgentType agentType = outputType;
        for (int index = this.Members.Count - 1; index >= 0; --index)
        {
            Agent agent = this.Members[index];
            HandoffLookup map = [];
            handoffMap[agent.Name ?? agent.Id] = map;
            agentType =
                await runtime.RegisterAgentFactoryAsync(
                    this.GetAgentType(context.Topic, index),
                    (agentId, runtime) =>
                        ValueTask.FromResult<IHostableAgent>(
                            new HandoffActor(agentId, runtime, context, agent, map, outputType, context.LoggerFactory.CreateLogger<HandoffActor>())
                            {
                                InteractiveCallback = this.InteractiveCallback
                            })).ConfigureAwait(false);
            agentMap[agent.Name ?? agent.Id] = agentType;

            await runtime.SubscribeAsync(agentType, context.Topic).ConfigureAwait(false);

            logger.LogRegisterActor(OrchestrationName, agentType, "MEMBER", index + 1);
        }

        // Complete the handoff model
        foreach ((string agentName, AgentHandoffs handoffs) in this._handoffs)
        {
            // Retrieve the map for the agent (every agent had an empty map created)
            HandoffLookup agentHandoffs = handoffMap[agentName];
            foreach ((string handoffName, string description) in handoffs)
            {
                // name = (type,description)
                agentHandoffs[handoffName] = (agentMap[handoffName], description);
            }
        }

        return agentType;
    }

    private AgentType GetAgentType(TopicId topic, int index) => this.FormatAgentType(topic, $"Agent_{index + 1}");
}
