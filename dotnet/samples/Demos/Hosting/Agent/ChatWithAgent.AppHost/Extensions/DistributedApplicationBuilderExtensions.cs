// Copyright (c) Microsoft. All rights reserved.

using ChatWithAgent.Configuration;

namespace ChatWithAgent.AppHost.Extensions;

/// <summary>
/// Distributed application builder extensions.
/// </summary>
internal static class DistributedApplicationBuilderExtensions
{
    /// <summary>
    /// Adds Azure OpenAI service and OpenAI model(s) to the distributed application.
    /// </summary>
    /// <param name="builder">The distributed application builder.</param>
    /// <param name="config">The host configuration.</param>
    /// <returns>A reference to the <see cref="IResourceBuilder{IResourceWithConnectionString}"/>.</returns>
    internal static IResourceBuilder<IResourceWithConnectionString> AddAzureOpenAI(this IDistributedApplicationBuilder builder, HostConfig config)
    {
        if (builder.ExecutionContext.IsPublishMode)
        {
            // Deploy and provision Azure OpenAI service with AI models
            return builder
                .AddAzureOpenAI(AzureOpenAIChatConfig.ConnectionStringName)
                .AddDeployment(new AzureOpenAIDeployment(
                    name: config.AzureOpenAIChat.DeploymentName,
                    modelName: config.AzureOpenAIChat.ModelName,
                    modelVersion: config.AzureOpenAIChat.ModelVersion)
                );
        }

        // Use an existing Azure OpenAI service via connection string
        return builder.AddConnectionString(AzureOpenAIChatConfig.ConnectionStringName);
    }
}
