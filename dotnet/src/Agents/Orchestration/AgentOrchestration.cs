// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Agents.Orchestration.Extensions;
using Microsoft.SemanticKernel.Agents.Runtime;
using Microsoft.SemanticKernel.Agents.Runtime.Core;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// Base class for multi-agent agent orchestration patterns.
/// </summary>
public abstract partial class AgentOrchestration<TInput, TSource, TResult, TOutput> : Orchestratable
{
    private readonly string _orchestrationRoot;

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentOrchestration{TInput, TSource, TResult, TOutput}"/> class.
    /// </summary>
    /// <param name="name">// %%% COMMENT</param>
    /// <param name="runtime">The runtime associated with the orchestration.</param>
    /// <param name="members">Specifies the member agents or orchestrations participating in this orchestration.</param>
    protected AgentOrchestration(string name, IAgentRuntime runtime, params OrchestrationTarget[] members)
    {
        Verify.NotNull(runtime, nameof(runtime));

        this.Runtime = runtime;
        this.Members = members;
        this._orchestrationRoot = name;
    }

    /// <summary>
    /// Gets the name of the orchestration.
    /// </summary>
    public string Name { get; init; } = string.Empty;

    /// <summary>
    /// Gets the description of the orchestration.
    /// </summary>
    public string Description { get; init; } = string.Empty;

    /// <summary>
    /// Gets the associated logger.
    /// </summary>
    public ILoggerFactory LoggerFactory { get; init; } = NullLoggerFactory.Instance;

    /// <summary>
    /// Transforms the orchestration input into a source input suitable for processing.
    /// </summary>
    public Func<TInput, ValueTask<TSource>>? InputTransform { get; init; }

    /// <summary>
    /// Transforms the processed result into the final output form.
    /// </summary>
    public Func<TResult, ValueTask<TOutput>>? ResultTransform { get; init; }

    /// <summary>
    /// Gets the list of member targets involved in the orchestration.
    /// </summary>
    protected IReadOnlyList<OrchestrationTarget> Members { get; }

    /// <summary>
    /// Gets the runtime associated with the orchestration.
    /// </summary>
    protected IAgentRuntime Runtime { get; }

    /// <summary>
    /// Initiates processing of the orchestration.
    /// </summary>
    /// <param name="input">The input message.</param>
    /// <param name="timeout">Optional timeout for the orchestration process.</param>
    public async ValueTask<OrchestrationResult<TOutput>> InvokeAsync(TInput input, TimeSpan? timeout = null)
    {
        ILogger logger = this.LoggerFactory.CreateLogger(this.GetType());

        Verify.NotNull(input, nameof(input));

        TopicId topic = new($"ID_{Guid.NewGuid().ToString().Replace("-", string.Empty)}");

        TaskCompletionSource<TOutput> completion = new();

        AgentType orchestrationType = await this.RegisterAsync(topic, completion, handoff: null, this.LoggerFactory).ConfigureAwait(false);

        logger.LogOrchestrationInvoke(this._orchestrationRoot, topic);

        Task task = this.Runtime.SendMessageAsync(input, orchestrationType).AsTask();

        logger.LogOrchestrationYield(this._orchestrationRoot, topic);

        return new OrchestrationResult<TOutput>(this._orchestrationRoot, topic, completion, logger);
    }

    /// <summary>
    /// Formats and returns a unique AgentType based on the provided topic and suffix.
    /// </summary>
    /// <param name="topic">The topic identifier used in formatting the agent type.</param>
    /// <param name="suffix">A suffix to differentiate the agent type.</param>
    /// <returns>A formatted AgentType object.</returns>
    protected AgentType FormatAgentType(TopicId topic, string suffix) => new($"{topic.Type}_{this._orchestrationRoot}_{suffix}");

    /// <summary>
    /// Initiates processing according to the orchestration pattern.
    /// </summary>
    /// <param name="topic">The unique identifier for the orchestration session.</param>
    /// <param name="input">The input message to be transformed and processed.</param>
    /// <param name="entryAgent">The initial agent type used for starting the orchestration.</param>
    protected abstract ValueTask StartAsync(TopicId topic, TSource input, AgentType? entryAgent);

