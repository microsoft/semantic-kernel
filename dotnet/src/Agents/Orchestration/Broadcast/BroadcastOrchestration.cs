// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Broadcast;

/// <summary>
/// %%%
/// </summary>
/// <param name="results"></param>
public delegate ValueTask BroadcastCompletedHandlerAsync(BroadcastMessages.Result[] results);

/// <summary>
/// %%%
/// </summary>
public class BroadcastOrchestration : AgentOrchestration
{
    internal sealed class Topics(string id) // %%% REVIEW
    {
        private const string Root = "BroadcastTopic";
        public TopicId Task = new($"{Root}_{nameof(Task)}_{id}", id);
        //public TopicId Result = new($"{Root}_{nameof(Result)}_{id}", id);
    }

    private readonly BroadcastCompletedHandlerAsync _completionHandler;
    private readonly Agent[] _agents;
    private readonly Topics _topics;

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="runtime"></param>
    /// <param name="completionHandler"></param>
    /// <param name="agents"></param>
    public BroadcastOrchestration(IAgentRuntime runtime, BroadcastCompletedHandlerAsync completionHandler, params Agent[] agents)
        : base(runtime)
    {
        Verify.NotNull(completionHandler, nameof(completionHandler));
        //Verify.NotEmpty(agents, nameof(agents)); // %%% TODO: Utility

        this._agents = agents;
        this._completionHandler = completionHandler;
        this._topics = new Topics(this.Id);
    }

    // ISCOMPLETE
    // RESULTS

    /// <inheritdoc />
    protected override async ValueTask MessageTaskAsync(ChatMessageContent message)
    {
        BroadcastMessages.Task task = new() { Message = message };
        await this.Runtime.PublishMessageAsync(task, this._topics.Task).ConfigureAwait(false);
    }

    /// <inheritdoc />
    protected override async ValueTask RegisterAsync()
    {
        AgentType receiverType = new($"{nameof(BroadcastReciever)}_{this.Id}");

        // All agents respond to the same message.
        foreach (Agent agent in this._agents)
        {
            await this.RegisterAgentAsync(agent, receiverType).ConfigureAwait(false);
        }

        await this.Runtime.RegisterAgentFactoryAsync(
            receiverType,
            (agentId, runtime) => ValueTask.FromResult<IHostableAgent>(new BroadcastReciever(agentId, runtime, this.HandleResult))).ConfigureAwait(false);
    }

    private async ValueTask RegisterAgentAsync(Agent agent, AgentType receiverType)
    {
        string agentType = this.GetAgentId(agent);
        await this.Runtime.RegisterAgentFactoryAsync(
            agentType,
            (agentId, runtime) => ValueTask.FromResult<IHostableAgent>(new BroadcastProxy(agentId, runtime, agent, receiverType))).ConfigureAwait(false);

        await this.RegisterTopicsAsync(agentType, this._topics.Task).ConfigureAwait(false);
    }

    private void HandleResult(BroadcastMessages.Result result)
    {
        // %%% TODO: ???
        Console.WriteLine(result);
    }
}
