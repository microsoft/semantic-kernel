// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using System.Text.Json;
using Azure.AI.Agents.Persistent;
using Azure.AI.Projects;
using Azure.AI.Projects.Agents;
using Azure.Identity;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.ChatCompletion;

/// <summary>
/// Base class for samples that demonstrate the usage of host agents
/// based on API's such as Azure AI Agents or Microsoft Foundry Prompt Agents.
/// </summary>
public abstract class BaseOrchestrationTest(ITestOutputHelper output) : BaseAgentsTest(output)
{
    protected const int ResultTimeoutInSeconds = 30;

    private readonly List<ProjectsAgentVersion> _promptAgents = [];
    private AIProjectClient? _projectClient;

    protected virtual bool EnableLogging => true;

    protected new ILoggerFactory LoggerFactory => this.EnableLogging ? base.LoggerFactory : NullLoggerFactory.Instance;

    protected ChatCompletionAgent CreateChatCompletionAgent(string instructions, string? description = null, string? name = null, Kernel? kernel = null)
    {
        return
            new ChatCompletionAgent
            {
                Name = name,
                Description = description,
                Instructions = instructions,
                Kernel = kernel ?? this.CreateKernelWithChatCompletion(),
            };
    }

    /// <summary>
    /// Creates a <see cref="ChatCompletionAgent"/> whose chat service is a new Microsoft Foundry Prompt Agent.
    /// </summary>
    /// <remarks>
    /// Call <see cref="DeleteFoundryPromptAgentsAsync"/> to delete the Prompt Agents that the sample created.
    /// </remarks>
    protected async Task<ChatCompletionAgent> CreateFoundryPromptAgentAsync(string instructions, string? description = null, string? name = null)
    {
        this._projectClient ??= new AIProjectClient(new Uri(TestConfiguration.AzureAI.Endpoint), new AzureCliCredential());

        // The Prompt Agent definition holds the model and the instructions.
        ProjectsAgentVersion agentVersion =
            await this._projectClient.CreatePromptAgentAsync(
                name ?? "Agent",
                new DeclarativeAgentDefinition(TestConfiguration.AzureAI.ChatModelId)
                {
                    Instructions = instructions,
                });
        this._promptAgents.Add(agentVersion);

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton(this._projectClient.AsKernelChatClient(agentVersion, this.LoggerFactory));

        return
            new ChatCompletionAgent
            {
                Name = name,
                Description = description,
                Kernel = builder.Build(),
            };
    }

    /// <summary>
    /// Deletes the Microsoft Foundry Prompt Agents created by <see cref="CreateFoundryPromptAgentAsync"/>.
    /// </summary>
    protected async Task DeleteFoundryPromptAgentsAsync()
    {
        foreach (ProjectsAgentVersion agentVersion in this._promptAgents)
        {
            await this._projectClient!.DeletePromptAgentAsync(agentVersion);
        }

        this._promptAgents.Clear();
    }

    protected async Task<AzureAIAgent> CreateAzureAIAgentAsync(string instructions, string? description = null, string? name = null, Kernel? kernel = null, IEnumerable<Azure.AI.Agents.Persistent.ToolDefinition>? tools = null)
    {
        var agentsClient = AzureAIAgent.CreateAgentsClient(TestConfiguration.AzureAI.Endpoint, new AzureCliCredential());

        PersistentAgent definition = await agentsClient.Administration.CreateAgentAsync(
            TestConfiguration.AzureAI.ChatModelId,
            name,
            description,
            instructions,
            tools);

        return
            new(definition, agentsClient)
            {
                Kernel = kernel ?? new Kernel(),
            };
    }

    protected static void WriteResponse(ChatMessageContent response)
    {
        if (!string.IsNullOrEmpty(response.Content))
        {
            System.Console.WriteLine($"\n# RESPONSE {response.Role}{(response.AuthorName is not null ? $" - {response.AuthorName}" : string.Empty)}: {response}");
        }
    }

    protected static void WriteStreamedResponse(IEnumerable<StreamingChatMessageContent> streamedResponses)
    {
        string? authorName = null;
        AuthorRole? authorRole = null;
        StringBuilder builder = new();
        foreach (StreamingChatMessageContent response in streamedResponses)
        {
            authorName ??= response.AuthorName;
            authorRole ??= response.Role;

            if (!string.IsNullOrEmpty(response.Content))
            {
                builder.Append($"({JsonSerializer.Serialize(response.Content)})");
            }
        }

        if (builder.Length > 0)
        {
            System.Console.WriteLine($"\n# STREAMED {authorRole ?? AuthorRole.Assistant}{(authorName is not null ? $" - {authorName}" : string.Empty)}: {builder}\n");
        }
    }

    protected sealed class OrchestrationMonitor
    {
        public List<StreamingChatMessageContent> StreamedResponses = [];

        public ChatHistory History { get; } = [];

        public ValueTask ResponseCallback(ChatMessageContent response)
        {
            this.History.Add(response);
            WriteResponse(response);
            return ValueTask.CompletedTask;
        }

        public ValueTask StreamingResultCallback(StreamingChatMessageContent streamedResponse, bool isFinal)
        {
            this.StreamedResponses.Add(streamedResponse);

            if (isFinal)
            {
                WriteStreamedResponse(this.StreamedResponses);
                this.StreamedResponses.Clear();
            }

            return ValueTask.CompletedTask;
        }
    }
}
