// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Azure.AI.Projects;
using Azure.Identity;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Service;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.IntentTriage;

/// <summary>
/// Factory for creating a <see cref="Kernel"/> instance.
/// </summary>
internal static class KernelFactory
{
    /// <summary>
    /// Create a <see cref="Kernel"/> instance configured with a logging
    /// and an <see cref="IChatCompletionService"/>.
    /// </summary>
    /// <remarks>
    /// PLACEHOLDER: Expect the specifics on authentication for a hosted agent to evolve.
    /// </remarks>
    public static async ValueTask<Kernel> CreateKernelAsync(FoundrySettings settings, ILoggerFactory loggerFactory)
    {
        ConnectionProperties openAIConnectionProperties = await GetConnectionAsync(settings.ConnectionString);
        string endpoint = openAIConnectionProperties.GetEndpoint();
        string? apikey = openAIConnectionProperties.GetApiKey();

        IKernelBuilder builder = Kernel.CreateBuilder();

        // Define the logging services
        builder.Services.AddSingleton(loggerFactory);

        // Configure a chat-completion service
        if (!string.IsNullOrEmpty(apikey))
        {
            builder.AddAzureOpenAIChatCompletion(
                settings.DeploymentName,
                endpoint,
                apikey);
        }
        else
        {
            builder.AddAzureOpenAIChatCompletion(
                settings.DeploymentName,
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
