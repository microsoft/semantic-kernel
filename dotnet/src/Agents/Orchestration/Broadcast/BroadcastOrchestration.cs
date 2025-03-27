// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Concurrent;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Broadcast;

/// <summary>
/// %%%
/// </summary>
/// <param name="results"></param>
public delegate ValueTask BroadcastCompletedHandlerAsync(ChatMessageContent[] results);

/// <summary>
/// %%%
/// </summary>
public sealed class BroadcastOrchestration : AgentOrchestration
{
    private readonly BroadcastCompletedHandlerAsync _completionHandler;
    private readonly Agent[] _agents;
    private readonly TopicId _topic;
    private readonly ConcurrentQueue<ChatMessageContent> _results;
    private int _resultCount;

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
        this._topic = new($"BroadcastTopic_{nameof(Task)}_{this.Id}", this.Id);
        this._results = [];
    }

    /// <inheritdoc />
    public override bool IsComplete => this._resultCount == this._agents.Length;

    /// <inheritdoc />
    protected override async ValueTask MessageTaskAsync(ChatMessageContent message)
    {
        await this.Runtime.PublishMessageAsync(message.ToTask(), this._topic).ConfigureAwait(false);
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
            (agentId, runtime) => ValueTask.FromResult<IHostableAgent>(new BroadcastReciever(agentId, runtime, this.HandleResultAsync))).ConfigureAwait(false);
    }

    private async ValueTask RegisterAgentAsync(Agent agent, AgentType receiverType)
    {
        string agentType = this.GetAgentId(agent);
        await this.Runtime.RegisterAgentFactoryAsync(
            agentType,
            (agentId, runtime) => ValueTask.FromResult<IHostableAgent>(new BroadcastProxy(agentId, runtime, agent, receiverType))).ConfigureAwait(false);

        await this.RegisterTopicsAsync(agentType, this._topic).ConfigureAwait(false);
    }

    private async ValueTask HandleResultAsync(BroadcastMessages.Result result)
    {
        this._results.Enqueue(result.Message);
        Interlocked.Increment(ref this._resultCount);
        if (this.IsComplete)
        {
            await this._completionHandler.Invoke(this._results.ToArray()).ConfigureAwait(false);
        }
    }
}
