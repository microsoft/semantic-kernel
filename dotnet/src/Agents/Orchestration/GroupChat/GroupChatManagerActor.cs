// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Runtime;
using Microsoft.SemanticKernel.Agents.Runtime.Core;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;

/// <summary>
/// An <see cref="OrchestrationActor"/> used to manage a <see cref="GroupChatOrchestration{TInput, TOutput}"/>.
/// </summary>
internal sealed class GroupChatManagerActor :
    OrchestrationActor,
    IHandle<GroupChatMessages.InputTask>,
    IHandle<GroupChatMessages.Group>
{
    /// <summary>
    /// A common description for the manager.
    /// </summary>
    public const string DefaultDescription = "Orchestrates a team of agents to accomplish a defined task.";

    private readonly AgentType _orchestrationType;
    private readonly GroupChatManager _manager;
    private readonly ChatHistory _chat;
    private readonly GroupChatTeam _team;

    /// <summary>
    /// Initializes a new instance of the <see cref="GroupChatManagerActor"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="context">The orchestration context.</param>
    /// <param name="manager">The manages the flow of the group-chat.</param>
    /// <param name="team">The team of agents being orchestrated</param>
    /// <param name="orchestrationType">Identifies the orchestration agent.</param>
    /// <param name="logger">The logger to use for the actor</param>
    public GroupChatManagerActor(AgentId id, IAgentRuntime runtime, OrchestrationContext context, GroupChatManager manager, GroupChatTeam team, AgentType orchestrationType, ILogger? logger = null)
        : base(id, runtime, context, DefaultDescription, logger)
    {
        this._chat = [];
        this._manager = manager;
        this._orchestrationType = orchestrationType;
        this._team = team;
    }

    /// <inheritdoc/>
    public async ValueTask HandleAsync(GroupChatMessages.InputTask item, MessageContext messageContext)
    {
        this.Logger.LogChatManagerInit(this.Id);

        this._chat.AddRange(item.Messages);

        await this.PublishMessageAsync(item.Messages.AsGroupMessage(), this.Context.Topic).ConfigureAwait(false);

        await this.ManageAsync(messageContext).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async ValueTask HandleAsync(GroupChatMessages.Group item, MessageContext messageContext)
    {
        this.Logger.LogChatManagerInvoke(this.Id);

        this._chat.AddRange(item.Messages);

        await this.ManageAsync(messageContext).ConfigureAwait(false);
    }

    private async ValueTask ManageAsync(MessageContext messageContext)
    {
        if (this._manager.InteractiveCallback != null)
        {
            GroupChatManagerResult<bool> inputResult = await this._manager.ShouldRequestUserInput(this._chat, messageContext.CancellationToken).ConfigureAwait(false);
            this.Logger.LogChatManagerInput(this.Id, inputResult.Value, inputResult.Reason);
            if (inputResult.Value)
            {
                ChatMessageContent input = await this._manager.InteractiveCallback.Invoke().ConfigureAwait(false);
                this.Logger.LogChatManagerUserInput(this.Id, input.Content);
                this._chat.Add(input);
                await this.PublishMessageAsync(input.AsGroupMessage(), this.Context.Topic).ConfigureAwait(false);
            }
        }

        GroupChatManagerResult<bool> terminateResult = await this._manager.ShouldTerminate(this._chat, messageContext.CancellationToken).ConfigureAwait(false);
        this.Logger.LogChatManagerTerminate(this.Id, terminateResult.Value, terminateResult.Reason);
        if (terminateResult.Value)
        {
            GroupChatManagerResult<string> filterResult = await this._manager.FilterResults(this._chat, messageContext.CancellationToken).ConfigureAwait(false);
            this.Logger.LogChatManagerResult(this.Id, filterResult.Value, filterResult.Reason);
            await this.SendMessageAsync(filterResult.Value.AsResultMessage(), this._orchestrationType, messageContext.CancellationToken).ConfigureAwait(false);
            return;
        }

        GroupChatManagerResult<string> selectionResult = await this._manager.SelectNextAgent(this._chat, this._team, messageContext.CancellationToken).ConfigureAwait(false);
        AgentType selectionType = this._team[selectionResult.Value].Type;
        this.Logger.LogChatManagerSelect(this.Id, selectionType);
        await this.SendMessageAsync(new GroupChatMessages.Speak(), selectionType, messageContext.CancellationToken).ConfigureAwait(false);
    }
}
