// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;
using Microsoft.SemanticKernel.Agents.Runtime;
using Microsoft.SemanticKernel.Agents.Runtime.Core;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.Magentic;

/// <summary>
/// An <see cref="OrchestrationActor"/> used to manage a <see cref="MagenticOrchestration{TInput, TOutput}"/>.
/// </summary>
internal sealed class MagenticManagerActor :
    OrchestrationActor,
    IHandle<MagenticMessages.InputTask>,
    IHandle<MagenticMessages.Group>
{
    /// <summary>
    /// A common description for the manager.
    /// </summary>
    public const string DefaultDescription = "Orchestrates a team of agents to accomplish a defined task.";

    private readonly AgentType _orchestrationType;
    private readonly MagenticManager _manager;
    private readonly ChatHistory _chat;
    private readonly MagenticTeam _team;

    private IReadOnlyList<ChatMessageContent> _inputTask = [];
    private int _invocationCount;
    private int _stallCount = 0;
    private int _retryCount = 0;

    /// <summary>
    /// Initializes a new instance of the <see cref="MagenticManagerActor"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="context">The orchestration context.</param>
    /// <param name="manager">The manages the flow of the group-chat.</param>
    /// <param name="team">The team of agents being orchestrated</param>
    /// <param name="orchestrationType">Identifies the orchestration agent.</param>
    /// <param name="logger">The logger to use for the actor</param>
    public MagenticManagerActor(AgentId id, IAgentRuntime runtime, OrchestrationContext context, MagenticManager manager, MagenticTeam team, AgentType orchestrationType, ILogger? logger = null)
        : base(id, runtime, context, DefaultDescription, logger)
    {
        this._chat = [];
        this._manager = manager;
        this._orchestrationType = orchestrationType;
        this._team = team;

        Debug.WriteLine($"TEAM:\n{team.FormatList()}");
    }

    /// <inheritdoc/>
    public async ValueTask HandleAsync(MagenticMessages.InputTask item, MessageContext messageContext)
    {
        this.Logger.LogMagenticManagerInit(this.Id);

        this._chat.AddRange(item.Messages);
        this._inputTask = item.Messages.ToList().AsReadOnly();

        await this.PublishMessageAsync(item.Messages.AsGroupMessage(), this.Context.Topic).ConfigureAwait(false);
        await this.PrepareAsync(isReset: false, messageContext.CancellationToken).ConfigureAwait(false);
        await this.ManageAsync(messageContext.CancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async ValueTask HandleAsync(MagenticMessages.Group item, MessageContext messageContext)
    {
        this.Logger.LogMagenticManagerInvoke(this.Id);

        this._chat.AddRange(item.Messages);

        await this.ManageAsync(messageContext.CancellationToken).ConfigureAwait(false);
    }

    private async ValueTask ManageAsync(CancellationToken cancellationToken)
    {
        bool isStalled = false;
        string? stallMessage = null;

        do
        {
            string agentName = string.Empty;
            string agentInstruction = string.Empty;
            try
            {
                MagenticManagerContext context = this.CreateContext();
                MagenticProgressLedger status = await this._manager.EvaluateTaskProgressAsync(context, cancellationToken).ConfigureAwait(false);

                Debug.WriteLine($"STATUS:\n{status.ToJson()}");

                if (status.IsTaskComplete)
                {
                    ChatMessageContent finalAnswer = await this._manager.PrepareFinalAnswerAsync(context, cancellationToken).ConfigureAwait(false);
                    await this.PublishMessageAsync(finalAnswer.AsResultMessage(), this._orchestrationType, cancellationToken).ConfigureAwait(false);
                    break;
                }

                isStalled = !status.IsTaskProgressing || status.IsTaskInLoop;
                agentName = status.Name;
                agentInstruction = status.Instruction;
            }
            catch (Exception exception) when (!exception.IsCriticalException())
            {
                this.Logger.LogMagenticManagerStatusFailure(this.Context.Topic, exception);
                isStalled = true;
                stallMessage = exception.Message;
            }

            bool hasAgent = this._team.TryGetValue(agentName, out (string Type, string Description) agent);
            if (!hasAgent)
            {
                isStalled = true;
                stallMessage = $"Invalid agent selected: {agentName}";
            }

            if (isStalled)
            {
                ++this._stallCount;

                Debug.WriteLine($"TASK STALLED: #{this._stallCount}/{this._manager.MaximumStallCount} [#{this._retryCount}] -  {stallMessage}");
            }
            else
            {
                this._stallCount = Math.Max(0, this._stallCount - 1);
            }

            bool needsReset = this._stallCount >= this._manager.MaximumStallCount;

            if (!needsReset && hasAgent)
            {
                ++this._invocationCount;

                if (this._invocationCount >= this._manager.MaximumInvocationCount)
                {
                    await this.PublishMessageAsync("Maximum number of invocations reached.".AsResultMessage(), this._orchestrationType, cancellationToken).ConfigureAwait(false);
                    break;
                }

                ChatMessageContent instruction = new(AuthorRole.Assistant, agentInstruction);
                this._chat.Add(instruction);
                await this.PublishMessageAsync(instruction.AsGroupMessage(), this.Context.Topic, messageId: null, cancellationToken).ConfigureAwait(false);
                await this.PublishMessageAsync(new MagenticMessages.Speak(), agent.Type, cancellationToken).ConfigureAwait(false);
                break;
            }

            if (this._stallCount >= this._manager.MaximumStallCount)
            {
                if (this._retryCount >= this._manager.MaximumResetCount)
                {
                    this.Logger.LogMagenticManagerTaskFailed(this.Context.Topic);
                    await this.PublishMessageAsync("I've experienced multiple failures and am unable to continue.".AsResultMessage(), this._orchestrationType, cancellationToken).ConfigureAwait(false);
                    break;
                }

                this._retryCount++;
                this._stallCount = 0;

                this.Logger.LogMagenticManagerTaskReset(this.Context.Topic, this._retryCount);
                Debug.WriteLine($"TASK RESET [#{this._retryCount}]");

                await this.PublishMessageAsync(new MagenticMessages.Reset(), this.Context.Topic, messageId: null, cancellationToken).ConfigureAwait(false);
                await this.PrepareAsync(isReset: true, cancellationToken).ConfigureAwait(false);
            }
        }
        while (isStalled);
    }

    private async ValueTask PrepareAsync(bool isReset, CancellationToken cancellationToken)
    {
        ChatHistory internalChat = [.. this._chat];
        this._chat.Clear();

        MagenticManagerContext context = this.CreateContext(internalChat);

        IList<ChatMessageContent> plan;
        if (isReset)
        {
            plan = await this._manager.PlanAsync(context, cancellationToken).ConfigureAwait(false);
        }
        else
        {
            plan = await this._manager.ReplanAsync(context, cancellationToken).ConfigureAwait(false);
        }

        this._chat.AddRange(plan);
    }

    private MagenticManagerContext CreateContext(ChatHistory? chat = null) =>
        new(this._team, this._inputTask, (chat ?? this._chat), this._invocationCount, this._stallCount, this._retryCount);
}
