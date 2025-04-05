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
/// Provider to create a <see cref="ChatServiceAgent"/> instance and
/// its associated <see cref="AgentThread"/>.
/// </summary>
public class ChatServiceAgentProvider(IConfiguration configuration, ILoggerFactory loggerFactory)
    : ServiceAgentProvider(configuration, loggerFactory)
{
    private static class Settings
    {
        public const string DeploymentName = "AzureOpenAI:DeploymentName";
        public const string ConnectionString = "AzureAI:ConnectionString";
    }

    /// <inheritdoc/>
    public override async ValueTask<Agent> CreateAgentAsync(string id, string? name, CancellationToken cancellationToken = default)
    {
        Kernel kernel = await this.CreateKernelAsync();

        ChatServiceAgent agent =
            new()
            {
                Id = id,
                Name = name ?? "DemoAgent",
                Kernel = kernel,
            };

        return agent;
    }

    /// <inheritdoc/>
    public override async ValueTask<AgentThread> CreateThreadAsync(string threadId, CancellationToken cancellationToken)
    {
        IAsyncEnumerable<ChatMessageContent> messages = this.GetThreadMessagesAsync(threadId, limit: null, cancellationToken);

        ChatHistory history = [.. await messages.ToArrayAsync(cancellationToken)];

        ChatHistoryAgentThread agentThread = new(history, threadId);

        return agentThread;
    }

    private async ValueTask<Kernel> CreateKernelAsync()
    {
        ConnectionProperties openAIConnectionProperties = await GetConnectionAsync(this.FoundrySettings.ConnectionString);
        string endpoint = openAIConnectionProperties.GetEndpoint();
        string? apikey = openAIConnectionProperties.GetApiKey();

        IKernelBuilder builder = Kernel.CreateBuilder();

        // Define the logging services
        builder.Services.AddSingleton(this.LoggerFactory);

        // Configure a chat-completion service
        if (!string.IsNullOrEmpty(apikey))
        {
            builder.AddAzureOpenAIChatCompletion(
                this.FoundrySettings.DeploymentName,
                endpoint,
                apikey);
        }
        else
        {
            builder.AddAzureOpenAIChatCompletion(
                this.FoundrySettings.DeploymentName,
                endpoint,
                new AzureCliCredential());
        }

        // Create the kernel
        return builder.Build();
    }

    private static async Task<ConnectionProperties> GetConnectionAsync(string connectionString, ConnectionType connectionType = ConnectionType.AzureOpenAI)
    {
        AIProjectClient client = new(connectionString, new AzureCliCredential());
        ConnectionsClient connectionsClient = client.GetConnectionsClient();

        ConnectionResponse connection = await connectionsClient.GetDefaultConnectionAsync(connectionType, includeAll: true);

        return connection.Properties;
    }
}
