// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// Defines a signature for message processing.
/// </summary>
/// <param name="message">The messaging being processed.</param>
/// <param name="messageContext">The message context.</param>
public delegate ValueTask MessageHandler(object message, MessageContext messageContext);

/// <summary>
/// An base agent that can be hosted in a runtime (<see cref="IAgentRuntime"/>).
/// </summary>
public abstract class RuntimeAgent : IHostableAgent
{
    private readonly IAgentRuntime _runtime;
    private readonly Dictionary<Type, MessageHandler> _handlers;

    /// <summary>
    /// Initializes a new instance of the <see cref="RuntimeAgent"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="description">The agent description (exposed in <see cref="Metadata"/>).</param>
    protected RuntimeAgent(AgentId id, IAgentRuntime runtime, string description)
    {
        this._handlers = [];
        this._runtime = runtime;
        this.Id = id;
        this.Metadata = new(id.Type, id.Key, description);
    }

    /// <inheritdoc/>
    public AgentId Id { get; }

    /// <inheritdoc/>
    public AgentMetadata Metadata { get; }

    /// <inheritdoc/>
    public virtual ValueTask CloseAsync() => ValueTask.CompletedTask;

    /// <inheritdoc/>
    public async ValueTask<object?> OnMessageAsync(object message, MessageContext messageContext)
    {
        // Match all handlers for the message type, including if the handler declares a base type of the message.
        // Order for invoking handlers is entirely independant.
        Task[] tasks =
            [.. this._handlers.Keys
                .Where(key => key.IsAssignableFrom(message.GetType()))
                .Select(key => this._handlers[key].Invoke(message, messageContext).AsTask())];

        Debug.WriteLine($"HANDLE MESSAGE - {message.GetType().Name}/{messageContext.Topic}: #{tasks.Length} ");

        await Task.WhenAll(tasks).ConfigureAwait(false);

        return null;
    }

    /// <summary>
    /// Register the handler for a given message type.
    /// </summary>
    /// <typeparam name="TMessage">The message type</typeparam>
    /// <param name="messageHandler">The message handler</param>
    /// <remarks>
    /// The targeted message type may be the base type of the actual message.
    /// </remarks>
    protected void RegisterHandler<TMessage>(Func<TMessage, MessageContext, ValueTask> messageHandler)
    {
        this._handlers[typeof(TMessage)] = (message, context) => messageHandler((TMessage)message, context);
    }

    /// <summary>
    /// Publishes a message to all agents subscribed to the given topic.
    /// </summary>
    /// <typeparam name="TMessage">The message type</typeparam>
    /// <param name="message">The message to publish.</param>
    /// <param name="topic">The topic to which to publish the message.</param>
    protected async Task PublishMessageAsync<TMessage>(TMessage message, TopicId topic) where TMessage : class
    {
        await this._runtime.PublishMessageAsync(message, topic, this.Id).ConfigureAwait(false);
    }

    /// <summary>
    /// %%%
    /// </summary>
    /// <typeparam name="TMessage">The message type</typeparam>
    /// <param name="message">The message to publish.</param>
    /// <param name="agentType">%%%</param>
    protected async Task SendMessageAsync<TMessage>(TMessage message, AgentType agentType) where TMessage : class
    {
        AgentId agentId = await this._runtime.GetAgentAsync(agentType).ConfigureAwait(false);
        await this._runtime.SendMessageAsync(message, agentId, this.Id).ConfigureAwait(false);
    }
}
