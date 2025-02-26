// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.SemanticKernel.Http;
using OpenAI;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Provides extension methods for <see cref="Kernel"/>.
/// </summary>
[ExcludeFromCodeCoverage]
internal static class KernelExtensions
{
    private const string ApiKey = "api_key";

    private const string OpenAI = "openai";
    private const string AzureOpenAI = "azure_openai";

    /// <summary>
    /// Return the <see cref="OpenAIClient"/> to be used with the specified <see cref="AgentDefinition"/>.
    /// </summary>
    /// <param name="kernel">Kernel instance which will be used to resolve a default <see cref="OpenAIClient"/>.</param>
    /// <param name="agentDefinition">Agent definition which will be used to provide configuration for the <see cref="OpenAIClient"/>.</param>
    public static OpenAIClient GetOpenAIClient(this Kernel kernel, AgentDefinition agentDefinition)
    {
        Verify.NotNull(agentDefinition);

        // Use the agent configuration as the first option
        var configuration = agentDefinition?.Model?.Configuration;
        if (configuration is not null)
        {
            if (configuration.Type is null)
            {
                throw new InvalidOperationException("OpenAI client type must be specified.");
            }

#pragma warning disable CA2000 // Dispose objects before losing scope, not applicable because the HttpClient is created and may be used elsewhere
            var httpClient = HttpClientProvider.GetHttpClient(kernel.Services);
#pragma warning restore CA2000 // Dispose objects before losing scope

            if (configuration.Type.Equals(OpenAI, StringComparison.OrdinalIgnoreCase))
            {
                OpenAIClientOptions clientOptions = OpenAIClientProvider.CreateOpenAIClientOptions(configuration.GetEndpointUri(), httpClient);
                return new OpenAIClient(configuration.GetApiKeyCredential(), clientOptions);
            }
            else if (configuration.Type.Equals(AzureOpenAI, StringComparison.OrdinalIgnoreCase))
            {
                var endpoint = configuration.GetEndpointUri();
                Verify.NotNull(endpoint, "Endpoint must be specified when using Azure OpenAI.");

                AzureOpenAIClientOptions clientOptions = OpenAIClientProvider.CreateAzureClientOptions(httpClient);

                if (configuration.ExtensionData.TryGetValue(ApiKey, out var apiKey) && apiKey is not null)
                {
                    return new AzureOpenAIClient(endpoint, configuration.GetApiKeyCredential(), clientOptions);
                }

                return new AzureOpenAIClient(endpoint, new DefaultAzureCredential(), clientOptions);
            }

            throw new InvalidOperationException($"Invalid OpenAI client type '{configuration.Type}' was specified.");
        }

        // Use the client registered on the kernel
        var client = kernel.GetAllServices<OpenAIClient>().FirstOrDefault();
        if (client is not null)
        {
            return client;
        }

        throw new InvalidOperationException("OpenAI client not found.");
    }
}
