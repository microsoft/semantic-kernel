// Copyright (c) Microsoft. All rights reserved.

using Azure.Identity;
using ChatWithAgent.Configuration;
using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.Hosting;
using Microsoft.SemanticKernel;

namespace ChatWithAgent.ApiService.Extensions;

/// <summary>
/// Web application builder extensions.
/// </summary>
internal static class WebApplicationBuilderExtensions
{
    /// <summary>
    /// Adds Azure OpenAI services to the web application.
    /// </summary>
    /// <param name="builder">The web application builder.</param>
    /// <param name="hostConfig">The host configuration.</param>
    internal static void AddAzureOpenAIServices(this WebApplicationBuilder builder, HostConfig hostConfig)
    {
        // Add AzureOpenAI client.
        builder.AddAzureOpenAIClient(
            HostConfig.AzureOpenAIConnectionStringName,
            (settings) => settings.Credential = builder.Environment.IsProduction()
                ? new DefaultAzureCredential()
                : new AzureCliCredential()); // Use credentials from Azure CLI for local development.

        if (hostConfig.AIChatService == AzureOpenAIChatConfig.ConfigSectionName)
        {
            builder.Services.AddAzureOpenAIChatCompletion(hostConfig.AzureOpenAIChat.DeploymentName);
        }

        if (hostConfig.AIEmbeddingsService == AzureOpenAIEmbeddingsConfig.ConfigSectionName)
        {
            builder.Services.AddAzureOpenAITextEmbeddingGeneration(hostConfig.AzureOpenAIEmbeddings.DeploymentName);
        }
    }

    /// <summary>
    /// Adds OpenAI services to the web application.
    /// </summary>
    /// <param name="builder">The web application builder.</param>
    /// <param name="hostConfig">The host configuration.</param>
    internal static void AddOpenAIServices(this WebApplicationBuilder builder, HostConfig hostConfig)
    {
        // Add OpenAI client.
        builder.AddOpenAIClient(HostConfig.OpenAIConnectionStringName);

        if (hostConfig.AIChatService == OpenAIChatConfig.ConfigSectionName)
        {
            builder.Services.AddOpenAIChatCompletion(hostConfig.OpenAIChat.ModelName);
        }

        if (hostConfig.AIEmbeddingsService == OpenAIEmbeddingsConfig.ConfigSectionName)
        {
            builder.Services.AddOpenAITextEmbeddingGeneration(hostConfig.OpenAIEmbeddings.ModelName);
        }
    }
}
