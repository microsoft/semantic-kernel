// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Hosting;

namespace Microsoft.SemanticKernel.Agents.Runtime;

/// <summary>
/// Defines the runtime environment for agents, managing message sending, subscriptions, agent resolution, and state persistence.
/// </summary>
public interface IAgentRuntime : IHostedService, ISaveState
{
    /// <summary>
    /// Sends a message to an agent and gets a response.
    /// This method should be used to communicate directly with an agent.
    /// </summary>
    /// <param name="message">The message to send.</param>
    /// <param name="recipient">The agent to send the message to.</param>
    /// <param name="sender">The agent sending the message. Should be <c>null</c> if sent from an external source.</param>
    /// <param name="messageId">A unique identifier for the message. If <c>null</c>, a new ID will be generated.</param>
    /// <param name="cancellationToken">A token to cancel the operation if needed.</param>
    /// <returns>A task representing the asynchronous operation, returning the response from the agent.</returns>
    /// <exception cref="CantHandleException">Thrown if the recipient cannot handle the message.</exception>
    /// <exception cref="UndeliverableException">Thrown if the message cannot be delivered.</exception>
    ValueTask<object?> SendMessageAsync(object message, AgentId recipient, AgentId? sender = null, string? messageId = null, CancellationToken cancellationToken = default);

    /// <summary>
    /// Publishes a message to all agents subscribed to the given topic.
    /// No responses are expected from publishing.
    /// </summary>
    /// <param name="message">The message to publish.</param>
    /// <param name="topic">The topic to publish the message to.</param>
    /// <param name="sender">The agent sending the message. Defaults to <c>null</c>.</param>
    /// <param name="messageId">A unique message ID. If <c>null</c>, a new one will be generated.</param>
    /// <param name="cancellationToken">A token to cancel the operation if needed.</param>
    /// <returns>A task representing the asynchronous operation.</returns>
    /// <exception cref="UndeliverableException">Thrown if the message cannot be delivered.</exception>
    ValueTask PublishMessageAsync(object message, TopicId topic, AgentId? sender = null, string? messageId = null, CancellationToken cancellationToken = default);

    /// <summary>
    /// Retrieves an agent by its unique identifier.
    /// </summary>
    /// <param name="agentId">The unique identifier of the agent.</param>
    /// <param name="lazy">If <c>true</c>, the agent is fetched lazily.</param>
    /// <returns>A task representing the asynchronous operation, returning the agent's ID.</returns>
    ValueTask<AgentId> GetAgentAsync(AgentId agentId, bool lazy = true/*, CancellationToken? = default*/);

    /// <summary>
    /// Retrieves an agent by its type.
    /// </summary>
    /// <param name="agentType">The type of the agent.</param>
    /// <param name="key">An optional key to specify variations of the agent. Defaults to "default".</param>
    /// <param name="lazy">If <c>true</c>, the agent is fetched lazily.</param>
    /// <returns>A task representing the asynchronous operation, returning the agent's ID.</returns>
    ValueTask<AgentId> GetAgentAsync(AgentType agentType, string key = "default", bool lazy = true/*, CancellationToken? = default*/);

    /// <summary>
    /// Retrieves an agent by its string representation.
    /// </summary>
    /// <param name="agent">The string representation of the agent.</param>
    /// <param name="key">An optional key to specify variations of the agent. Defaults to "default".</param>
    /// <param name="lazy">If <c>true</c>, the agent is fetched lazily.</param>
    /// <returns>A task representing the asynchronous operation, returning the agent's ID.</returns>
    ValueTask<AgentId> GetAgentAsync(string agent, string key = "default", bool lazy = true/*, CancellationToken? = default*/);

    /// <summary>
    /// Saves the state of an agent.
    /// The result must be JSON serializable.
    /// </summary>
    /// <param name="agentId">The ID of the agent whose state is being saved.</param>
    /// <returns>A task representing the asynchronous operation, returning a dictionary of the saved state.</returns>
    ValueTask<JsonElement> SaveAgentStateAsync(AgentId agentId/*, CancellationToken? cancellationToken = default*/);

    /// <summary>
    /// Loads the saved state into an agent.
    /// </summary>
    /// <param name="agentId">The ID of the agent whose state is being restored.</param>
    /// <param name="state">The state dictionary to restore.</param>
    /// <returns>A task representing the asynchronous operation.</returns>
    ValueTask LoadAgentStateAsync(AgentId agentId, JsonElement state/*, CancellationToken? cancellationToken = default*/);

    /// <summary>
    /// Retrieves metadata for an agent.
    /// </summary>
    /// <param name="agentId">The ID of the agent.</param>
    /// <returns>A task representing the asynchronous operation, returning the agent's metadata.</returns>
    ValueTask<AgentMetadata> GetAgentMetadataAsync(AgentId agentId/*, CancellationToken? cancellationToken = default*/);

    /// <summary>
    /// Adds a new subscription for the runtime to handle when processing published messages.
    /// </summary>
    /// <param name="subscription">The subscription to add.</param>
    /// <returns>A task representing the asynchronous operation.</returns>
    ValueTask AddSubscriptionAsync(ISubscriptionDefinition subscription/*, CancellationToken? cancellationToken = default*/);

    /// <summary>
    /// Removes a subscription from the runtime.
    /// </summary>
    /// <param name="subscriptionId">The unique identifier of the subscription to remove.</param>
    /// <returns>A task representing the asynchronous operation.</returns>
    /// <exception cref="KeyNotFoundException">Thrown if the subscription does not exist.</exception>
    ValueTask RemoveSubscriptionAsync(string subscriptionId/*, CancellationToken? cancellationToken = default*/);

    /// <summary>
    /// Registers an agent factory with the runtime, associating it with a specific agent type.
    /// The type must be unique.
    /// </summary>
    /// <param name="type">The agent type to associate with the factory.</param>
    /// <param name="factoryFunc">A function that asynchronously creates the agent instance.</param>
    /// <returns>A task representing the asynchronous operation, returning the registered <see cref="AgentType"/>.</returns>
    ValueTask<AgentType> RegisterAgentFactoryAsync(AgentType type, Func<AgentId, IAgentRuntime, ValueTask<IHostableAgent>> factoryFunc);

    /// <summary>
    /// Attempts to retrieve an <see cref="AgentProxy"/> for the specified agent.
    /// </summary>
    /// <param name="agentId">The ID of the agent.</param>
    /// <returns>A task representing the asynchronous operation, returning an <see cref="AgentProxy"/> if successful.</returns>
    ValueTask<AgentProxy> TryGetAgentProxyAsync(AgentId agentId);
}
