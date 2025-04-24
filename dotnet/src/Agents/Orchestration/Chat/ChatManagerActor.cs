// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;
using Microsoft.SemanticKernel.Agents.Runtime;
using Microsoft.SemanticKernel.Agents.Runtime.Core;
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
    private readonly ChatHandoff _handoff;

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatManagerActor"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="team">The team of agents being orchestrated</param>
    /// <param name="orchestrationType">Identifies the orchestration agent.</param>
    /// <param name="groupTopic">The unique topic used to broadcast to the entire chat.</param>
    /// <param name="handoff">Defines how the group-chat is translated into a singular response.</param>
    /// <param name="logger">The logger to use for the actor</param>
    protected ChatManagerActor(AgentId id, IAgentRuntime runtime, ChatGroup team, AgentType orchestrationType, TopicId groupTopic, ChatHandoff handoff, ILogger? logger = null)
        : base(id, runtime, DefaultDescription, logger)
    {
        this._orchestrationType = orchestrationType;
        this._handoff = handoff;

        this.Chat = [];
        this.Team = team;
        this.GroupTopic = groupTopic;
    }

    /// <summary>
    /// The conversation history with the team.
    /// </summary>
    protected ChatHistory Chat { get; }

    /// <summary>
    /// The agent type used to identify the orchestration agent.
    /// </summary>
    protected TopicId GroupTopic { get; }

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
            await this.PublishMessageAsync(item.Message.ToGroup(), this.GroupTopic).ConfigureAwait(false);
        }
        else
        {
            this.Logger.LogChatManagerTerminate(this.Id);
            ChatMessageContent handoff = await this._handoff.ProcessAsync(this.Chat, messageContext.CancellationToken).ConfigureAwait(false);
            await this.SendMessageAsync(handoff.ToResult(), this._orchestrationType, messageContext.CancellationToken).ConfigureAwait(false);
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
            ChatMessageContent handoff = await this._handoff.ProcessAsync(this.Chat, messageContext.CancellationToken).ConfigureAwait(false);
            await this.SendMessageAsync(handoff.ToResult(), this._orchestrationType, messageContext.CancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    public ValueTask HandleAsync(ChatMessages.Result item, MessageContext messageContext)
    {
        this.Logger.LogChatManagerResult(this.Id);
        return ValueTask.CompletedTask;
    }
}
