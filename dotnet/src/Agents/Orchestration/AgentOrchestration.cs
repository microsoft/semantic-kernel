// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;
using Microsoft.AgentRuntime.Core;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// Base class for multi-agent orchestration patterns.
/// </summary>
public abstract partial class AgentOrchestration<TInput, TSource, TResult, TOutput> : Orchestratable
{
    private readonly string _orchestrationType;

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentOrchestration{TInput, TSource, TResult, TOutput}"/> class.
    /// </summary>
    /// <param name="runtime">The runtime associated with the orchestration.</param>
    /// <param name="members">// %%% COMMENT</param>
    protected AgentOrchestration(IAgentRuntime runtime, params OrchestrationTarget[] members)
    {
        Verify.NotNull(runtime, nameof(runtime));

        this.Runtime = runtime;
        this.Members = members;
        this._orchestrationType = this.GetType().Name.Split('`').First();
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    public string Name { get; init; } = string.Empty;

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    public string Description { get; init; } = string.Empty;

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    public Func<TInput, TSource>? InputTransform { get; init; } // %%% TODO: ASYNC

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    public Func<TResult, TOutput>? ResultTransform { get; init; } // %%% TODO: ASYNC

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    protected IReadOnlyList<OrchestrationTarget> Members { get; }

    /// <summary>
    /// Gets the runtime associated with the orchestration.
    /// </summary>
    protected IAgentRuntime Runtime { get; }

    /// <summary>
    /// Initiate processing of the orchestration.
    /// </summary>
    /// <param name="input">The input message</param>
    /// <param name="timeout">// %%% COMMENT</param>
    public async ValueTask<OrchestrationResult<TOutput>> InvokeAsync(TInput input, TimeSpan? timeout = null)
    {
        Verify.NotNull(input, nameof(input));

        TopicId topic = new($"ID_{Guid.NewGuid().ToString().Replace("-", string.Empty)}");

        TaskCompletionSource<TOutput> completion = new();

        Trace.WriteLine($"!!! ORCHESTRATION REGISTER: {topic}\n");

        AgentType orchestrationType = await this.RegisterAsync(topic, completion).ConfigureAwait(false);

        Trace.WriteLine($"\n!!! ORCHESTRATION INVOKE: {orchestrationType}\n");

        //await this.Runtime.SendMessageAsync(input, new AgentId(orchestrationType, AgentId.DefaultKey)).ConfigureAwait(false);
        Task task = this.Runtime.SendMessageAsync(input, new AgentId(orchestrationType, AgentId.DefaultKey)).AsTask(); // %%% TODO: REFINE

        Trace.WriteLine($"\n!!! ORCHESTRATION YIELD: {orchestrationType}");

        return new OrchestrationResult<TOutput>(topic, completion);
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="topic"></param>
    /// <param name="suffix"></param>
    /// <returns></returns>
    protected AgentType FormatAgentType(TopicId topic, string suffix) => new($"{topic.Type}_{this._orchestrationType}_{suffix}");

    /// <summary>
    /// Initiate processing according to the orchestration pattern.
    /// </summary>
    /// <param name="topic">// %%% COMMENT</param>
    /// <param name="input">The input message</param>
    /// <param name="entryAgent">// %%% COMMENT</param>
    protected abstract ValueTask StartAsync(TopicId topic, TSource input, AgentType? entryAgent);

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="topic"></param>
    /// <param name="orchestrationType"></param>
    /// <returns></returns>
    protected abstract ValueTask<AgentType?> RegisterMembersAsync(TopicId topic, AgentType orchestrationType);

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="externalTopic"></param>
    /// <param name="targetActor"></param>
    /// <returns></returns>
    protected internal override ValueTask<AgentType> RegisterAsync(TopicId externalTopic, AgentType? targetActor)
    {
        TopicId orchestrationTopic = new($"{externalTopic.Type}_{Guid.NewGuid().ToString().Replace("-", string.Empty)}");

        return this.RegisterAsync(orchestrationTopic, completion: null, targetActor);
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    protected async Task SubscribeAsync(string agentType, params TopicId[] topics)
    {
        for (int index = 0; index < topics.Length; ++index)
        {
            await this.Runtime.AddSubscriptionAsync(new TypeSubscription(topics[index].Type, agentType)).ConfigureAwait(false);
        }
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="topic"></param>
    /// <param name="completion"></param>
    /// <param name="targetActor"></param>
    /// <returns></returns>
    private async ValueTask<AgentType> RegisterAsync(TopicId topic, TaskCompletionSource<TOutput>? completion, AgentType? targetActor = null)
    {
        // Register actor for final result
        AgentType orchestrationFinal = this.FormatAgentType(topic, "Root");
        await this.Runtime.RegisterAgentFactoryAsync(
            orchestrationFinal,
            (agentId, runtime) =>
                ValueTask.FromResult<IHostableAgent>(
                    new ResultActor(agentId, runtime, this.ResultTransform!, completion) // %%% NULL OVERRIDE
                    {
                        CompletionTarget = targetActor,
                    })).ConfigureAwait(false);

        // Register orchestration members
        AgentType? entryAgent = await this.RegisterMembersAsync(topic, orchestrationFinal).ConfigureAwait(false);

        // Register actor for orchestration entry-point
        AgentType orchestrationEntry = this.FormatAgentType(topic, "Boot");
        await this.Runtime.RegisterAgentFactoryAsync(
            orchestrationEntry,
            (agentId, runtime) =>
                ValueTask.FromResult<IHostableAgent>(
                    new RequestActor(agentId, runtime, this.InputTransform!, async (TSource source) => await this.StartAsync(topic, source, entryAgent).ConfigureAwait(false))) // %%% NULL OVERRIDE
        ).ConfigureAwait(false);

        return orchestrationEntry;
    }
}
