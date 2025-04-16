// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Orchestration.Chat;
using Microsoft.SemanticKernel.Agents.Orchestration.Concurrent;
using Microsoft.SemanticKernel.Agents.Orchestration.Extensions;

namespace Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;

/// <summary>
/// An orchestration that coordinates a group-chat.
/// </summary>
public class GroupChatOrchestration<TInput, TOutput> :
    AgentOrchestration<TInput, ChatMessages.InputTask, ChatMessages.Result, TOutput>
{
    internal static readonly string OrchestrationName = typeof(ConcurrentOrchestration<,>).Name.Split('`').First();

    /// <summary>
    /// Initializes a new instance of the <see cref="GroupChatOrchestration{TInput, TOutput}"/> class.
    /// </summary>
    /// <param name="runtime">The runtime associated with the orchestration.</param>
    /// <param name="agents">The agents participating in the orchestration.</param>
    public GroupChatOrchestration(IAgentRuntime runtime, params OrchestrationTarget[] agents)
        : base(OrchestrationName, runtime, agents)
    {
    }

    /// <inheritdoc />
    protected override ValueTask StartAsync(TopicId topic, ChatMessages.InputTask input, AgentType? entryAgent)
    {
        return this.Runtime.SendMessageAsync(input, entryAgent!.Value);
    }

    /// <inheritdoc />
    protected override async ValueTask<AgentType?> RegisterMembersAsync(TopicId topic, AgentType orchestrationType, ILogger logger)
    {
        AgentType managerType = this.FormatAgentType(topic, "Manager");

        int agentCount = 0;
        ChatGroup team = [];
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
                memberType = await orchestration.RegisterAsync(topic, managerType, logger).ConfigureAwait(false);
            }

            team[memberType] = (memberType, "an agent"); // %%% DESCRIPTION & NAME ID

            logger.LogRegisterActor(OrchestrationName, memberType, "MEMBER", agentCount);

            await this.SubscribeAsync(memberType, topic).ConfigureAwait(false);
        }

        ILogger loggerManager = this.LoggerFactory.CreateLogger<ConcurrentActor>();
        await this.Runtime.RegisterAgentFactoryAsync(
            managerType,
            (agentId, runtime) =>
                ValueTask.FromResult<IHostableAgent>(
                    new GroupChatManagerActor(agentId, runtime, team, orchestrationType, topic, loggerManager))).ConfigureAwait(false);

        await this.SubscribeAsync(managerType, topic).ConfigureAwait(false);

        return managerType;

        async ValueTask<AgentType> RegisterAgentAsync(Agent agent)
        {
            AgentType agentType = this.FormatAgentType(topic, $"Agent_{agentCount}");
            ILogger loggerActor = this.LoggerFactory.CreateLogger<ConcurrentActor>();
            await this.Runtime.RegisterAgentFactoryAsync(
                agentType,
                (agentId, runtime) =>
                    ValueTask.FromResult<IHostableAgent>(new ChatAgentActor(agentId, runtime, agent, topic, loggerActor))).ConfigureAwait(false);

            return agentType;
        }
    }
}
