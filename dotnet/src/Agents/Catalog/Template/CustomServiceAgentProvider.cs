// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.Projects;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Service;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.Template;

/// <summary>
/// Provider to create a <see cref="CustomServiceAgent"/> instance and
/// its associated <see cref="AgentThread"/>.
/// </summary>
public class CustomServiceAgentProvider(IConfiguration configuration, ILoggerFactory loggerFactory)
    : ServiceAgentProvider(configuration, loggerFactory)
{
    /// <inheritdoc/>
    public override async ValueTask<Agent> CreateAgentAsync(string id, string? name, CancellationToken cancellationToken = default)
    {
        Kernel kernel = await this.CreateKernelAsync();

        CustomServiceAgent agent =
            new()
            {
                Id = id,
                Name = name ?? "CustomAgent",
                Kernel = kernel,
            };

        return agent;
    }

    /// <summary>
    /// Responsible for creating and initializing the agent thread to be
    /// passed to the agent during invocation.
    /// </summary>
    public override async ValueTask<AgentThread> CreateThreadAsync(string threadId, CancellationToken cancellationToken)
    {
        // Retrieves the entire external thread
        IAsyncEnumerable<ChatMessageContent> messages = this.GetThreadMessagesAsync(threadId, limit: null, cancellationToken);

        ChatHistory history = [.. await messages.ToArrayAsync(cancellationToken)];

        ChatHistoryAgentThread agentThread = new(history, threadId);

        return agentThread;
    }

    // NOTE: A OOTB agent will exist in a particular user subscription and Foundry project
    // The ability to connect to AI services from this project is absolute required.
    // Specifics on how this is managed by the hosting container may evolve, but for now
    // the expected approach is being used here.
    // The target model will be defined as part of the agent configuration.
    private async ValueTask<Kernel> CreateKernelAsync()
    {
        ConnectionProperties openAIConnectionProperties = await this.Client.GetConnectionAsync();
        string endpoint = openAIConnectionProperties.GetEndpoint();
        string? apikey = openAIConnectionProperties.GetApiKey();

        IKernelBuilder builder = Kernel.CreateBuilder();

        // Define the logging services
        builder.Services.AddSingleton(this.LoggerFactory);

        // Retrieve the configured dall-e model name
        string dalleModel = this.Configuration.GetRequiredValue("foundry:imagedeployment");

        if (!string.IsNullOrEmpty(apikey))
        {
            // Configure a chat-completion service
            builder.AddAzureOpenAIChatCompletion(
                this.FoundrySettings.DeploymentName,
                endpoint,
                apikey);
            // Configure text-to-image service
            builder.AddAzureOpenAITextToImage(
                dalleModel,
                endpoint,
                apikey);
        }
        else
        {
            // Configure a chat-completion service
            builder.AddAzureOpenAIChatCompletion(
                this.FoundrySettings.DeploymentName,
                endpoint,
                new AzureCliCredential());
            // Configure text-to-image service
            builder.AddAzureOpenAITextToImage(
                dalleModel,
                endpoint,
                new AzureCliCredential());
        }

        // Create the kernel
        return builder.Build();
    }
}
