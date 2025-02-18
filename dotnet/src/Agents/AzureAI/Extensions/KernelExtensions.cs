// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.Linq;

namespace Microsoft.SemanticKernel.Agents.AzureAI.Extensions;

/// <summary>
/// Provides extension methods for <see cref="Kernel"/>.
/// </summary>
internal static class KernelExtensions
{
    private const string ConfigEndpoint = "endpoint";
    private const string ConfigApiKey = "api_key";

    /// <summary>
    /// Return the <see cref="AzureAIClientProvider"/> to be used with the specified <see cref="AgentDefinition"/>.
    /// </summary>
    /// <param name="kernel">Kernel instance which will be used to resolve a default <see cref="AzureAIClientProvider"/>.</param>
    /// <param name="agentDefinition">Agent definition whih will be used t provide configuration for the <see cref="AzureAIClientProvider"/>.</param>
    public static AzureAIClientProvider GetAzureAIClientProvider(this Kernel kernel, AgentDefinition agentDefinition)
    {
        Verify.NotNull(agentDefinition);

        // Use the agent configuration as the first option
        var configuration = agentDefinition?.Model?.Configuration;
        if (configuration is not null)
        {
            var hasEndpoint = configuration.TryGetValue(ConfigEndpoint, out var endpoint) && endpoint is not null;
            var hasApiKey = configuration.TryGetValue(ConfigApiKey, out var apiKey) && apiKey is not null;
            if (hasApiKey && hasEndpoint)
            {
                return OpenAIClientProvider.ForAzureOpenAI(new ApiKeyCredential(apiKey!.ToString()!), new Uri(endpoint!.ToString()!));
            }
            else if (hasApiKey && !hasEndpoint)
            {
                return OpenAIClientProvider.ForOpenAI(new ApiKeyCredential(apiKey!.ToString()!));
            }
            /*
            else if (!hasApiKey && hasEndpoint)
            {
                return OpenAIClientProvider.ForAzureOpenAI(new AzureCliCredential(), new Uri(endpoint!.ToString()!));
            }
            */
        }

        // Return the service registered on the kernel
        var clientProvider = kernel.GetAllServices<AzureAIClientProvider>().FirstOrDefault();
        if (clientProvider is not null)
        {
            return clientProvider;
        }

        throw new InvalidOperationException("AzureAI client provider not found.");
    }
}
