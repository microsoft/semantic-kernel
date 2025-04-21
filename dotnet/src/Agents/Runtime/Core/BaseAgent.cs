// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Agents.Runtime.Core.Internal;

namespace Microsoft.SemanticKernel.Agents.Runtime.Core;

/// <summary>
/// Represents the base class for an agent in the AutoGen system.
/// </summary>
public abstract class BaseAgent : IHostableAgent, ISaveState
{
    /// <summary>
    /// The activity source for tracing.
    /// </summary>
    public static readonly ActivitySource TraceSource = new($"{typeof(IAgent).Namespace}");

    private readonly Dictionary<Type, HandlerInvoker> _handlerInvokers;
    private readonly IAgentRuntime _runtime;

    /// <summary>
    /// Provides logging capabilities used for diagnostic and operational information.
    /// </summary>
    protected internal ILogger Logger { get; }

    /// <summary>
    /// Gets the description of the agent.
    /// </summary>
    protected string Description { get; }

    /// <summary>
    /// Gets the unique identifier of the agent.
    /// </summary>
    public AgentId Id { get; }

    /// <summary>
    /// Gets the metadata of the agent.
    /// </summary>
    public AgentMetadata Metadata { get; }

    /// <summary>
    /// Initializes a new instance of the BaseAgent class with the specified identifier, runtime, description, and optional logger.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime environment in which the agent operates.</param>
    /// <param name="description">A brief description of the agent's purpose.</param>
    /// <param name="logger">An optional logger for recording diagnostic information.</param>
    protected BaseAgent(
        AgentId id,
        IAgentRuntime runtime,
        string description,
        ILogger? logger = null)
    {
        this.Logger = logger ?? NullLogger.Instance;

        this.Id = id;
        this.Description = description;
        this.Metadata = new AgentMetadata(this.Id.Type, this.Id.Key, this.Description);

        this._runtime = runtime;
        this._handlerInvokers = HandlerInvoker.ReflectAgentHandlers(this);
    }

    /// <summary>
    /// Handles an incoming message by determining its type and invoking the corresponding handler method if available.
    /// </summary>
    /// <param name="message">The message object to be handled.</param>
    /// <param name="messageContext">The context associated with the message.</param>
    /// <returns>A ValueTask that represents the asynchronous operation, containing the response object or null.</returns>
    public async ValueTask<object?> OnMessageAsync(object message, MessageContext messageContext)
    {
        // Determine type of message, then get handler method and invoke it
        Type messageType = message.GetType();
        if (this._handlerInvokers.TryGetValue(messageType, out HandlerInvoker? handlerInvoker))
        {
            return await handlerInvoker.InvokeAsync(message, messageContext).ConfigureAwait(false);
        }

        return null;
    }

    /// <inheritdoc/>
    public virtual ValueTask<JsonElement> SaveStateAsync()
    {
#if !NETCOREAPP
        return JsonDocument.Parse("{}").RootElement.AsValueTask();
#else
        return ValueTask.FromResult(JsonDocument.Parse("{}").RootElement);
#endif
    }

    /// <inheritdoc/>
    public virtual ValueTask LoadStateAsync(JsonElement state)
    {
#if !NETCOREAPP
        return Task.CompletedTask.AsValueTask();
#else
        return ValueTask.CompletedTask;
#endif
    }

    /// <summary>
    /// Closes this agent gracefully by releasing allocated resources and performing any necessary cleanup.
    /// </summary>
    public virtual ValueTask CloseAsync()
    {
#if !NETCOREAPP
        return Task.CompletedTask.AsValueTask();
#else
        return ValueTask.CompletedTask;
#endif
    }

    /// <summary>
    /// Sends a message to a specified recipient agent through the runtime.
    /// </summary>
    /// <param name="agent">The requested agent's type.</param>
    /// <param name="cancellationToken">A token used to cancel the operation if needed.</param>
    /// <returns>A ValueTask that represents the asynchronous operation, returning the response object or null.</returns>
    protected async ValueTask<AgentId?> GetAgentAsync(AgentType agent, CancellationToken cancellationToken = default)
    {
        try
        {
            return await this._runtime.GetAgentAsync(agent, lazy: false).ConfigureAwait(false);
        }
        catch (InvalidOperationException)
        {
            return null;
        }
    }

    /// <summary>
    /// Sends a message to a specified recipient agent through the runtime.
    /// </summary>
    /// <param name="message">The message object to send.</param>
    /// <param name="recipient">The recipient agent's identifier.</param>
    /// <param name="messageId">An optional identifier for the message.</param>
    /// <param name="cancellationToken">A token used to cancel the operation if needed.</param>
    /// <returns>A ValueTask that represents the asynchronous operation, returning the response object or null.</returns>
    protected ValueTask<object?> SendMessageAsync(object message, AgentId recipient, string? messageId = null, CancellationToken cancellationToken = default)
    {
        return this._runtime.SendMessageAsync(message, recipient, sender: this.Id, messageId, cancellationToken);
    }

    /// <summary>
    /// Publishes a message to all agents subscribed to a specific topic through the runtime.
    /// </summary>
    /// <param name="message">The message object to publish.</param>
    /// <param name="topic">The topic identifier to which the message is published.</param>
    /// <param name="messageId">An optional identifier for the message.</param>
    /// <param name="cancellationToken">A token used to cancel the operation if needed.</param>
    /// <returns>A ValueTask that represents the asynchronous publish operation.</returns>
    protected ValueTask PublishMessageAsync(object message, TopicId topic, string? messageId = null, CancellationToken cancellationToken = default)
    {
        return this._runtime.PublishMessageAsync(message, topic, sender: this.Id, messageId, cancellationToken);
    }
}
