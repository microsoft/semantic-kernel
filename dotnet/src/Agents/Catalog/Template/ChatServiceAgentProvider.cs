// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Service;
using Microsoft.SemanticKernel.ChatCompletion;
using Foundry = Azure.AI.Projects;

namespace Microsoft.SemanticKernel.Agents.Template;

/// <summary>
/// Provider to create a <see cref="ChatServiceAgent"/> instance and
/// its associated <see cref="AgentThread"/>.
/// </summary>
public class ChatServiceAgentProvider(IConfiguration configuration, ILoggerFactory loggerFactory)
    : ServiceAgentProvider(configuration, loggerFactory)
{
    private static class Settings
    {
        public const string DeploymentName = "AzureOpenAI:DeploymentName";
        public const string Endpoint = "AzureOpenAI:Endpoint";
        public const string ApiKey = "AzureOpenAI:ApiKey";
        public const string ConnectionString = "AzureAI:ConnectionString";
    }

    /// <inheritdoc/>
    public override ValueTask<Agent> CreateAgentAsync(string id, string? name, CancellationToken cancellationToken = default)
    {
        ChatServiceAgent agent =
            new()
            {
                Id = id,
                Name = name ?? "DemoAgent",
                Kernel = this.CreateKernel(),
            };

        return ValueTask.FromResult<Agent>(agent);
    }

    /// <inheritdoc/>
    public override async ValueTask<AgentThread> CreateThreadAsync(string threadId, CancellationToken cancellationToken)
    {
        Foundry.AIProjectClient client = new(
            this.Configuration.GetRequiredValue(Settings.ConnectionString),
            new AzureCliCredential());

        IAsyncEnumerable<ChatMessageContent> messages = GetThreadMessagesAsync(client.GetAgentsClient(), threadId, limit: null, cancellationToken);
        ChatHistory history = [.. await messages.ToArrayAsync(cancellationToken)];

        ChatHistoryAgentThread agentThread = new(history, threadId);

        return agentThread;
    }

    private Kernel CreateKernel()
    {
        IKernelBuilder builder = Kernel.CreateBuilder();

        // Define the logging services
        builder.Services.AddSingleton(this.LoggerFactory);

        // Configure a chat-completion service
        builder.AddAzureOpenAIChatCompletion(
            this.Configuration.GetRequiredValue(Settings.ConnectionString),
            this.Configuration.GetRequiredValue(Settings.DeploymentName),
            this.Configuration.GetRequiredValue(Settings.Endpoint),
            this.Configuration.GetRequiredValue(Settings.ApiKey));

        // Create the kernel
        return builder.Build();
    }
}
