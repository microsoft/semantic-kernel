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
            AzureOpenAIChatConfig.ConnectionStringName,
            (settings) => settings.Credential = builder.Environment.IsProduction()
                ? new DefaultAzureCredential()
                : new AzureCliCredential()); // Use credentials from Azure CLI for local development.

        // Add AzureOpenAI chat completion service.
        builder.Services.AddAzureOpenAIChatCompletion(hostConfig.AzureOpenAIChat.DeploymentName);
    }
}
