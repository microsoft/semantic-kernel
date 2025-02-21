// Copyright (c) Microsoft. All rights reserved.
using System;
using System.ClientModel;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using Azure.Identity;
using OpenAI;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Provides extension methods for <see cref="Kernel"/>.
/// </summary>
[ExcludeFromCodeCoverage]
internal static class KernelExtensions
{
    private const string Endpoint = "endpoint";
    private const string ApiKey = "api_key";

    /// <summary>
    /// Return the <see cref="OpenAIClientProvider"/> to be used with the specified <see cref="AgentDefinition"/>.
    /// </summary>
    /// <param name="kernel">Kernel instance which will be used to resolve a default <see cref="OpenAIClientProvider"/>.</param>
    /// <param name="agentDefinition">Agent definition which will be used to provide configuration for the <see cref="OpenAIClientProvider"/>.</param>
    public static OpenAIClientProvider GetOpenAIClientProvider(this Kernel kernel, AgentDefinition agentDefinition)
    {
        Verify.NotNull(agentDefinition);

        // Use the agent configuration as the first option
        var configuration = agentDefinition?.Model?.Configuration;
        if (configuration is not null)
        {
            var hasEndpoint = configuration.TryGetValue(Endpoint, out var endpoint) && endpoint is not null;
            var hasApiKey = configuration.TryGetValue(ApiKey, out var apiKey) && apiKey is not null;
            if (hasApiKey && hasEndpoint)
            {
                return OpenAIClientProvider.ForAzureOpenAI(new ApiKeyCredential(apiKey!.ToString()!), new Uri(endpoint!.ToString()!));
            }
            else if (hasApiKey && !hasEndpoint)
            {
                return OpenAIClientProvider.ForOpenAI(new ApiKeyCredential(apiKey!.ToString()!));
            }
            else if (!hasApiKey && hasEndpoint)
            {
                return OpenAIClientProvider.ForAzureOpenAI(new AzureCliCredential(), new Uri(endpoint!.ToString()!));
            }
        }

        // Use the client registered on the kernel
        var client = kernel.GetAllServices<OpenAIClient>().FirstOrDefault();
        if (client is not null)
        {
            return OpenAIClientProvider.FromClient(client);
        }

        // Use the provider registered on the kernel
        var clientProvider = kernel.GetAllServices<OpenAIClientProvider>().FirstOrDefault();
        return (OpenAIClientProvider?)clientProvider ?? throw new InvalidOperationException("OpenAI client provider not found.");
    }
}
