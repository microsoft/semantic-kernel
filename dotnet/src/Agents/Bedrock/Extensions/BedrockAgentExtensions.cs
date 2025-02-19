// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockAgent;
using Amazon.BedrockAgent.Model;

namespace Microsoft.SemanticKernel.Agents.Bedrock.Extensions;

/// <summary>
/// Extensions associated with <see cref="AmazonBedrockAgentClient"/>
/// </summary>
public static class BedrockAgentExtensions
{
    /// <summary>
    /// Creates an agent.
    /// </summary>
    /// <param name="client">The <see cref="AmazonBedrockAgentClient"/> instance.</param>
    /// <param name="request">The <see cref="CreateAgentRequest"/> instance.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> instance.</param>
    public static async Task<Amazon.BedrockAgent.Model.Agent> CreateAndPrepareAgentAsync(
        this AmazonBedrockAgentClient client,
        CreateAgentRequest request,
        CancellationToken cancellationToken = default)
    {
        var createAgentResponse = await client.CreateAgentAsync(request, cancellationToken).ConfigureAwait(false);
        // The agent will first enter the CREATING status.
        // When the operation finishes, it will enter the NOT_PREPARED status.
        // We need to wait for the agent to reach the NOT_PREPARED status before we can prepare it.
        await client.WaitForAgentStatusAsync(createAgentResponse.Agent, AgentStatus.NOT_PREPARED, cancellationToken: cancellationToken).ConfigureAwait(false);
        return await client.PrepareAgentAsync(createAgentResponse.Agent, cancellationToken).ConfigureAwait(false);
    }

    private static async Task<Amazon.BedrockAgent.Model.Agent> PrepareAgentAsync(
        this AmazonBedrockAgentClient client,
        Amazon.BedrockAgent.Model.Agent agent,
        CancellationToken cancellationToken = default)
    {
        var prepareAgentResponse = await client.PrepareAgentAsync(new() { AgentId = agent.AgentId }, cancellationToken).ConfigureAwait(false);

        // The agent will enter the PREPARING status.
        // When the agent is prepared, it will enter the PREPARED status.
        return await client.WaitForAgentStatusAsync(agent, AgentStatus.PREPARED, cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Wait for the agent to reach the specified status.
    /// </summary>
    /// <param name="client">The <see cref="AmazonBedrockAgentClient"/> instance.</param>
    /// <param name="agent">The <see cref="BedrockAgent"/> to monitor.</param>
    /// <param name="status">The status to wait for.</param>
    /// <param name="interval">The interval in seconds to wait between attempts. The default is 2 seconds.</param>
    /// <param name="maxAttempts">The maximum number of attempts to make. The default is 5 attempts.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests.</param>
    /// <returns>The <see cref="Amazon.BedrockAgent.Model.Agent"/> instance.</returns>
    private static async Task<Amazon.BedrockAgent.Model.Agent> WaitForAgentStatusAsync(
        this AmazonBedrockAgentClient client,
        Amazon.BedrockAgent.Model.Agent agent,
        AgentStatus status,
        int interval = 2,
        int maxAttempts = 5,
        CancellationToken cancellationToken = default)
    {
        for (var i = 0; i < maxAttempts; i++)
        {
            var getAgentResponse = await client.GetAgentAsync(new() { AgentId = agent.AgentId }, cancellationToken).ConfigureAwait(false);

            if (getAgentResponse.Agent.AgentStatus == status)
            {
                return getAgentResponse.Agent;
            }

            await Task.Delay(interval * 1000, cancellationToken).ConfigureAwait(false);
        }

        throw new TimeoutException($"Agent did not reach status {status} within the specified time.");
    }
}
