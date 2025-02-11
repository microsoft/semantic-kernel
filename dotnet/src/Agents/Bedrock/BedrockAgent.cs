// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using AmazonBedrockAgent = Amazon.BedrockAgent;
using Amazon.BedrockAgentRuntime;
using AmazonBedrockAgentModel = Amazon.BedrockAgent.Model;
using AmazonBedrockAgentRuntimeModel = Amazon.BedrockAgentRuntime.Model;
using Microsoft.SemanticKernel.Agents.Extensions;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Agents.Bedrock.Extensions;

namespace Microsoft.SemanticKernel.Agents.Bedrock;

/// <summary>
/// Provides a specialized <see cref="KernelAgent"/> for the Bedrock Agent service.
/// </summary>
public class BedrockAgent : KernelAgent
{
    private readonly AmazonBedrockAgent.AmazonBedrockAgentClient _client;

    private readonly AmazonBedrockAgentRuntimeClient _runtimeClient;

    private readonly AmazonBedrockAgentModel.Agent _agentModel;

    // There is a default alias created by Bedrock for the working draft version of the agent.
    // https://docs.aws.amazon.com/bedrock/latest/userguide/agents-deploy.html
    private const string WORKING_DRAFT_AGENT_ALIAS = "TSTALIASID";

    /// <summary>
    /// Initializes a new instance of the <see cref="BedrockAgent"/> class.
    /// </summary>
    /// <param name="agentModel">The agent model of an agent that exists on the Bedrock Agent service.</param>
    /// <param name="client">A client used to interact with the Bedrock Agent service.</param>
    /// <param name="runtimeClient">A client used to interact with the Bedrock Agent runtime service.</param>
    public BedrockAgent(
        AmazonBedrockAgentModel.Agent agentModel,
        AmazonBedrockAgent.AmazonBedrockAgentClient client,
        AmazonBedrockAgentRuntimeClient runtimeClient)
    {
        this._agentModel = agentModel;
        this._client = client;
        this._runtimeClient = runtimeClient;

        this.Id = agentModel.AgentId;
        this.Name = agentModel.AgentName;
        this.Description = agentModel.Description;
        this.Instructions = agentModel.Instruction;
    }

    /// <summary>
    /// Create a Bedrock agent on the service.
    /// </summary>
    /// <param name="request">The request to create the agent.</param>
    /// <param name="enableCodeInterpreter">Whether to enable the code interpreter for the agent.</param>
    /// <param name="enableKernelFunctions">Whether to enable kernel functions for the agent.</param>
    /// <param name="client">The client to use.</param>
    /// <param name="runtimeClient">The runtime client to use.</param>
    /// <param name="kernel">A kernel instance for the agent to use.</param>
    /// <param name="defaultArguments">Optional default arguments.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An instance of the <see cref="BedrockAgent"/>.</returns>
    public static async Task<BedrockAgent> CreateAsync(
        AmazonBedrockAgentModel.CreateAgentRequest request,
        bool enableCodeInterpreter = false,
        bool enableKernelFunctions = false,
        AmazonBedrockAgent.AmazonBedrockAgentClient? client = null,
        AmazonBedrockAgentRuntimeClient? runtimeClient = null,
        Kernel? kernel = null,
        KernelArguments? defaultArguments = null,
        CancellationToken cancellationToken = default)
    {
        client ??= new AmazonBedrockAgent.AmazonBedrockAgentClient();
        runtimeClient ??= new AmazonBedrockAgentRuntimeClient();
        var createAgentResponse = await client.CreateAgentAsync(request, cancellationToken).ConfigureAwait(false);

        BedrockAgent agent = new(createAgentResponse.Agent, client, runtimeClient)
        {
            Kernel = kernel ?? new(),
            Arguments = defaultArguments,
        };

        // The agent will first enter the CREATING status.
        // When the agent is created, it will enter the NOT_PREPARED status.
        await agent.WaitForAgentStatusAsync(AmazonBedrockAgent.AgentStatus.NOT_PREPARED, cancellationToken).ConfigureAwait(false);

        if (enableCodeInterpreter)
        {
            await agent.CreateCodeInterpreterActionGroupAsync(cancellationToken).ConfigureAwait(false);
        }
        if (enableKernelFunctions)
        {
            await agent.CreateKernelFunctionActionGroupAsync(cancellationToken).ConfigureAwait(false);
        }

        // Need to prepare the agent before it can be invoked.
        await agent.PrepareAsync(cancellationToken).ConfigureAwait(false);

        return agent;
    }

