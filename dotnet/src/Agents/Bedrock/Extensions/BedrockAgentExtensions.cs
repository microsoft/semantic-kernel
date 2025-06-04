// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockAgent;
using Amazon.BedrockAgent.Model;

namespace Microsoft.SemanticKernel.Agents.Bedrock;

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
        this IAmazonBedrockAgent client,
        CreateAgentRequest request,
        CancellationToken cancellationToken = default)
    {
        var createAgentResponse = await client.CreateAgentAsync(request, cancellationToken).ConfigureAwait(false);
        // The agent will first enter the CREATING status.
        // When the operation finishes, it will enter the NOT_PREPARED status.
        // We need to wait for the agent to reach the NOT_PREPARED status before we can prepare it.
        await client.WaitForAgentStatusAsync(createAgentResponse.Agent, AgentStatus.NOT_PREPARED, cancellationToken: cancellationToken).ConfigureAwait(false);
        return await client.PrepareAgentAndWaitUntilPreparedAsync(createAgentResponse.Agent, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Creates an agent.
    /// </summary>
    /// <param name="client">The <see cref="AmazonBedrockAgentClient"/> instance.</param>
    /// <param name="request">The <see cref="CreateAgentRequest"/> instance.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> instance.</param>
    public static async Task<Amazon.BedrockAgent.Model.Agent> CreateAgentAndWaitAsync(
        this IAmazonBedrockAgent client,
        CreateAgentRequest request,
        CancellationToken cancellationToken = default)
    {
        var createAgentResponse = await client.CreateAgentAsync(request, cancellationToken).ConfigureAwait(false);
        // The agent will first enter the CREATING status.
        // When the operation finishes, it will enter the NOT_PREPARED status.
        // We need to wait for the agent to reach the NOT_PREPARED status before we can prepare it.
        await client.WaitForAgentStatusAsync(createAgentResponse.Agent, AgentStatus.NOT_PREPARED, cancellationToken: cancellationToken).ConfigureAwait(false);
        return createAgentResponse.Agent;
    }

    /// <summary>
    /// Creates an agent.
    /// </summary>
    /// <param name="client">The <see cref="AmazonBedrockAgentClient"/> instance.</param>
    /// <param name="agent">The <see cref="Amazon.BedrockAgent.Model.Agent"/> instance.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> instance.</param>
    public static async Task<Amazon.BedrockAgent.Model.Agent> PrepareAgentAndWaitAsync(
        this IAmazonBedrockAgent client,
        Amazon.BedrockAgent.Model.Agent agent,
        CancellationToken cancellationToken = default)
    {
        return await client.PrepareAgentAndWaitUntilPreparedAsync(agent, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Associates an agent with a knowledge base.
    /// </summary>
    /// <param name="agent">The <see cref="BedrockAgent"/> instance.</param>
    /// <param name="knowledgeBaseId">The knowledge base ID.</param>
    /// <param name="description">The description of the association.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> instance.</param>
    public static async Task AssociateAgentKnowledgeBaseAsync(
        this BedrockAgent agent,
        string knowledgeBaseId,
        string description,
        CancellationToken cancellationToken = default)
    {
        await agent.Client.AssociateAgentKnowledgeBaseAsync(new()
        {
            AgentId = agent.Id,
            AgentVersion = agent.AgentModel.AgentVersion ?? "DRAFT",
            KnowledgeBaseId = knowledgeBaseId,
            Description = description,
        }, cancellationToken).ConfigureAwait(false);

        await agent.Client.PrepareAgentAndWaitUntilPreparedAsync(agent.AgentModel, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Disassociate the agent with a knowledge base.
    /// </summary>
    /// <param name="agent">The <see cref="BedrockAgent"/> instance.</param>
    /// <param name="knowledgeBaseId">The id of the knowledge base to disassociate with the agent.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public static async Task DisassociateAgentKnowledgeBaseAsync(
        this BedrockAgent agent,
        string knowledgeBaseId,
        CancellationToken cancellationToken = default)
    {
        await agent.Client.DisassociateAgentKnowledgeBaseAsync(new()
        {
            AgentId = agent.Id,
            AgentVersion = agent.AgentModel.AgentVersion ?? "DRAFT",
            KnowledgeBaseId = knowledgeBaseId,
        }, cancellationToken).ConfigureAwait(false);

        await agent.Client.PrepareAgentAndWaitUntilPreparedAsync(agent.AgentModel, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// List the knowledge bases associated with the agent.
    /// </summary>
    /// <param name="agent">The <see cref="BedrockAgent"/> instance.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A <see cref="ListAgentKnowledgeBasesResponse"/> containing the knowledge bases associated with the agent.</returns>
    public static async Task<ListAgentKnowledgeBasesResponse> ListAssociatedKnowledgeBasesAsync(
        this BedrockAgent agent,
        CancellationToken cancellationToken = default)
    {
        return await agent.Client.ListAgentKnowledgeBasesAsync(new()
        {
            AgentId = agent.Id,
            AgentVersion = agent.AgentModel.AgentVersion ?? "DRAFT",
        }, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Create a code interpreter action group for the agent and prepare the agent.
    /// </summary>
    /// <param name="agent">The <see cref="BedrockAgent"/> instance.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public static async Task CreateCodeInterpreterActionGroupAsync(
        this BedrockAgent agent,
        CancellationToken cancellationToken = default)
    {
        var createAgentActionGroupRequest = new CreateAgentActionGroupRequest
        {
            AgentId = agent.Id,
            AgentVersion = agent.AgentModel.AgentVersion ?? "DRAFT",
            ActionGroupName = agent.CodeInterpreterActionGroupSignature,
            ActionGroupState = ActionGroupState.ENABLED,
            ParentActionGroupSignature = new(Amazon.BedrockAgent.ActionGroupSignature.AMAZONCodeInterpreter),
        };

        await agent.Client.CreateAgentActionGroupAsync(createAgentActionGroupRequest, cancellationToken).ConfigureAwait(false);
        await agent.Client.PrepareAgentAndWaitUntilPreparedAsync(agent.AgentModel, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Create a kernel function action group for the agent and prepare the agent.
    /// </summary>
    /// <param name="agent">The <see cref="BedrockAgent"/> instance.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public static async Task CreateKernelFunctionActionGroupAsync(
        this BedrockAgent agent,
        CancellationToken cancellationToken = default)
    {
        await agent.CreateKernelFunctionActionGroupAsync(agent.Kernel.ToFunctionSchema(), cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Create a kernel function action group for the agent and prepare the agent.
    /// </summary>
    /// <param name="agent">The <see cref="BedrockAgent"/> instance.</param>
    /// <param name="functionSchema">The details of the function schema for the action group.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public static async Task CreateKernelFunctionActionGroupAsync(
        this BedrockAgent agent,
        FunctionSchema functionSchema,
        CancellationToken cancellationToken = default)
    {
        var createAgentActionGroupRequest = new CreateAgentActionGroupRequest
        {
            AgentId = agent.Id,
            AgentVersion = agent.AgentModel.AgentVersion ?? "DRAFT",
            ActionGroupName = agent.KernelFunctionActionGroupSignature,
            ActionGroupState = ActionGroupState.ENABLED,
            ActionGroupExecutor = new()
            {
                CustomControl = Amazon.BedrockAgent.CustomControlMethod.RETURN_CONTROL,
            },
            FunctionSchema = functionSchema,
        };

        await agent.Client.CreateAgentActionGroupAsync(createAgentActionGroupRequest, cancellationToken).ConfigureAwait(false);
        await agent.Client.PrepareAgentAndWaitUntilPreparedAsync(agent.AgentModel, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Enable user input for the agent and prepare the agent.
    /// </summary>
    /// <param name="agent">The <see cref="BedrockAgent"/> instance.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public static async Task EnableUserInputActionGroupAsync(
        this BedrockAgent agent,
        CancellationToken cancellationToken = default)
    {
        var createAgentActionGroupRequest = new CreateAgentActionGroupRequest
        {
            AgentId = agent.Id,
            AgentVersion = agent.AgentModel.AgentVersion ?? "DRAFT",
            ActionGroupName = agent.UseInputActionGroupSignature,
            ActionGroupState = ActionGroupState.ENABLED,
            ParentActionGroupSignature = new(Amazon.BedrockAgent.ActionGroupSignature.AMAZONUserInput),
        };

        await agent.Client.CreateAgentActionGroupAsync(createAgentActionGroupRequest, cancellationToken).ConfigureAwait(false);
        await agent.Client.PrepareAgentAndWaitUntilPreparedAsync(agent.AgentModel, cancellationToken).ConfigureAwait(false);
    }

    private static async Task<Amazon.BedrockAgent.Model.Agent> PrepareAgentAndWaitUntilPreparedAsync(
        this IAmazonBedrockAgent client,
        Amazon.BedrockAgent.Model.Agent agent,
        CancellationToken cancellationToken = default)
    {
        var prepareAgentResponse = await client.PrepareAgentAsync(new() { AgentId = agent.AgentId }, cancellationToken).ConfigureAwait(false);

        // The agent will take some time to enter the PREPARING status after the prepare operation is called.
        // We need to wait for the agent to reach the PREPARING status before we can proceed, otherwise we
        // will return immediately if the agent is already in PREPARED status.
        await client.WaitForAgentStatusAsync(agent, AgentStatus.PREPARING, cancellationToken: cancellationToken).ConfigureAwait(false);
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
        this IAmazonBedrockAgent client,
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
