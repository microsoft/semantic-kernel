// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// %%%
/// </summary>
public abstract class AgentOrchestration
{
    private const int IsRegistered = 1;
    private const int NotRegistered = 0;
    private int _isRegistered = NotRegistered;

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="runtime"></param>
    protected AgentOrchestration(IAgentRuntime runtime)
    {
        Verify.NotNull(runtime, nameof(runtime));

        this.Runtime = runtime;
        //this.Id = $"{this.GetType().Name}_{Guid.NewGuid():N}";
        this.Id = Guid.NewGuid().ToString("N");
    }

    /// <summary>
    /// %%%
    /// </summary>
    public string Id { get; }

    /// <summary>
    /// %%%
    /// </summary>
    protected IAgentRuntime Runtime { get; }

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="message"></param>
    /// <returns></returns>
    public async ValueTask StartAsync(ChatMessageContent message) // %%% IS SUFFICIENTLY FLEXIBLE ???
    {
        Verify.NotNull(message, nameof(message));

        if (Interlocked.CompareExchange(ref this._isRegistered, NotRegistered, IsRegistered) == NotRegistered)
        {
            await this.RegisterAsync().ConfigureAwait(false);
        }

        await this.MessageTaskAsync(message).ConfigureAwait(false);
    }

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="message"></param>
    /// <returns></returns>
    protected abstract ValueTask MessageTaskAsync(ChatMessageContent message);

    /// <summary>
    /// %%%
    /// </summary>
    protected abstract ValueTask RegisterAsync();

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="agentType"></param>
    /// <param name="topics"></param>
    /// <returns></returns>
    protected async Task RegisterTopicsAsync(string agentType, params TopicId[] topics)
    {
        for (int index = 0; index < topics.Length; ++index)
        {
            await this.Runtime.AddSubscriptionAsync(new Subscription(topics[index], agentType)).ConfigureAwait(false);
        }
    }

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="agent"></param>
    /// <returns></returns>
    protected string GetAgentId(Agent agent)
    {
        return (agent.Name ?? $"{agent.GetType().Name}_{agent.Id}").Replace("-", "_");
    }
}
