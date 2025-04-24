// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Orchestration.Chat;
using Microsoft.SemanticKernel.Agents.Orchestration.Concurrent;
using Microsoft.SemanticKernel.Agents.Orchestration.Extensions;
using Microsoft.SemanticKernel.Agents.Runtime;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Magentic;

/// <summary>
/// An orchestration that coordinates a group-chat.
/// </summary>
public class MagenticOrchestration<TInput, TOutput> :
    AgentOrchestration<TInput, ChatMessages.InputTask, ChatMessages.Result, TOutput>
{
    internal const string DefaultAgentDescription = "A helpful agent.";

    internal static readonly string OrchestrationName = typeof(ConcurrentOrchestration<,>).Name.Split('`').First();

    private readonly Kernel _kernel;

    /// <summary>
    /// Initializes a new instance of the <see cref="MagenticOrchestration{TInput, TOutput}"/> class.
    /// </summary>
    /// <param name="runtime">The runtime associated with the orchestration.</param>
    /// <param name="kernel">A kernel with services used by the manager.</param>
    /// <param name="agents">The agents participating in the orchestration.</param>
    public MagenticOrchestration(IAgentRuntime runtime, Kernel kernel, params OrchestrationTarget[] agents)
        : base(OrchestrationName, runtime, agents)
    {
        this._kernel = kernel;
    }

    /// <summary>
    /// Defines how the group-chat is translated into the orchestration result (or handoff).
    /// </summary>
    public ChatHandoff Handoff { get; init; } = ChatHandoff.Default;

    /// <summary>
    /// The maximum number of retry attempts when the task execution faulters.
    /// </summary>
    public MagenticOrchestrationSettings Settings { get; init; } = MagenticOrchestrationSettings.Default;

    /// <inheritdoc />
    protected override ValueTask StartAsync(TopicId topic, ChatMessages.InputTask input, AgentType? entryAgent)
    {
        return this.Runtime.SendMessageAsync(input, entryAgent!.Value);
    }

    /// <inheritdoc />
    protected override async ValueTask<AgentType?> RegisterMembersAsync(TopicId topic, AgentType orchestrationType, ILoggerFactory loggerFactory, ILogger logger)
    {
        AgentType managerType = this.FormatAgentType(topic, "Manager");

        int agentCount = 0;
        ChatGroup team = [];
        foreach (OrchestrationTarget member in this.Members)
        {
            ++agentCount;

            AgentType memberType = default;
            string? description = null;
            string? name = null;
            if (member.IsAgent(out Agent? agent))
            {
                memberType = await RegisterAgentAsync(agent).ConfigureAwait(false);
                description = agent.Description;
                name = agent.Name ?? agent.Id;
            }
            else if (member.IsOrchestration(out Orchestratable? orchestration))
            {
                memberType = await orchestration.RegisterAsync(topic, managerType, loggerFactory).ConfigureAwait(false);
                description = orchestration.Description;
                name = orchestration.Name;
            }

            team[memberType] = (name ?? memberType, description ?? DefaultAgentDescription);

            logger.LogRegisterActor(OrchestrationName, memberType, "MEMBER", agentCount);

            await this.SubscribeAsync(memberType, topic).ConfigureAwait(false);
        }

        await this.Runtime.RegisterAgentFactoryAsync(
            managerType,
            (agentId, runtime) =>
                ValueTask.FromResult<IHostableAgent>(
                    new MagenticManagerActor(agentId, runtime, team, orchestrationType, topic, this._kernel, this.Handoff, loggerFactory.CreateLogger<MagenticManagerActor>()) { Settings = this.Settings })).ConfigureAwait(false);

        await this.SubscribeAsync(managerType, topic).ConfigureAwait(false);

        return managerType;

        ValueTask<AgentType> RegisterAgentAsync(Agent agent)
        {
            return
                this.Runtime.RegisterAgentFactoryAsync(
                    this.FormatAgentType(topic, $"Agent_{agentCount}"),
                    (agentId, runtime) =>
                        ValueTask.FromResult<IHostableAgent>(new ChatAgentActor(agentId, runtime, agent, topic, loggerFactory.CreateLogger<ChatAgentActor>())));
        }
    }
}