    /// <summary>
    /// Retrieve a Bedrock agent from the service by id.
    /// </summary>
    /// <param name="id">The id of the agent that exists on the Bedrock Agent service.</param>
    /// <param name="client">The client to use.</param>
    /// <param name="runtimeClient">The runtime client to use.</param>
    /// <param name="kernel">A kernel instance for the agent to use.</param>
    /// <param name="defaultArguments">Optional default arguments.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An instance of the <see cref="BedrockAgent"/>.</returns>
    public static async Task<BedrockAgent> RetrieveAsync(
        string id,
        AmazonBedrockAgent.AmazonBedrockAgentClient? client = null,
        AmazonBedrockAgentRuntimeClient? runtimeClient = null,
        Kernel? kernel = null,
        KernelArguments? defaultArguments = null,
        CancellationToken cancellationToken = default)
    {
        client ??= new AmazonBedrockAgent.AmazonBedrockAgentClient();
        runtimeClient ??= new AmazonBedrockAgentRuntimeClient();
        var getAgentResponse = await client.GetAgentAsync(new() { AgentId = id }, cancellationToken).ConfigureAwait(false);

        return new(getAgentResponse.Agent, client, runtimeClient)
        {
            Kernel = kernel ?? new(),
            Arguments = defaultArguments,
        };
    }

    /// <summary>
    /// Convenient method to create an unique session id.
    /// </summary>
    public static string CreateSessionId()
    {
        return Guid.NewGuid().ToString();
    }

