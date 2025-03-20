// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using Azure.AI.Projects;
using Azure.Core;
using Azure.Identity;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Http;

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
    /// <param name="kernel">Kernel instance which will be used to resolve a default <see cref="AIProjectClient"/>.</param>
    /// <param name="agentDefinition">Agent definition which will be used to provide configuration for the <see cref="AIProjectClient"/>.</param>
    public static AIProjectClient GetAIProjectClient(this Kernel kernel, AgentDefinition agentDefinition)
    {
        Verify.NotNull(agentDefinition);

        // Use the agent configuration as the first option
        var configuration = agentDefinition?.Model?.Configuration;
        if (configuration is not null)
        {
            if (configuration.ExtensionData.TryGetValue(ConnectionString, out var value) && value is string connectionString)
            {
#pragma warning disable CA2000 // Dispose objects before losing scope, not relevant because the HttpClient is created and may be used elsewhere
                var httpClient = HttpClientProvider.GetHttpClient(kernel.Services);
#pragma warning restore CA2000 // Dispose objects before losing scope
                AIProjectClientOptions clientOptions = AzureAIClientProvider.CreateAzureClientOptions(httpClient);

                var tokenCredential = kernel.Services.GetService<TokenCredential>() ?? new DefaultAzureCredential();
                return new(connectionString, tokenCredential, clientOptions);
            }
        }

        // Return the client registered on the kernel
        var client = kernel.GetAllServices<AIProjectClient>().FirstOrDefault();
        return (AIProjectClient?)client ?? throw new InvalidOperationException("AzureAI project client not found.");
    }
}
