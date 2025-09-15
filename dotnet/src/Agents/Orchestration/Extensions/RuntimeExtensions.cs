// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Runtime;
using Microsoft.SemanticKernel.Agents.Runtime.Core;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Extensions;

/// <summary>
/// Extension methods for <see cref="IAgentRuntime"/>.
/// </summary>
public static class RuntimeExtensions
{
    /// <summary>
    /// Sends a message to the specified agent.
    /// </summary>
    public static async ValueTask PublishMessageAsync(this IAgentRuntime runtime, object message, AgentType agentType, CancellationToken cancellationToken = default)
    {
        await runtime.PublishMessageAsync(message, new TopicId(agentType), sender: null, messageId: null, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Registers an agent factory for the specified agent type and associates it with the runtime.
    /// </summary>
    /// <param name="runtime">The runtime targeted for registration.</param>
    /// <param name="agentType">The type of agent to register.</param>
    /// <param name="factoryFunc">The factory function for creating the agent.</param>
    /// <returns>The registered agent type.</returns>
    public static async ValueTask<AgentType> RegisterOrchestrationAgentAsync(this IAgentRuntime runtime, AgentType agentType, Func<AgentId, IAgentRuntime, ValueTask<IHostableAgent>> factoryFunc)
    {
        AgentType registeredType = await runtime.RegisterAgentFactoryAsync(agentType, factoryFunc).ConfigureAwait(false);

        // Subscribe agent to its own unique topic
        await runtime.SubscribeAsync(registeredType).ConfigureAwait(false);

        return registeredType;
    }

    /// <summary>
    /// Subscribes the specified agent type to its own dedicated topic.
    /// </summary>
    /// <param name="runtime">The runtime for managing the subscription.</param>
    /// <param name="agentType">The agent type to subscribe.</param>
    public static async Task SubscribeAsync(this IAgentRuntime runtime, string agentType)
    {
        await runtime.AddSubscriptionAsync(new TypeSubscription(agentType, agentType)).ConfigureAwait(false);
    }

    /// <summary>
    /// Subscribes the specified agent type to the provided topics.
    /// </summary>
    /// <param name="runtime">The runtime for managing the subscription.</param>
    /// <param name="agentType">The agent type to subscribe.</param>
    /// <param name="topics">A variable list of topics for subscription.</param>
    public static async Task SubscribeAsync(this IAgentRuntime runtime, string agentType, params TopicId[] topics)
    {
        for (int index = 0; index < topics.Length; ++index)
        {
            await runtime.AddSubscriptionAsync(new TypeSubscription(topics[index].Type, agentType)).ConfigureAwait(false);
        }
    }
}
