// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;
using Microsoft.SemanticKernel.Agents.Orchestration.Extensions;

namespace Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;

/// <summary>
/// An orchestration that coordinates a group-chat.
/// </summary>
public class GroupChatOrchestration<TInput, TOutput> :
    AgentOrchestration<TInput, ChatMessages.InputTask, ChatMessages.Result, TOutput>
{
    /// <summary>
    /// Initializes a new instance of the <see cref="GroupChatOrchestration{TInput, TOutput}"/> class.
    /// </summary>
    /// <param name="runtime">The runtime associated with the orchestration.</param>
    /// <param name="agents">The agents participating in the orchestration.</param>
    public GroupChatOrchestration(IAgentRuntime runtime, params OrchestrationTarget[] agents)
        : base(runtime, agents)
    {
    }

    /// <inheritdoc />
    protected override ValueTask StartAsync(TopicId topic, ChatMessages.InputTask input, AgentType? entryAgent)
    {
        Trace.WriteLine($"> GROUPCHAT START: {topic} [{entryAgent}]");

        return this.Runtime.SendMessageAsync(input, entryAgent!.Value);
    }

    /// <inheritdoc />
    protected override async ValueTask<AgentType?> RegisterMembersAsync(TopicId topic, AgentType orchestrationType)
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
                memberType = await orchestration.RegisterAsync(topic, managerType).ConfigureAwait(false);
            }

            team[memberType] = (memberType, "an agent"); // %%% DESCRIPTION & NAME ID

            Trace.WriteLine($"> GROUPCHAT MEMBER #{agentCount}: {memberType}");

            await this.SubscribeAsync(memberType, topic).ConfigureAwait(false);
        }

        await this.Runtime.RegisterAgentFactoryAsync(
            managerType,
            (agentId, runtime) =>
                ValueTask.FromResult<IHostableAgent>(
                    new GroupChatManagerActor(agentId, runtime, team, orchestrationType, topic))).ConfigureAwait(false);

        await this.SubscribeAsync(managerType, topic).ConfigureAwait(false);

        return managerType;

        async ValueTask<AgentType> RegisterAgentAsync(Agent agent)
        {
            AgentType agentType = this.FormatAgentType(topic, $"Agent_{agentCount}");
            await this.Runtime.RegisterAgentFactoryAsync(
                agentType,
                (agentId, runtime) =>
                    ValueTask.FromResult<IHostableAgent>(new ChatAgentActor(agentId, runtime, agent, topic))).ConfigureAwait(false);

            return agentType;
        }
    }
}
