// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Agents.Orchestration.Extensions;
using Microsoft.SemanticKernel.Agents.Orchestration.Transforms;
using Microsoft.SemanticKernel.Agents.Runtime;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// Called for every response is produced by any agent.
/// </summary>
/// <param name="response">The agent response</param>
public delegate ValueTask OrchestrationResponseCallback(ChatMessageContent response);

/// <summary>
/// Called when human interaction is requested.
/// </summary>
public delegate ValueTask<ChatMessageContent> OrchestrationInteractiveCallback();

/// <summary>
/// Base class for multi-agent agent orchestration patterns.
/// </summary>
/// <typeparam name="TInput">The type of the input to the orchestration.</typeparam>
/// <typeparam name="TOutput">The type of the result output by the orchestration.</typeparam>
public abstract partial class AgentOrchestration<TInput, TOutput>
{
    /// <summary>
    /// Initializes a new instance of the <see cref="AgentOrchestration{TInput, TOutput}"/> class.
    /// </summary>
    /// <param name="members">Specifies the member agents or orchestrations participating in this orchestration.</param>
    protected AgentOrchestration(params Agent[] members)
    {
        // Capture orchestration root name without generic parameters for use in
        // agent type and topic formatting as well as logging.
        this.OrchestrationLabel = this.GetType().Name.Split('`').First();

        this.Members = members;
    }

    /// <summary>
    /// Gets the description of the orchestration.
    /// </summary>
    public string Description { get; init; } = string.Empty;

    /// <summary>
    /// Gets the name of the orchestration.
    /// </summary>
    public string Name { get; init; } = string.Empty;

    /// <summary>
    /// Gets the associated logger.
    /// </summary>
    public ILoggerFactory LoggerFactory { get; init; } = NullLoggerFactory.Instance;

    /// <summary>
    /// Transforms the orchestration input into a source input suitable for processing.
    /// </summary>
    public OrchestrationInputTransform<TInput> InputTransform { get; init; } = DefaultTransforms.FromInput<TInput>;

    /// <summary>
    /// Transforms the processed result into the final output form.
    /// </summary>
    public OrchestrationOutputTransform<TOutput> ResultTransform { get; init; } = DefaultTransforms.ToOutput<TOutput>;

    /// <summary>
    /// Optional callback that is invoked for every agent response.
    /// </summary>
    public OrchestrationResponseCallback? ResponseCallback { get; init; }

    /// <summary>
    /// Gets the list of member targets involved in the orchestration.
    /// </summary>
    protected IReadOnlyList<Agent> Members { get; }

    /// <summary>
    /// Orchestration identifier without generic parameters for use in
    /// agent type and topic formatting as well as logging.
    /// </summary>
    protected string OrchestrationLabel { get; }

    /// <summary>
    /// Initiates processing of the orchestration.
    /// </summary>
    /// <param name="input">The input message.</param>
    /// <param name="runtime">The runtime associated with the orchestration.</param>
    /// <param name="cancellationToken">A cancellation token that can be used to cancel the operation.</param>
    public async ValueTask<OrchestrationResult<TOutput>> InvokeAsync(
        TInput input,
        IAgentRuntime runtime,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(input, nameof(input));

        TopicId topic = new($"{this.OrchestrationLabel}_{Guid.NewGuid().ToString().Replace("-", string.Empty)}");

        CancellationTokenSource orchestrationCancelSource = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);

        OrchestrationContext context = new(this.OrchestrationLabel, topic, this.ResponseCallback, this.LoggerFactory, cancellationToken);

        ILogger logger = this.LoggerFactory.CreateLogger(this.GetType());

        TaskCompletionSource<TOutput> completion = new();

        AgentType orchestrationType = await this.RegisterAsync(runtime, context, completion, handoff: null).ConfigureAwait(false);

        cancellationToken.ThrowIfCancellationRequested();

        logger.LogOrchestrationInvoke(this.OrchestrationLabel, topic);

        Task task = runtime.SendMessageAsync(input, orchestrationType, cancellationToken).AsTask();

        logger.LogOrchestrationYield(this.OrchestrationLabel, topic);

