// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.Runtime.InProcess;

/// <summary>
/// Provides an in-process/in-memory implementation of the agent runtime.
/// </summary>
public sealed class InProcessRuntime : IAgentRuntime, IAsyncDisposable
{
    private readonly Dictionary<AgentType, Func<AgentId, IAgentRuntime, ValueTask<IHostableAgent>>> _agentFactories = [];
    private readonly Dictionary<string, ISubscriptionDefinition> _subscriptions = [];
    private readonly ConcurrentQueue<MessageDelivery> _messageDeliveryQueue = new();

    private CancellationTokenSource? _shutdownSource;
    private CancellationTokenSource? _finishSource;
    private Task _messageDeliveryTask = Task.CompletedTask;
    private Func<bool> _shouldContinue = () => true;

    // Exposed for testing purposes.
    internal int messageQueueCount;
    internal readonly Dictionary<AgentId, IHostableAgent> agentInstances = [];

    /// <summary>
    /// Gets or sets a value indicating whether agents should receive messages they send themselves.
    /// </summary>
    public bool DeliverToSelf { get; set; } //= false;

    /// <inheritdoc/>
    public async ValueTask DisposeAsync()
    {
        await this.RunUntilIdleAsync().ConfigureAwait(false);
        this._shutdownSource?.Dispose();
        this._finishSource?.Dispose();
    }

    /// <summary>
    /// Starts the runtime service.
    /// </summary>
    /// <param name="cancellationToken">Token to monitor for shutdown requests.</param>
    /// <returns>A task representing the asynchronous operation.</returns>
    /// <exception cref="InvalidOperationException">Thrown if the runtime is already started.</exception>
    public Task StartAsync(CancellationToken cancellationToken = default)
    {
        if (this._shutdownSource != null)
        {
            throw new InvalidOperationException("Runtime is already running.");
        }

        this._shutdownSource = new CancellationTokenSource();
        this._messageDeliveryTask = Task.Run(() => this.RunAsync(this._shutdownSource.Token), cancellationToken);

        return Task.CompletedTask;
    }

    /// <summary>
    /// Stops the runtime service.
    /// </summary>
    /// <param name="cancellationToken">Token to propagate when stopping the runtime.</param>
    /// <returns>A task representing the asynchronous operation.</returns>
    /// <exception cref="InvalidOperationException">Thrown if the runtime is in the process of stopping.</exception>
    public Task StopAsync(CancellationToken cancellationToken = default)
    {
        if (this._shutdownSource != null)
        {
            if (this._finishSource != null)
            {
                throw new InvalidOperationException("Runtime is already stopping.");
            }

            this._finishSource = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);

            this._shutdownSource.Cancel();
        }

