// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using AmazonBedrockAgent = Amazon.BedrockAgent;


namespace Microsoft.SemanticKernel.Agents.Bedrock.Extensions;

/// <summary>
/// Extensions associated with the status of a <see cref="BedrockAgent"/>.
/// </summary>
internal static class BedrockAgentStatusExtensions
{
    /// <summary>
    /// Wait for the agent to reach the specified status.
    /// </summary>
    /// <param name="agent">The <see cref="BedrockAgent"/> to monitor.</param>
    /// <param name="status">The status to wait for.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests.</param>
    /// <param name="interval">The interval in seconds to wait between attempts. The default is 2 seconds.</param>
    /// <param name="maxAttempts">The maximum number of attempts to make. The default is 5 attempts.</param>
    public static async Task WaitForAgentStatusAsync(
        this BedrockAgent agent,
        AmazonBedrockAgent.AgentStatus status,
        CancellationToken cancellationToken,
        int interval = 2,
        int maxAttempts = 5)
    {
        for (var i = 0; i < maxAttempts; i++)
        {
            var getAgentResponse = await agent.GetClient().GetAgentAsync(new() { AgentId = agent.Id }, cancellationToken).ConfigureAwait(false);

            if (getAgentResponse.Agent.AgentStatus == status)
            {
                return;
            }

            await Task.Delay(interval * 1000, cancellationToken).ConfigureAwait(false);
        }

        throw new TimeoutException($"Agent did not reach status {status} within the specified time.");
    }
}