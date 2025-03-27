// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Handoff;

/// <summary>
/// %%%
/// </summary>
/// <param name="result"></param>
public delegate ValueTask HandoffCompletedHandlerAsync(ChatMessageContent result);

/// <summary>
/// %%%
/// </summary>
public sealed class HandoffOrchestration : AgentOrchestration
{
    private readonly HandoffCompletedHandlerAsync _completionHandler;
    private readonly Agent[] _agents;
    private readonly AgentType _firstAgent;
    private ChatMessageContent? _result;

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="runtime"></param>
    /// <param name="completionHandler"></param>
    /// <param name="agents"></param>
    public HandoffOrchestration(IAgentRuntime runtime, HandoffCompletedHandlerAsync completionHandler, params Agent[] agents)
        : base(runtime)
    {
        Verify.NotNull(completionHandler, nameof(completionHandler));
        //Verify.NotEmpty(agents, nameof(agents)); // %%% TODO: Utility

        this._completionHandler = completionHandler;
        this._agents = agents;
        this._firstAgent = this.GetAgentId(agents.First());
    }

    /// <inheritdoc />
    public override bool IsComplete => this._result != null;

    /// <inheritdoc />
    protected override async ValueTask MessageTaskAsync(ChatMessageContent message)
    {
        AgentId agentId = await this.Runtime.GetAgentAsync(this._firstAgent).ConfigureAwait(false); // %%% COMMON PATTERN
        await this.Runtime.SendMessageAsync(message.ToInput(), agentId).ConfigureAwait(false);
    }

    /// <inheritdoc />
    protected override async ValueTask RegisterAsync()
    {
        AgentType receiverType = new($"{nameof(HandoffReciever)}_{this.Id}");

        // Each agent handsoff its result to the next agent.
        for (int index = 0; index < this._agents.Length; ++index)
        {
            Agent agent = this._agents[index];
            AgentType nextAgent = index == this._agents.Length - 1 ? receiverType : this.GetAgentId(this._agents[index + 1]);
            string agentType = this.GetAgentId(agent);
            await this.Runtime.RegisterAgentFactoryAsync(
                agentType,
                (agentId, runtime) => ValueTask.FromResult<IHostableAgent>(new HandoffProxy(agentId, runtime, agent, nextAgent))).ConfigureAwait(false);
        }

        await this.Runtime.RegisterAgentFactoryAsync(
            receiverType,
            (agentId, runtime) => ValueTask.FromResult<IHostableAgent>(new HandoffReciever(agentId, runtime, this.HandleResultAsync))).ConfigureAwait(false);
    }

    private async ValueTask HandleResultAsync(HandoffMessages.Input result)
    {
        Interlocked.CompareExchange(ref this._result, result.Results.Last(), null);
        if (this.IsComplete)
        {
            await this._completionHandler.Invoke(this._result).ConfigureAwait(false);
        }
    }
}
