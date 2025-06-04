// Copyright (c) Microsoft. All rights reserved.

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
    public static async ValueTask SendMessageAsync(this IAgentRuntime runtime, object message, AgentType agentType, CancellationToken cancellationToken = default)
    {
        AgentId? agentId = await runtime.GetAgentAsync(agentType, lazy: false).ConfigureAwait(false);
        if (agentId.HasValue)
        {
            await runtime.SendMessageAsync(message, agentId.Value, sender: null, messageId: null, cancellationToken).ConfigureAwait(false);
        }
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
