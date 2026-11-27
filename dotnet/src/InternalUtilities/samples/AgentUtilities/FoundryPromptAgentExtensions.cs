// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.CompilerServices;
using Azure.AI.Projects;
using Azure.AI.Projects.Agents;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using OpenAI.Responses;

/// <summary>
/// Extensions that let a Semantic Kernel <see cref="Microsoft.SemanticKernel.Agents.ChatCompletionAgent"/> use a Microsoft Foundry Prompt Agent.
/// </summary>
/// <remarks>
/// A Foundry Prompt Agent is a versioned agent definition (model, instructions, and tools) stored in a Foundry project.
/// It replaces the OpenAI Assistants API, which OpenAI shut down on August 26, 2026.
/// </remarks>
public static class FoundryPromptAgentExtensions
{
    /// <summary>
    /// Creates a Prompt Agent version with a unique name that starts with <paramref name="name"/>.
    /// </summary>
    /// <param name="projectClient">The Foundry project client.</param>
    /// <param name="name">The name prefix of the Prompt Agent.</param>
    /// <param name="definition">The definition (model, instructions, and tools) of the Prompt Agent.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests.</param>
    public static async Task<ProjectsAgentVersion> CreatePromptAgentAsync(
        this AIProjectClient projectClient,
        string name,
        DeclarativeAgentDefinition definition,
        CancellationToken cancellationToken = default)
    {
        // Prompt Agent names are unique within a project. Creating an agent with an existing name adds a new version to it,
        // so the suffix keeps repeated or parallel sample runs from changing each other's agent.
        string agentName = $"{name}-{Guid.NewGuid():N}";

        return await projectClient.AgentAdministrationClient.CreateAgentVersionAsync(
            agentName,
            new ProjectsAgentVersionCreationOptions(definition),
            cancellationToken: cancellationToken);
    }

    /// <summary>
    /// Deletes the Prompt Agent, including all of its versions.
    /// </summary>
    /// <param name="projectClient">The Foundry project client.</param>
    /// <param name="agentVersion">A version of the Prompt Agent to delete.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests.</param>
    public static async Task DeletePromptAgentAsync(
        this AIProjectClient projectClient,
        ProjectsAgentVersion agentVersion,
        CancellationToken cancellationToken = default)
    {
        await projectClient.AgentAdministrationClient.DeleteAgentAsync(agentVersion.Name, cancellationToken);
    }

    /// <summary>
    /// Declares the functions of a <see cref="KernelPlugin"/> as function tools of a Prompt Agent definition.
    /// </summary>
    /// <remarks>
    /// The Prompt Agent stores only the function schemas. Semantic Kernel runs the functions locally when the agent calls them,
    /// so the same plugin must also be added to the kernel of the agent.
    /// </remarks>
    /// <param name="definition">The Prompt Agent definition.</param>
    /// <param name="plugin">The plugin whose functions the Prompt Agent may call.</param>
    public static DeclarativeAgentDefinition AddFunctionTools(this DeclarativeAgentDefinition definition, KernelPlugin plugin)
    {
        foreach (KernelFunction function in plugin)
        {
            // The tool is named "<plugin>_<function>", which is the name Semantic Kernel resolves when the agent calls the function.
            definition.Tools.Add(function.AsOpenAIResponseTool());
        }

        return definition;
    }

