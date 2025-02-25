// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Net.Http;
using Azure.AI.Projects;
using Azure.Identity;

namespace Microsoft.SemanticKernel.Agents.AzureAI;

/// <summary>
/// Provides extension methods for <see cref="Kernel"/>.
/// </summary>
internal static class KernelExtensions
{
    private const string ConnectionString = "connection_string";

    /// <summary>
    /// Return the <see cref="AIProjectClient"/> to be used with the specified <see cref="AgentDefinition"/>.
    /// </summary>
    /// <param name="kernel">Kernel instance which will be used to resolve a default <see cref="AzureAIClientProvider"/>.</param>
    /// <param name="agentDefinition">Agent definition which will be used to provide configuration for the <see cref="AzureAIClientProvider"/>.</param>
    public static AIProjectClient GetAIProjectClient(this Kernel kernel, AgentDefinition agentDefinition)
    {
        Verify.NotNull(agentDefinition);

        // Use the agent configuration as the first option
        var configuration = agentDefinition?.Model?.Configuration;
        if (configuration is not null)
        {
            var hasConnectionString = configuration.ExtensionData.TryGetValue(ConnectionString, out var connectionString) && connectionString is not null;
            if (hasConnectionString)
            {
                var httpClient = kernel.GetAllServices<HttpClient>().FirstOrDefault();
                AIProjectClientOptions clientOptions = AzureAIClientProvider.CreateAzureClientOptions(httpClient);
                return new(connectionString!.ToString()!, new AzureCliCredential(), clientOptions);
            }
        }

        // Return the client registered on the kernel
        var client = kernel.GetAllServices<AIProjectClient>().FirstOrDefault();
        if (client is not null)
        {
            return client;
        }

        throw new InvalidOperationException("AzureAI project client not found.");
    }
}
