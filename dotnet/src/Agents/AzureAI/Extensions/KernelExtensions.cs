// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Net.Http;
using Azure.AI.Projects;
using Azure.Core;
using Azure.Identity;
using Microsoft.Extensions.DependencyInjection;

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

                var tokenCredential = kernel.Services.GetService<TokenCredential>() ?? new DefaultAzureCredential();
                return new(connectionString!.ToString()!, tokenCredential, clientOptions);
            }
        }

        // Return the client registered on the kernel
        var client = kernel.GetAllServices<AIProjectClient>().FirstOrDefault();
        return (AIProjectClient?)client ?? throw new InvalidOperationException("AzureAI project client not found.");
    }
}