        return Task.CompletedTask;
    }

    /// <summary>
    /// This will run until the message queue is empty and then stop the runtime.
    /// </summary>
    public async Task RunUntilIdleAsync()
    {
        Func<bool> oldShouldContinue = this._shouldContinue;
        this._shouldContinue = () => !this._messageDeliveryQueue.IsEmpty;

        // TODO: Do we want detach semantics?
        await this._messageDeliveryTask.ConfigureAwait(false);

        this._shouldContinue = oldShouldContinue;
    }

    /// <inheritdoc/>
    public ValueTask PublishMessageAsync(object message, TopicId topic, AgentId? sender = null, string? messageId = null, CancellationToken cancellationToken = default)
    {
        return this.ExecuteTracedAsync(async () =>
        {
            MessageDelivery delivery =
                new MessageEnvelope(message, messageId, cancellationToken)
                    .WithSender(sender)
                    .ForPublish(topic, this.PublishMessageServicerAsync);

            this._messageDeliveryQueue.Enqueue(delivery);
            Interlocked.Increment(ref this.messageQueueCount);

            await delivery.ResultSink.Future.ConfigureAwait(false);
        });
    }

    /// <inheritdoc/>
    public async ValueTask<object?> SendMessageAsync(object message, AgentId recipient, AgentId? sender = null, string? messageId = null, CancellationToken cancellationToken = default)
    {
        return await this.ExecuteTracedAsync(async () =>
        {
            MessageDelivery delivery =
                new MessageEnvelope(message, messageId, cancellationToken)
                    .WithSender(sender)
                    .ForSend(recipient, this.SendMessageServicerAsync);

            this._messageDeliveryQueue.Enqueue(delivery);
            Interlocked.Increment(ref this.messageQueueCount);

            try
            {
                return await delivery.ResultSink.Future.ConfigureAwait(false);
            }
            catch (TargetInvocationException ex) when (ex.InnerException is OperationCanceledException innerOCEx)
            {
                throw new OperationCanceledException($"Delivery of message {messageId} was cancelled.", innerOCEx);
            }
        }).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async ValueTask<AgentId> GetAgentAsync(AgentId agentId, bool lazy = true)
    {
        if (!lazy)
        {
            await this.EnsureAgentAsync(agentId).ConfigureAwait(false);
        }

        return agentId;
    }

    /// <inheritdoc/>
    public ValueTask<AgentId> GetAgentAsync(AgentType agentType, string key = AgentId.DefaultKey, bool lazy = true)
        => this.GetAgentAsync(new AgentId(agentType, key), lazy);

    /// <inheritdoc/>
    public ValueTask<AgentId> GetAgentAsync(string agent, string key = AgentId.DefaultKey, bool lazy = true)
        => this.GetAgentAsync(new AgentId(agent, key), lazy);

    /// <inheritdoc/>
    public async ValueTask<AgentMetadata> GetAgentMetadataAsync(AgentId agentId)
    {
        IHostableAgent agent = await this.EnsureAgentAsync(agentId).ConfigureAwait(false);
        return agent.Metadata;
    }

    /// <inheritdoc/>
    public async ValueTask<TAgent> TryGetUnderlyingAgentInstanceAsync<TAgent>(AgentId agentId) where TAgent : IHostableAgent
    {
        IHostableAgent agent = await this.EnsureAgentAsync(agentId).ConfigureAwait(false);

        if (agent is not TAgent concreteAgent)
        {
            throw new InvalidOperationException($"Agent with name {agentId.Type} is not of type {typeof(TAgent).Name}.");
        }

        return concreteAgent;
    }

    /// <inheritdoc/>
    public async ValueTask LoadAgentStateAsync(AgentId agentId, JsonElement state)
    {
        IHostableAgent agent = await this.EnsureAgentAsync(agentId).ConfigureAwait(false);
        await agent.LoadStateAsync(state).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async ValueTask<JsonElement> SaveAgentStateAsync(AgentId agentId)
    {
        IHostableAgent agent = await this.EnsureAgentAsync(agentId).ConfigureAwait(false);
        return await agent.SaveStateAsync().ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public ValueTask AddSubscriptionAsync(ISubscriptionDefinition subscription)
    {
        if (this._subscriptions.ContainsKey(subscription.Id))
        {
            throw new InvalidOperationException($"Subscription with id {subscription.Id} already exists.");
        }

        this._subscriptions.Add(subscription.Id, subscription);

#if !NETCOREAPP
        return Task.CompletedTask.AsValueTask();
#else
        return ValueTask.CompletedTask;
#endif
    }

    /// <inheritdoc/>
    public ValueTask RemoveSubscriptionAsync(string subscriptionId)
    {
        if (!this._subscriptions.ContainsKey(subscriptionId))
        {
            throw new InvalidOperationException($"Subscription with id {subscriptionId} does not exist.");
        }

        this._subscriptions.Remove(subscriptionId);

#if !NETCOREAPP
        return Task.CompletedTask.AsValueTask();
#else
        return ValueTask.CompletedTask;
#endif
    }

    /// <inheritdoc/>
    public async ValueTask LoadStateAsync(JsonElement state)
    {
        foreach (JsonProperty agentIdStr in state.EnumerateObject())
        {
            AgentId agentId = AgentId.FromStr(agentIdStr.Name);

            if (this._agentFactories.ContainsKey(agentId.Type))
            {
                IHostableAgent agent = await this.EnsureAgentAsync(agentId).ConfigureAwait(false);
                await agent.LoadStateAsync(agentIdStr.Value).ConfigureAwait(false);
            }
        }
    }

    /// <inheritdoc/>
    public async ValueTask<JsonElement> SaveStateAsync()
    {
        Dictionary<string, JsonElement> state = [];
        foreach (AgentId agentId in this.agentInstances.Keys)
        {
            JsonElement agentState = await this.agentInstances[agentId].SaveStateAsync().ConfigureAwait(false);
            state[agentId.ToString()] = agentState;
        }
        return JsonSerializer.SerializeToElement(state);
    }

    /// <summary>
    /// Registers an agent factory with the runtime, associating it with a specific agent type.
    /// </summary>
    /// <typeparam name="TAgent">The type of agent created by the factory.</typeparam>
    /// <param name="type">The agent type to associate with the factory.</param>
    /// <param name="factoryFunc">A function that asynchronously creates the agent instance.</param>
    /// <returns>A task representing the asynchronous operation, returning the registered agent type.</returns>
    public ValueTask<AgentType> RegisterAgentFactoryAsync<TAgent>(AgentType type, Func<AgentId, IAgentRuntime, ValueTask<TAgent>> factoryFunc) where TAgent : IHostableAgent
        // Declare the lambda return type explicitly, as otherwise the compiler will infer 'ValueTask<TAgent>'
        // and recurse into the same call, causing a stack overflow.
        => this.RegisterAgentFactoryAsync(type, async ValueTask<IHostableAgent> (agentId, runtime) => await factoryFunc(agentId, runtime).ConfigureAwait(false));

    /// <inheritdoc/>
    public ValueTask<AgentType> RegisterAgentFactoryAsync(AgentType type, Func<AgentId, IAgentRuntime, ValueTask<IHostableAgent>> factoryFunc)
    {
        if (this._agentFactories.ContainsKey(type))
        {
            throw new InvalidOperationException($"Agent with type {type} already exists.");
        }

        this._agentFactories.Add(type, factoryFunc);

#if !NETCOREAPP
        return type.AsValueTask();
#else
        return ValueTask.FromResult(type);
#endif
    }

    /// <inheritdoc/>
    public ValueTask<AgentProxy> TryGetAgentProxyAsync(AgentId agentId)
    {
        AgentProxy proxy = new(agentId, this);

#if !NETCOREAPP
        return proxy.AsValueTask();
#else
        return ValueTask.FromResult(proxy);
#endif
    }

    private ValueTask ProcessNextMessageAsync(CancellationToken cancellation = default)
    {
        if (this._messageDeliveryQueue.TryDequeue(out MessageDelivery? delivery))
        {
            Interlocked.Decrement(ref this.messageQueueCount);
            Debug.WriteLine($"Processing message {delivery.Message.MessageId}...");
            return delivery.InvokeAsync(cancellation);
        }

#if !NETCOREAPP
        return Task.CompletedTask.AsValueTask();
#else
        return ValueTask.CompletedTask;
#endif
    }

    private async Task RunAsync(CancellationToken cancellation)
    {
        Dictionary<Guid, Task> pendingTasks = [];
        while (!cancellation.IsCancellationRequested && this._shouldContinue())
        {
            // Get a unique task id
            Guid taskId;
            do
            {
                taskId = Guid.NewGuid();
            } while (pendingTasks.ContainsKey(taskId));

            // There is potentially a race condition here, but even if we leak a Task, we will
            // still catch it on the Finish() pass.
            ValueTask processTask = this.ProcessNextMessageAsync(cancellation);
            await Task.Yield();

            // Check if the task is already completed
            if (processTask.IsCompleted)
            {
                continue;
            }

            Task actualTask = processTask.AsTask();
            pendingTasks.Add(taskId, actualTask.ContinueWith(t => pendingTasks.Remove(taskId), TaskScheduler.Current));
        }

        // The pending task dictionary may contain null values when a race condition is experienced during
        // the prior "ContinueWith" call.  This could be solved with a ConcurrentDictionary, but locking
        // is entirely undesirable in this context.
        await Task.WhenAll([.. pendingTasks.Values.Where(task => task is not null)]).ConfigureAwait(false);
        await this.FinishAsync(this._finishSource?.Token ?? CancellationToken.None).ConfigureAwait(false);
    }

    private async ValueTask PublishMessageServicerAsync(MessageEnvelope envelope, CancellationToken deliveryToken)
    {
        if (!envelope.Topic.HasValue)
        {
            throw new InvalidOperationException("Message must have a topic to be published.");
        }

        List<Exception> exceptions = [];
        TopicId topic = envelope.Topic.Value;
        foreach (ISubscriptionDefinition subscription in this._subscriptions.Values.Where(subscription => subscription.Matches(topic)))
        {
            try
            {
                deliveryToken.ThrowIfCancellationRequested();

                AgentId? sender = envelope.Sender;

                using CancellationTokenSource combinedSource = CancellationTokenSource.CreateLinkedTokenSource(envelope.Cancellation, deliveryToken);
                MessageContext messageContext = new(envelope.MessageId, combinedSource.Token)
                {
                    Sender = sender,
                    Topic = topic,
                    IsRpc = false
                };

                AgentId agentId = subscription.MapToAgent(topic);
                if (!this.DeliverToSelf && sender.HasValue && sender == agentId)
                {
                    continue;
                }

                IHostableAgent agent = await this.EnsureAgentAsync(agentId).ConfigureAwait(false);

                // TODO: Cancellation propagation!
                await agent.OnMessageAsync(envelope.Message, messageContext).ConfigureAwait(false);
            }
            catch (Exception ex) when (!ex.IsCriticalException())
            {
                exceptions.Add(ex);
            }
        }

        if (exceptions.Count > 0)
        {
            // TODO: Unwrap TargetInvocationException?
            throw new AggregateException("One or more exceptions occurred while processing the message.", exceptions);
        }
    }

    private async ValueTask<object?> SendMessageServicerAsync(MessageEnvelope envelope, CancellationToken deliveryToken)
    {
        if (!envelope.Receiver.HasValue)
        {
            throw new InvalidOperationException("Message must have a receiver to be sent.");
        }

        using CancellationTokenSource combinedSource = CancellationTokenSource.CreateLinkedTokenSource(envelope.Cancellation, deliveryToken);
        MessageContext messageContext = new(envelope.MessageId, combinedSource.Token)
        {
            Sender = envelope.Sender,
            IsRpc = false
        };

        AgentId receiver = envelope.Receiver.Value;
        IHostableAgent agent = await this.EnsureAgentAsync(receiver).ConfigureAwait(false);

        return await agent.OnMessageAsync(envelope.Message, messageContext).ConfigureAwait(false);
    }

    private async ValueTask<IHostableAgent> EnsureAgentAsync(AgentId agentId)
    {
        if (!this.agentInstances.TryGetValue(agentId, out IHostableAgent? agent))
        {
            if (!this._agentFactories.TryGetValue(agentId.Type, out Func<AgentId, IAgentRuntime, ValueTask<IHostableAgent>>? factoryFunc))
            {
                throw new InvalidOperationException($"Agent with name {agentId.Type} not found.");
            }

            agent = await factoryFunc(agentId, this).ConfigureAwait(false);
            this.agentInstances.Add(agentId, agent);
        }

        return this.agentInstances[agentId];
    }

    private async Task FinishAsync(CancellationToken token)
    {
        foreach (IHostableAgent agent in this.agentInstances.Values)
        {
            if (!token.IsCancellationRequested)
            {
                await agent.CloseAsync().ConfigureAwait(false);
            }
        }

        this._shutdownSource?.Dispose();
        this._finishSource?.Dispose();
        this._finishSource = null;
        this._shutdownSource = null;
    }

#pragma warning disable CA1822 // Mark members as static
    private ValueTask<T> ExecuteTracedAsync<T>(Func<ValueTask<T>> func)
#pragma warning restore CA1822 // Mark members as static
    {
        // TODO: Bind tracing
        return func();
    }

#pragma warning disable CA1822 // Mark members as static
    private ValueTask ExecuteTracedAsync(Func<ValueTask> func)
#pragma warning restore CA1822 // Mark members as static
    {
        // TODO: Bind tracing
        return func();
    }
}