    /// <summary>
    /// Creates an <see cref="IChatClient"/> that sends every request to the given Prompt Agent version and lets
    /// Semantic Kernel invoke the kernel functions that the agent calls.
    /// </summary>
    /// <remarks>
    /// Register the client in the kernel of a <see cref="Microsoft.SemanticKernel.Agents.ChatCompletionAgent"/> to use the Prompt Agent
    /// as its chat service. The model, instructions, and tools come from the Prompt Agent definition;
    /// instructions set on the <see cref="Microsoft.SemanticKernel.Agents.ChatCompletionAgent"/> are still sent as an additional system message.
    /// </remarks>
    /// <param name="projectClient">The Foundry project client.</param>
    /// <param name="agentVersion">The Prompt Agent version that receives the requests.</param>
    /// <param name="loggerFactory">An optional logger factory for function invocation logging.</param>
    public static IChatClient AsKernelChatClient(this AIProjectClient projectClient, ProjectsAgentVersion agentVersion, ILoggerFactory? loggerFactory = null)
    {
        IChatClient? promptAgentClient = null;

        // AsAIAgent (Microsoft.Agents.AI.Foundry) wraps the Prompt Agent in an Agent Framework agent. Its innermost chat client sends
        // each request with the agent reference and removes the request options that the service rejects when an agent is specified,
        // such as the model, instructions, and tools. The client factory captures that innermost client so that Semantic Kernel,
        // rather than the Agent Framework agent, runs the function calling loop and applies its function invocation filters.
        _ = projectClient.AsAIAgent(
            agentVersion,
            clientFactory: client =>
            {
                promptAgentClient = client;
                return client;
            });

        // The returned pipeline owns the wrapper, so it is disposed together with the pipeline.
#pragma warning disable CA2000 // Dispose objects before losing scope
        return new LocalHistoryChatClient(promptAgentClient!)
            .AsBuilder()
            .UseKernelFunctionInvocation(loggerFactory)
            .Build();
#pragma warning restore CA2000 // Dispose objects before losing scope
    }

    /// <summary>
    /// Gets the files that the code interpreter tool generated for a response.
    /// </summary>
    /// <remarks>
    /// The generated files are referenced by container file citations on the output text of the raw OpenAI response.
    /// Semantic Kernel keeps that response as the inner content of the message, but doesn't convert the citations into content items.
    /// Download a file with <c>projectClient.GetProjectOpenAIClient().GetContainerClient().DownloadContainerFileAsync(containerId, fileId)</c>.
    /// </remarks>
    /// <param name="message">A response message of an agent that uses a Prompt Agent.</param>
    public static IEnumerable<ContainerFileCitationMessageAnnotation> GetGeneratedFiles(this ChatMessageContent message)
        => message.InnerContent is ResponseResult response ? GetGeneratedFiles(response) : [];

    /// <summary>
    /// Gets the files that the code interpreter tool generated for a streamed response.
    /// </summary>
    /// <remarks>
    /// Only the update that completes the response carries the full response, including its file citations.
    /// </remarks>
    /// <param name="message">A streamed update of an agent that uses a Prompt Agent.</param>
    public static IEnumerable<ContainerFileCitationMessageAnnotation> GetGeneratedFiles(this StreamingChatMessageContent message)
        => message.InnerContent is StreamingResponseCompletedUpdate completed ? GetGeneratedFiles(completed.Response) : [];

    private static IEnumerable<ContainerFileCitationMessageAnnotation> GetGeneratedFiles(ResponseResult response)
        => response.OutputItems
            .OfType<MessageResponseItem>()
            .SelectMany(item => item.Content)
            .SelectMany(part => part.OutputTextAnnotations)
            .OfType<ContainerFileCitationMessageAnnotation>()
            .DistinctBy(citation => citation.FileId);

    /// <summary>
    /// Keeps the Semantic Kernel chat history as the only record of the conversation.
    /// </summary>
    /// <remarks>
    /// The Responses API returns a conversation id with every response. When the function calling loop receives one, it stops
    /// sending the local history and passes an empty message list to the function invocation, which breaks Semantic Kernel's
    /// auto function invocation filters. A <see cref="Microsoft.SemanticKernel.Agents.ChatHistoryAgentThread"/> already holds the whole
    /// conversation, so removing the id makes every request carry the full history instead.
    /// </remarks>
    private sealed class LocalHistoryChatClient(IChatClient innerClient) : DelegatingChatClient(innerClient)
    {
        public override async Task<ChatResponse> GetResponseAsync(IEnumerable<ChatMessage> messages, ChatOptions? options = null, CancellationToken cancellationToken = default)
        {
            ChatResponse response = await base.GetResponseAsync(messages, options, cancellationToken);
            response.ConversationId = null;
            return response;
        }

        public override async IAsyncEnumerable<ChatResponseUpdate> GetStreamingResponseAsync(IEnumerable<ChatMessage> messages, ChatOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
        {
            await foreach (ChatResponseUpdate update in base.GetStreamingResponseAsync(messages, options, cancellationToken))
            {
                update.ConversationId = null;
                yield return update;
            }
        }
    }
}