    /// <summary>
    /// Registers additional orchestration members and returns the entry agent if available.
    /// </summary>
    /// <param name="topic">The topic identifier for the orchestration session.</param>
    /// <param name="orchestrationType">The orchestration type used in registration.</param>
    /// <returns>The entry AgentType for the orchestration, if any.</returns>
    /// <param name="loggerFactory">The active logger factory.</param>
    /// <param name="logger">The logger to use during registration</param>
    protected abstract ValueTask<AgentType?> RegisterMembersAsync(TopicId topic, AgentType orchestrationType, ILoggerFactory loggerFactory, ILogger logger); // %%% TODO - CLASS LEVEL

    /// <summary>
    /// Registers the orchestration with the runtime using an external topic and an optional target actor.
    /// </summary>
    /// <param name="externalTopic">The external topic identifier to register with.</param>
    /// <param name="handoff">The actor type used for handoff.  Only defined for nested orchestrations.</param>
    /// <param name="loggerFactory">The active logger factory.</param>
    /// <returns>A ValueTask containing the AgentType that indicates the registered agent.</returns>
    protected internal override ValueTask<AgentType> RegisterAsync(TopicId externalTopic, AgentType? handoff, ILoggerFactory loggerFactory)
    {
        TopicId orchestrationTopic = new($"{externalTopic.Type}_{Guid.NewGuid().ToString().Replace("-", string.Empty)}");

        return this.RegisterAsync(orchestrationTopic, completion: null, handoff, loggerFactory);
    }

    /// <summary>
    /// Subscribes the specified agent type to the provided topics.
    /// </summary>
    /// <param name="agentType">The agent type to subscribe.</param>
    /// <param name="topics">A variable list of topics for subscription.</param>
    protected async Task SubscribeAsync(string agentType, params TopicId[] topics)
    {
        for (int index = 0; index < topics.Length; ++index)
        {
            await this.Runtime.AddSubscriptionAsync(new TypeSubscription(topics[index].Type, agentType)).ConfigureAwait(false);
        }
    }

    /// <summary>
    /// Registers the orchestration's root and boot agents, setting up completion and target routing.
    /// </summary>
    /// <param name="topic">The unique topic for the orchestration session.</param>
    /// <param name="completion">A TaskCompletionSource for the final result output, if applicable.</param>
    /// <param name="handoff">The actor type used for handoff.  Only defined for nested orchestrations.</param>
    /// <param name="loggerFactory">The logger factory to use during initialization.</param>
    /// <returns>The AgentType representing the orchestration entry point.</returns>
    private async ValueTask<AgentType> RegisterAsync(TopicId topic, TaskCompletionSource<TOutput>? completion, AgentType? handoff, ILoggerFactory loggerFactory)
    {
        // Use the orchestration's logger factory, if assigned; otherwise, use the provided factory.
        if (this.LoggerFactory.GetType() != typeof(NullLoggerFactory))
        {
            loggerFactory = this.LoggerFactory;
        }
        // Create a logger for the orchestration registration.
        ILogger logger = loggerFactory.CreateLogger(this.GetType());

        logger.LogOrchestrationRegistrationStart(this._orchestrationRoot, topic);

        if (this.InputTransform == null)
        {
            throw new InvalidOperationException("InputTransform must be set before invoking the orchestration.");
        }
        if (this.ResultTransform == null)
        {
            throw new InvalidOperationException("ResultTransform must be set before invoking the orchestration.");
        }

        // Register actor for final result
        AgentType orchestrationFinal =
            await this.Runtime.RegisterAgentFactoryAsync(
                this.FormatAgentType(topic, "Root"),
                (agentId, runtime) =>
                    ValueTask.FromResult<IHostableAgent>(
                        new ResultActor(agentId, runtime, this._orchestrationRoot, this.ResultTransform, completion, loggerFactory.CreateLogger<ResultActor>())
                        {
                            CompletionTarget = handoff,
                        })).ConfigureAwait(false);

        // Register orchestration members
        AgentType? entryAgent = await this.RegisterMembersAsync(topic, orchestrationFinal, loggerFactory, logger).ConfigureAwait(false);

        // Register actor for orchestration entry-point
        AgentType orchestrationEntry =
            await this.Runtime.RegisterAgentFactoryAsync(
                this.FormatAgentType(topic, "Boot"),
                (agentId, runtime) =>
                    ValueTask.FromResult<IHostableAgent>(
                        new RequestActor(agentId, runtime, this._orchestrationRoot, this.InputTransform, (TSource source) => this.StartAsync(topic, source, entryAgent), loggerFactory.CreateLogger<RequestActor>()))
            ).ConfigureAwait(false);

        logger.LogOrchestrationRegistrationDone(this._orchestrationRoot, topic);

        return orchestrationEntry;
    }
}
