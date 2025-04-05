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
    public static async ValueTask<Kernel> CreateKernelAsync(AIProjectClient client, string deploymentName, ILoggerFactory loggerFactory)
    {
        ConnectionProperties openAIConnectionProperties = await client.GetConnectionAsync();
        string endpoint = openAIConnectionProperties.GetEndpoint();
        string? apikey = openAIConnectionProperties.GetApiKey();

        IKernelBuilder builder = Kernel.CreateBuilder();

        // Define the logging services
        builder.Services.AddSingleton(loggerFactory);

        // Configure a chat-completion service
        if (!string.IsNullOrEmpty(apikey))
        {
            builder.AddAzureOpenAIChatCompletion(
                deploymentName,
                endpoint,
                apikey);
        }
        else
        {
            builder.AddAzureOpenAIChatCompletion(
                deploymentName,
                endpoint,
                new AzureCliCredential());
        }

        // Create the kernel
        return builder.Build();
    }
}
