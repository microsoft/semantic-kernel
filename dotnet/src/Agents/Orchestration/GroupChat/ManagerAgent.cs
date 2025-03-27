// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.AgentRuntime;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;

/// <summary>
/// A <see cref="RuntimeAgent"/> that orchestrates a team of agents.
/// </summary>
public abstract class ManagerAgent : RuntimeAgent
{
    /// <summary>
    /// A common description for the orchestrator.
    /// </summary>
    public const string Description = "Orchestrates a team of agents to accomplish a defined task.";

    /// <summary>
    /// Initializes a new instance of the <see cref="ManagerAgent"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="team">The team of agents being orchestrated</param>
    protected ManagerAgent(AgentId id, IAgentRuntime runtime, AgentTeam team)
        : base(id, runtime, Description)
    {
        this.Chat = [];
        this.Team = team;
        this.RegisterHandler<GroupChatMessages.Task>(this.OnTaskMessageAsync);
        this.RegisterHandler<GroupChatMessages.Group>(this.OnGroupMessageAsync);
    }

    /// <summary>
    /// The conversation history with the team.
    /// </summary>
    protected ChatHistory Chat { get; }

    /// <summary>
    /// The input task.
    /// </summary>
    protected GroupChatMessages.Task Task { get; private set; } = GroupChatMessages.Task.None;

    /// <summary>
    /// Metadata that describes team of agents being orchestrated.
    /// </summary>
    protected AgentTeam Team { get; }

    /// <summary>
    /// Message a specific agent, by topic.
    /// </summary>
    protected Task RequestAgentResponseAsync(TopicId agentTopic)
    {
        return this.PublishMessageAsync(new GroupChatMessages.Speak(), agentTopic); // %%% EXCEPTION: KeyNotFoundException/AggregateException
    }

    /// <summary>
    /// Defines one-time logic required to prepare to execute the given task.
    /// </summary>
    /// <returns>
    /// The agent specific topic for first step in executing the task.
    /// </returns>
    /// <remarks>
    /// Returning a null TopicId indicates that the task will not be executed.
    /// </remarks>
    protected abstract Task<TopicId?> PrepareTaskAsync();

    /// <summary>
    /// Determines which agent's must respond.
    /// </summary>
    /// <returns>
    /// The agent specific topic for first step in executing the task.
    /// </returns>
    /// <remarks>
    /// Returning a null TopicId indicates that the task will not be executed.
    /// </remarks>
    protected abstract Task<TopicId?> SelectAgentAsync();

    private async ValueTask OnTaskMessageAsync(GroupChatMessages.Task message, MessageContext context)
    {
        this.Task = message;
        TopicId? agentTopic = await this.PrepareTaskAsync().ConfigureAwait(false);
        if (agentTopic != null)
        {
            await this.RequestAgentResponseAsync(agentTopic.Value).ConfigureAwait(false);
        }
    }

    private async ValueTask OnGroupMessageAsync(GroupChatMessages.Group message, MessageContext context)
    {
        this.Chat.Add(message.Message);
        TopicId? agentTopic = await this.SelectAgentAsync().ConfigureAwait(false);
        if (agentTopic != null)
        {
            await this.RequestAgentResponseAsync(agentTopic.Value).ConfigureAwait(false);
        }
    }
}
