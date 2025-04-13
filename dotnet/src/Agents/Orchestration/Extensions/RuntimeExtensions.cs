// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Extensions;

/// <summary>
/// Extension methods for <see cref="IAgentRuntime"/>.
/// </summary>
internal static class RuntimeExtensions
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
}