        return new OrchestrationResult<TOutput>(context, completion, orchestrationCancelSource, logger);
    }

    /// <summary>
    /// Initiates processing according to the orchestration pattern.
    /// </summary>
    /// <param name="runtime">The runtime associated with the orchestration.</param>
    /// <param name="topic">The unique identifier for the orchestration session.</param>
    /// <param name="input">The input to be transformed and processed.</param>
    /// <param name="entryAgent">The initial agent type used for starting the orchestration.</param>
    protected abstract ValueTask StartAsync(IAgentRuntime runtime, TopicId topic, IEnumerable<ChatMessageContent> input, AgentType? entryAgent);

    /// <summary>
    /// Orchestration specific registration, including members and returns an optional entry agent.
    /// </summary>
    /// <param name="runtime">The runtime targeted for registration.</param>
    /// <param name="context">The orchestration context.</param>
    /// <param name="registrar">A registration context.</param>
    /// <param name="logger">The logger to use during registration</param>
    /// <returns>The entry AgentType for the orchestration, if any.</returns>
    protected abstract ValueTask<AgentType?> RegisterOrchestrationAsync(IAgentRuntime runtime, OrchestrationContext context, RegistrationContext registrar, ILogger logger);

    /// <summary>
    /// Formats and returns a unique AgentType based on the provided topic and suffix.
    /// </summary>
    /// <param name="topic">The topic identifier used in formatting the agent type.</param>
    /// <param name="suffix">A suffix to differentiate the agent type.</param>
    /// <returns>A formatted AgentType object.</returns>
    protected AgentType FormatAgentType(TopicId topic, string suffix) => new($"{topic.Type}_{suffix}");

    /// <summary>
    /// Registers the orchestration's root and boot agents, setting up completion and target routing.
    /// </summary>
    /// <param name="runtime">The runtime targeted for registration.</param>
    /// <param name="context">The orchestration context.</param>
    /// <param name="completion">A TaskCompletionSource for the orchestration.</param>
    /// <param name="handoff">The actor type used for handoff.  Only defined for nested orchestrations.</param>
    /// <returns>The AgentType representing the orchestration entry point.</returns>
    private async ValueTask<AgentType> RegisterAsync(IAgentRuntime runtime, OrchestrationContext context, TaskCompletionSource<TOutput> completion, AgentType? handoff)
    {
        // Create a logger for the orchestration registration.
        ILogger logger = context.LoggerFactory.CreateLogger(this.GetType());
        logger.LogOrchestrationRegistrationStart(context.Orchestration, context.Topic);

        // Register orchestration
        RegistrationContext registrar = new(this.FormatAgentType(context.Topic, "Root"), runtime, context, completion, this.ResultTransform);
        AgentType? entryAgent = await this.RegisterOrchestrationAsync(runtime, context, registrar, logger).ConfigureAwait(false);

        // Register actor for orchestration entry-point
        AgentType orchestrationEntry =
            await runtime.RegisterAgentFactoryAsync(
                this.FormatAgentType(context.Topic, "Boot"),
                    (agentId, runtime) =>
                    {
                        RequestActor actor =
                            new(agentId,
                                runtime,
                                context,
                                this.InputTransform,
                                completion,
                                StartAsync,
                                context.LoggerFactory.CreateLogger<RequestActor>());
#if !NETCOREAPP
                        return actor.AsValueTask<IHostableAgent>();
#else
                        return ValueTask.FromResult<IHostableAgent>(actor);
#endif
                    }).ConfigureAwait(false);

        logger.LogOrchestrationRegistrationDone(context.Orchestration, context.Topic);

        return orchestrationEntry;

        ValueTask StartAsync(IEnumerable<ChatMessageContent> input) => this.StartAsync(runtime, context.Topic, input, entryAgent);
    }

    /// <summary>
    /// A context used during registration (<see cref="RegisterAsync"/>).
    /// </summary>
    public sealed class RegistrationContext(
        AgentType agentType,
        IAgentRuntime runtime,
        OrchestrationContext context,
        TaskCompletionSource<TOutput> completion,
        OrchestrationOutputTransform<TOutput> outputTransform)
    {
        /// <summary>
        /// Register the final result type.
        /// </summary>
        public async ValueTask<AgentType> RegisterResultTypeAsync<TResult>(OrchestrationResultTransform<TResult> resultTransform)
        {
            // Register actor for final result
            return
                await runtime.RegisterAgentFactoryAsync(
                    agentType,
                    (agentId, runtime) =>
                    {
                        ResultActor<TResult> actor =
                            new(agentId,
                                runtime,
                                context,
                                resultTransform,
                                outputTransform,
                                completion,
                                context.LoggerFactory.CreateLogger<ResultActor<TResult>>());
#if !NETCOREAPP
                        return actor.AsValueTask<IHostableAgent>();
#else
                        return ValueTask.FromResult<IHostableAgent>(actor);
#endif
                    }).ConfigureAwait(false);
        }
    }
}
