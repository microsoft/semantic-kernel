// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockAgent;
using Amazon.BedrockAgent.Model;
using Amazon.BedrockAgentRuntime;
using Amazon.BedrockAgentRuntime.Model;
using Microsoft.SemanticKernel.Agents.Bedrock.Extensions;
using Microsoft.SemanticKernel.Agents.Extensions;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Agents.Bedrock;

/// <summary>
/// Provides a specialized <see cref="KernelAgent"/> for the Bedrock Agent service.
/// </summary>
public class BedrockAgent : KernelAgent
{
    private readonly AmazonBedrockAgentClient _client;

    private readonly AmazonBedrockAgentRuntimeClient _runtimeClient;

    private readonly Amazon.BedrockAgent.Model.Agent _agentModel;

    /// <summary>
    /// There is a default alias created by Bedrock for the working draft version of the agent.
    /// https://docs.aws.amazon.com/bedrock/latest/userguide/agents-deploy.html
    /// </summary>
    public static readonly string WorkingDraftAgentAlias = "TSTALIASID";

    /// <summary>
    /// Initializes a new instance of the <see cref="BedrockAgent"/> class.
    /// </summary>
    /// <param name="agentModel">The agent model of an agent that exists on the Bedrock Agent service.</param>
    /// <param name="client">A client used to interact with the Bedrock Agent service.</param>
    /// <param name="runtimeClient">A client used to interact with the Bedrock Agent runtime service.</param>
    public BedrockAgent(
        Amazon.BedrockAgent.Model.Agent agentModel,
        AmazonBedrockAgentClient client,
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

    #region static methods

    /// <summary>
    /// Create a Bedrock agent on the service.
    /// </summary>
    /// <param name="request">The request to create the agent.</param>
    /// <param name="enableCodeInterpreter">Whether to enable the code interpreter for the agent.</param>
    /// <param name="enableKernelFunctions">Whether to enable kernel functions for the agent.</param>
    /// <param name="enableUserInput">Whether to enable user input for the agent.</param>
    /// <param name="client">The client to use.</param>
    /// <param name="runtimeClient">The runtime client to use.</param>
    /// <param name="kernel">A kernel instance for the agent to use.</param>
    /// <param name="defaultArguments">Optional default arguments.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An instance of the <see cref="BedrockAgent"/>.</returns>
    public static async Task<BedrockAgent> CreateAsync(
        CreateAgentRequest request,
        bool enableCodeInterpreter = false,
        bool enableKernelFunctions = false,
        bool enableUserInput = false,
        AmazonBedrockAgentClient? client = null,
        AmazonBedrockAgentRuntimeClient? runtimeClient = null,
        Kernel? kernel = null,
        KernelArguments? defaultArguments = null,
        CancellationToken cancellationToken = default)
    {
        client ??= new AmazonBedrockAgentClient();
        runtimeClient ??= new AmazonBedrockAgentRuntimeClient();
        var createAgentResponse = await client.CreateAgentAsync(request, cancellationToken).ConfigureAwait(false);

        BedrockAgent agent = new(createAgentResponse.Agent, client, runtimeClient)
        {
            Kernel = kernel ?? new(),
            Arguments = defaultArguments ?? [],
        };

        // The agent will first enter the CREATING status.
        // When the agent is created, it will enter the NOT_PREPARED status.
        await agent.WaitForAgentStatusAsync(AgentStatus.NOT_PREPARED, cancellationToken).ConfigureAwait(false);

        if (enableCodeInterpreter)
        {
            await agent.CreateCodeInterpreterActionGroupAsync(cancellationToken).ConfigureAwait(false);
        }
        if (enableKernelFunctions)
        {
            await agent.CreateKernelFunctionActionGroupAsync(cancellationToken).ConfigureAwait(false);
        }
        if (enableUserInput)
        {
            await agent.EnableUserInputActionGroupAsync(cancellationToken).ConfigureAwait(false);
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
        AmazonBedrockAgentClient? client = null,
        AmazonBedrockAgentRuntimeClient? runtimeClient = null,
        Kernel? kernel = null,
        KernelArguments? defaultArguments = null,
        CancellationToken cancellationToken = default)
    {
        client ??= new AmazonBedrockAgentClient();
        runtimeClient ??= new AmazonBedrockAgentRuntimeClient();
        var getAgentResponse = await client.GetAgentAsync(new() { AgentId = id }, cancellationToken).ConfigureAwait(false);

        return new(getAgentResponse.Agent, client, runtimeClient)
        {
            Kernel = kernel ?? new(),
            Arguments = defaultArguments ?? [],
        };
    }

    /// <summary>
    /// Convenient method to create an unique session id.
    /// </summary>
    public static string CreateSessionId()
    {
        return Guid.NewGuid().ToString();
    }

    #endregion

    # region public methods

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
        await this.WaitForAgentStatusAsync(AgentStatus.PREPARED, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Invoke the Bedrock agent with the given message.
    /// </summary>
    /// <param name="sessionId">The session id.</param>
    /// <param name="message">The message to send to the agent.</param>
    /// <param name="arguments">The arguments to use when invoking the agent.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <param name="agentAliasId">The alias id of the agent to use. The default is the working draft alias id.</param>
    /// <returns>An <see cref="IAsyncEnumerable{T}"/> of <see cref="ChatMessageContent"/>.</returns>
    public IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        string sessionId,
        string message,
        KernelArguments? arguments,
        CancellationToken cancellationToken,
        string? agentAliasId = null)
    {
        var invokeAgentRequest = new InvokeAgentRequest
        {
            AgentAliasId = agentAliasId ?? WorkingDraftAgentAlias,
            AgentId = this.Id,
            SessionId = sessionId,
            InputText = message,
        };

        return this.InvokeAsync(invokeAgentRequest, arguments, cancellationToken);
    }

    /// <summary>
    /// Invoke the Bedrock agent with the given request. Use this method when you want to customize the request.
    /// </summary>
    /// <param name="invokeAgentRequest">The request to send to the agent.</param>
    /// <param name="arguments">The arguments to use when invoking the agent.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        InvokeAgentRequest invokeAgentRequest,
        KernelArguments? arguments,
        CancellationToken cancellationToken)
    {
        return invokeAgentRequest.StreamingConfigurations != null && invokeAgentRequest.StreamingConfigurations.StreamFinalResponse
            ? throw new ArgumentException("The streaming configuration must be null for non-streaming responses.")
            : InvokeInternal();

        // Collect all responses from the agent and return them as a single chat message content since this
        // is a non-streaming API.
        // The Bedrock Agent API streams beck different types of responses, i.e. text, files, metadata, etc.
        // The Bedrock Agent API also won't stream back any content when it needs to call a function. It will
        // only start streaming back content after the function has been called and the response is ready.
        async IAsyncEnumerable<ChatMessageContent> InvokeInternal()
        {
            ChatMessageContentItemCollection items = [];
            string content = "";
            Dictionary<string, object?> metadata = [];
            List<object?> innerContents = [];

            await foreach (var message in ActivityExtensions.RunWithActivityAsync(
                () => ModelDiagnostics.StartAgentInvocationActivity(this.Id, this.GetDisplayName(), this.Description),
                () => this.InternalInvokeAsync(invokeAgentRequest, arguments, cancellationToken),
                cancellationToken).ConfigureAwait(false))
            {
                items.AddRange(message.Items);
                content += message.Content ?? "";
                if (message.Metadata != null)
                {
                    foreach (var key in message.Metadata.Keys)
                    {
                        metadata[key] = message.Metadata[key];
                    }
                }
                innerContents.Add(message.InnerContent);
            }

            yield return content.Length == 0
                ? throw new KernelException("No content was returned from the agent.")
                : new ChatMessageContent(AuthorRole.Assistant, content)
                {
                    AuthorName = this.GetDisplayName(),
                    Items = items,
                    ModelId = this._agentModel.FoundationModel,
                    Metadata = metadata,
                    InnerContent = innerContents,
                };
        }
    }

    /// <summary>
    /// Invoke the Bedrock agent with the given request and streaming response.
    /// </summary>
    /// <param name="sessionId">The session id.</param>
    /// <param name="message">The message to send to the agent.</param>    /// <param name="arguments">The arguments to use when invoking the agent.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <param name="agentAliasId">The alias id of the agent to use. The default is the working draft alias id.</param>
    /// <returns>An <see cref="IAsyncEnumerable{T}"/> of <see cref="ChatMessageContent"/>.</returns>
    public IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(
        string sessionId,
        string message,
        KernelArguments? arguments,
        CancellationToken cancellationToken,
        string? agentAliasId = null)
    {
        var invokeAgentRequest = new InvokeAgentRequest
        {
            AgentAliasId = agentAliasId ?? WorkingDraftAgentAlias,
            AgentId = this.Id,
            SessionId = sessionId,
            InputText = message,
            StreamingConfigurations = new()
            {
                StreamFinalResponse = true,
            },
        };

        return this.InvokeStreamingAsync(invokeAgentRequest, arguments, cancellationToken);
    }

    /// <summary>
    /// Invoke the Bedrock agent with the given request and streaming response. Use this method when you want to customize the request.
    /// </summary>
    /// <param name="invokeAgentRequest">The request to send to the agent.</param>
    /// <param name="arguments">The arguments to use when invoking the agent.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="IAsyncEnumerable{T}"/> of <see cref="StreamingChatMessageContent"/>.</returns>
    public async IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(
        InvokeAgentRequest invokeAgentRequest,
        KernelArguments? arguments,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (invokeAgentRequest.StreamingConfigurations == null)
        {
            invokeAgentRequest.StreamingConfigurations = new()
            {
                StreamFinalResponse = true,
            };
        }
        else if (!invokeAgentRequest.StreamingConfigurations.StreamFinalResponse)
        {
            throw new ArgumentException("The streaming configuration must have StreamFinalResponse set to true.");
        }

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
    /// Associate the agent with a knowledge base.
    /// </summary>
    /// <param name="knowledgeBaseId">The id of the knowledge base to associate with the agent.</param>
    /// <param name="description">A description of what the agent should use the knowledge base for.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public async Task AssociateAgentKnowledgeBaseAsync(string knowledgeBaseId, string description, CancellationToken cancellationToken)
    {
        await this._client.AssociateAgentKnowledgeBaseAsync(new()
        {
            AgentId = this.Id,
            AgentVersion = this._agentModel.AgentVersion ?? "DRAFT",
            KnowledgeBaseId = knowledgeBaseId,
            Description = description,
        }, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Disassociate the agent with a knowledge base.
    /// </summary>
    /// <param name="knowledgeBaseId">The id of the knowledge base to disassociate with the agent.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public async Task DisassociateAgentKnowledgeBaseAsync(string knowledgeBaseId, CancellationToken cancellationToken)
    {
        await this._client.DisassociateAgentKnowledgeBaseAsync(new()
        {
            AgentId = this.Id,
            AgentVersion = this._agentModel.AgentVersion ?? "DRAFT",
            KnowledgeBaseId = knowledgeBaseId,
        }, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// List the knowledge bases associated with the agent.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A <see cref="ListAgentKnowledgeBasesResponse"/> containing the knowledge bases associated with the agent.</returns>
    public async Task<ListAgentKnowledgeBasesResponse> ListAssociatedKnowledgeBasesAsync(CancellationToken cancellationToken)
    {
        return await this._client.ListAgentKnowledgeBasesAsync(new()
        {
            AgentId = this.Id,
            AgentVersion = this._agentModel.AgentVersion ?? "DRAFT",
        }, cancellationToken).ConfigureAwait(false);
    }

    #endregion

    #region private methods

    /// <summary>
    /// Create a code interpreter action group for the agent.
    /// </summary>
    private async Task CreateCodeInterpreterActionGroupAsync(CancellationToken cancellationToken)
    {
        var createAgentActionGroupRequest = new CreateAgentActionGroupRequest
        {
            AgentId = this.Id,
            AgentVersion = this._agentModel.AgentVersion ?? "DRAFT",
            ActionGroupName = this.GetCodeInterpreterActionGroupSignature(),
            ActionGroupState = ActionGroupState.ENABLED,
            ParentActionGroupSignature = new(Amazon.BedrockAgent.ActionGroupSignature.AMAZONCodeInterpreter),
        };

        await this._client.CreateAgentActionGroupAsync(createAgentActionGroupRequest, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Create a kernel function action group for the agent.
    /// </summary>
    private async Task CreateKernelFunctionActionGroupAsync(CancellationToken cancellationToken)
    {
        var createAgentActionGroupRequest = new CreateAgentActionGroupRequest
        {
            AgentId = this.Id,
            AgentVersion = this._agentModel.AgentVersion ?? "DRAFT",
            ActionGroupName = this.GetKernelFunctionActionGroupSignature(),
            ActionGroupState = ActionGroupState.ENABLED,
            ActionGroupExecutor = new()
            {
                CustomControl = Amazon.BedrockAgent.CustomControlMethod.RETURN_CONTROL,
            },
            FunctionSchema = this.Kernel.ToFunctionSchema(),
        };

        await this._client.CreateAgentActionGroupAsync(createAgentActionGroupRequest, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Enable user input for the agent.
    /// </summary>
    private async Task EnableUserInputActionGroupAsync(CancellationToken cancellationToken)
    {
        var createAgentActionGroupRequest = new CreateAgentActionGroupRequest
        {
            AgentId = this.Id,
            AgentVersion = this._agentModel.AgentVersion ?? "DRAFT",
            ActionGroupName = this.GetUseInputActionGroupSignature(),
            ActionGroupState = ActionGroupState.ENABLED,
            ParentActionGroupSignature = new(Amazon.BedrockAgent.ActionGroupSignature.AMAZONUserInput),
        };

        await this._client.CreateAgentActionGroupAsync(createAgentActionGroupRequest, cancellationToken).ConfigureAwait(false);
    }

    #endregion

    /// <inheritdoc/>
    protected override IEnumerable<string> GetChannelKeys()
    {
        // Return the channel keys for the BedrockAgent
        yield return typeof(BedrockAgentChannel).FullName!;
    }

    /// <inheritdoc/>
    protected override Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
    {
        // Create and return a new BedrockAgentChannel
        return Task.FromResult<AgentChannel>(new BedrockAgentChannel());
    }

    /// <inheritdoc/>
    protected override Task<AgentChannel> RestoreChannelAsync(string channelState, CancellationToken cancellationToken)
    {
        // Restore and return a BedrockAgentChannel from the given state
        return Task.FromResult<AgentChannel>(new BedrockAgentChannel());
    }

    #region internal methods

    internal AmazonBedrockAgentClient GetClient() => this._client;
    internal AmazonBedrockAgentRuntimeClient GetRuntimeClient() => this._runtimeClient;
    internal Amazon.BedrockAgent.Model.Agent GetAgentModel() => this._agentModel;
    internal string GetCodeInterpreterActionGroupSignature() => $"{this.GetDisplayName()}_CodeInterpreter";
    internal string GetKernelFunctionActionGroupSignature() => $"{this.GetDisplayName()}_KernelFunctions";
    internal string GetUseInputActionGroupSignature() => $"{this.GetDisplayName()}_UserInput";

    #endregion
}
