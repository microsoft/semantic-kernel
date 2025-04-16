// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;
using Microsoft.AgentRuntime.Core;
using Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Chat;

/// <summary>
/// An <see cref="PatternActor"/> used to manage a <see cref="GroupChatOrchestration{TInput, TOutput}"/>.
/// </summary>
public abstract class ChatManagerActor :
    PatternActor,
    IHandle<ChatMessages.InputTask>,
    IHandle<ChatMessages.Group>,
    IHandle<ChatMessages.Result>
{
    /// <summary>
    /// A common description for the manager.
    /// </summary>
    public const string DefaultDescription = "Orchestrates a team of agents to accomplish a defined task.";

    private readonly AgentType _orchestrationType;
    private readonly TopicId _groupTopic;

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatManagerActor"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="team">The team of agents being orchestrated</param>
    /// <param name="orchestrationType">Identifies the orchestration agent.</param>
    /// <param name="groupTopic">The unique topic used to broadcast to the entire chat.</param>
    protected ChatManagerActor(AgentId id, IAgentRuntime runtime, ChatGroup team, AgentType orchestrationType, TopicId groupTopic)
        : base(id, runtime, DefaultDescription)
    {
        this.Chat = [];
        this.Team = team;
        this._orchestrationType = orchestrationType;
        this._groupTopic = groupTopic;
    }

    /// <summary>
    /// The conversation history with the team.
    /// </summary>
    protected ChatHistory Chat { get; }

    /// <summary>
    /// The input task.
    /// </summary>
    protected ChatMessages.InputTask InputTask { get; private set; } = ChatMessages.InputTask.None;

    /// <summary>
    /// Metadata that describes team of agents being orchestrated.
    /// </summary>
    protected ChatGroup Team { get; }

    /// <summary>
    /// Message a specific agent, by topic.
    /// </summary>
    protected ValueTask RequestAgentResponseAsync(AgentType agentType, CancellationToken cancellationToken)
    {
        this.Logger.LogChatManagerSelect(this.Id, agentType);
        return this.SendMessageAsync(new ChatMessages.Speak(), agentType, cancellationToken);
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
    protected abstract Task<AgentType?> PrepareTaskAsync();

    /// <summary>
    /// Determines which agent's must respond.
    /// </summary>
    /// <returns>
    /// The agent specific topic for first step in executing the task.
    /// </returns>
    /// <remarks>
    /// Returning a null TopicId indicates that the task will not be executed.
    /// </remarks>
    protected abstract Task<AgentType?> SelectAgentAsync();

    /// <inheritdoc/>
    public async ValueTask HandleAsync(ChatMessages.InputTask item, MessageContext messageContext)
    {
        this.Logger.LogChatManagerInit(this.Id);
        this.InputTask = item;
        AgentType? agentType = await this.PrepareTaskAsync().ConfigureAwait(false);
        if (agentType != null)
        {
            await this.RequestAgentResponseAsync(agentType.Value, messageContext.CancellationToken).ConfigureAwait(false);
            await this.PublishMessageAsync(item.Message.ToGroup(), this._groupTopic).ConfigureAwait(false);
        }
        else
        {
            this.Logger.LogChatManagerTerminate(this.Id);
            await this.SendMessageAsync(item.Message.ToResult(), this._orchestrationType, messageContext.CancellationToken).ConfigureAwait(false); // %%% PLACEHOLDER - FINAL MESSAGE
        }
    }

    /// <inheritdoc/>
    public async ValueTask HandleAsync(ChatMessages.Group item, MessageContext messageContext)
    {
        this.Logger.LogChatManagerInvoke(this.Id);

        this.Chat.Add(item.Message);
        AgentType? agentType = await this.SelectAgentAsync().ConfigureAwait(false);
        if (agentType != null)
        {
            await this.RequestAgentResponseAsync(agentType.Value, messageContext.CancellationToken).ConfigureAwait(false);
        }
        else
        {
            this.Logger.LogChatManagerTerminate(this.Id);
            await this.SendMessageAsync(item.Message.ToResult(), this._orchestrationType, messageContext.CancellationToken).ConfigureAwait(false); // %%% PLACEHOLDER - FINAL MESSAGE
        }
    }

    /// <inheritdoc/>
    public ValueTask HandleAsync(ChatMessages.Result item, MessageContext messageContext)
    {
        this.Logger.LogChatManagerResult(this.Id);
        return ValueTask.CompletedTask;
    }
}