    /// <summary>
    /// Delete the Bedrock agent from the service.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public async Task DeleteAsync(CancellationToken cancellationToken)
    {
        await this._client.DeleteAgentAsync(new() { AgentId = this.Id }, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Prepare the Bedrock agent for use.
    /// </summary>
    public async Task PrepareAsync(CancellationToken cancellationToken)
    {
        await this._client.PrepareAgentAsync(new() { AgentId = this.Id }, cancellationToken).ConfigureAwait(false);
        await this.WaitForAgentStatusAsync(AmazonBedrockAgent.AgentStatus.PREPARED, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Invoke the Bedrock agent with the given message.
    /// </summary>
    /// <param name="sessionId">The session id.</param>
    /// <param name="message">The message to send to the agent.</param>
    /// <param name="arguments">The arguments to use when invoking the agent.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="IAsyncEnumerable{T}"/> of <see cref="ChatMessageContent"/>.</returns>
    public IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        string sessionId,
        string message,
        KernelArguments? arguments,
        CancellationToken cancellationToken)
    {
        var invokeAgentRequest = new AmazonBedrockAgentRuntimeModel.InvokeAgentRequest
        {
            AgentAliasId = WORKING_DRAFT_AGENT_ALIAS,
            AgentId = this.Id,
            SessionId = sessionId,
            InputText = message,
        };

        return ActivityExtensions.RunWithActivityAsync(
            () => ModelDiagnostics.StartAgentInvocationActivity(this.Id, this.GetDisplayName(), this.Description),
            () => this.InternalInvokeAsync(invokeAgentRequest, arguments, cancellationToken),
            cancellationToken);
    }

    /// <summary>
    /// Invoke the Bedrock agent with the given request and streaming response.
    /// </summary>
    /// <param name="sessionId">The session id.</param>
    /// <param name="message">The message to send to the agent.</param>    /// <param name="arguments">The arguments to use when invoking the agent.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="IAsyncEnumerable{T}"/> of <see cref="ChatMessageContent"/>.</returns>
    public async IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(
        string sessionId,
        string message,
        KernelArguments? arguments,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        var invokeAgentRequest = new AmazonBedrockAgentRuntimeModel.InvokeAgentRequest
        {
            AgentAliasId = WORKING_DRAFT_AGENT_ALIAS,
            AgentId = this.Id,
            SessionId = sessionId,
            InputText = message,
            StreamingConfigurations = new()
            {
                StreamFinalResponse = true,
            },
        };

        // The Bedrock agent service has the same API for both streaming and non-streaming responses.
        // We are invoking the same method as the non-streaming response with the streaming configuration set,
        // and converting the chat message content to streaming chat message content.
        await foreach (var chatMessageContent in ActivityExtensions.RunWithActivityAsync(
            () => ModelDiagnostics.StartAgentInvocationActivity(this.Id, this.GetDisplayName(), this.Description),
            () => this.InternalInvokeAsync(invokeAgentRequest, arguments, cancellationToken),
            cancellationToken).ConfigureAwait(false))
        {
            yield return new StreamingChatMessageContent(chatMessageContent.Role, chatMessageContent.Content)
            {
                AuthorName = chatMessageContent.AuthorName,
                ModelId = chatMessageContent.ModelId,
                InnerContent = chatMessageContent.InnerContent,
                Metadata = chatMessageContent.Metadata,
            };
        }
    }

    /// <summary>
    /// Create a code interpreter action group for the agent.
    /// </summary>
    private async Task CreateCodeInterpreterActionGroupAsync(CancellationToken cancellationToken)
    {
        var createAgentActionGroupRequest = new AmazonBedrockAgentModel.CreateAgentActionGroupRequest
        {
            AgentId = this.Id,
            AgentVersion = this._agentModel.AgentVersion ?? "DRAFT",
            ActionGroupName = this.GetCodeInterpreterActionGroupSignature(),
            ActionGroupState = AmazonBedrockAgent.ActionGroupState.ENABLED,
            ParentActionGroupSignature = new(AmazonBedrockAgent.ActionGroupSignature.AMAZONCodeInterpreter),
        };

        await this._client.CreateAgentActionGroupAsync(createAgentActionGroupRequest, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Create a kernel function action group for the agent.
    /// </summary>
    private async Task CreateKernelFunctionActionGroupAsync(CancellationToken cancellationToken)
    {
        var createAgentActionGroupRequest = new AmazonBedrockAgentModel.CreateAgentActionGroupRequest
        {
            AgentId = this.Id,
            AgentVersion = this._agentModel.AgentVersion ?? "DRAFT",
            ActionGroupName = this.GetKernelFunctionActionGroupSignature(),
            ActionGroupState = AmazonBedrockAgent.ActionGroupState.ENABLED,
            ActionGroupExecutor = new()
            {
                CustomControl = AmazonBedrockAgent.CustomControlMethod.RETURN_CONTROL,
            },
            FunctionSchema = this.Kernel.ToFunctionSchema(),
        };

        await this._client.CreateAgentActionGroupAsync(createAgentActionGroupRequest, cancellationToken).ConfigureAwait(false);
    }

    protected override IEnumerable<string> GetChannelKeys()
    {
        // Return the channel keys for the BedrockAgent
        yield return typeof(BedrockAgentChannel).FullName!;
    }

    protected override Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
    {
        // Create and return a new BedrockAgentChannel
        return Task.FromResult<AgentChannel>(new BedrockAgentChannel());
    }

    protected override Task<AgentChannel> RestoreChannelAsync(string channelState, CancellationToken cancellationToken)
    {
        // Restore and return a BedrockAgentChannel from the given state
        return Task.FromResult<AgentChannel>(new BedrockAgentChannel());
    }

    internal AmazonBedrockAgent.AmazonBedrockAgentClient GetClient() => this._client;
    internal AmazonBedrockAgentRuntimeClient GetRuntimeClient() => this._runtimeClient;
    internal AmazonBedrockAgentModel.Agent GetAgentModel() => this._agentModel;

    internal string GetCodeInterpreterActionGroupSignature() => $"{this.GetDisplayName()}_CodeInterpreter";
    internal string GetKernelFunctionActionGroupSignature() => $"{this.GetDisplayName()}_KernelFunctions";
}
