// Copyright (c) Microsoft. All rights reserved.

using ChatWithAgent.Configuration;

namespace ChatWithAgent.AppHost.Extensions;

/// <summary>
/// Distributed application builder extensions.
/// </summary>
internal static class DistributedApplicationBuilderExtensions
{
    /// <summary>
    /// Adds Azure OpenAI service and OpenAI models.
    /// </summary>
    /// <param name="builder">The distributed application builder.</param>
    /// <param name="config">The host configuration.</param>
    /// <returns>A reference to the <see cref="IResourceBuilder{IResourceWithConnectionString}"/>.</returns>
    internal static IResourceBuilder<IResourceWithConnectionString> AddAzureOpenAIResources(this IDistributedApplicationBuilder builder, HostConfig config)
    {
        // Add Azure OpenAI service
        var azureOpenAI = builder.AddAzureOpenAI(HostConfig.AzureOpenAIConnectionStringName);

        // Add Azure OpenAI chat model
        if (config.AIChatService == AzureOpenAIChatConfig.ConfigSectionName)
        {
            azureOpenAI.AddDeployment(new AzureOpenAIDeployment(
                name: config.AzureOpenAIChat.DeploymentName,
                modelName: config.AzureOpenAIChat.ModelName,
                modelVersion: config.AzureOpenAIChat.ModelVersion)
            );
        }

        // Add Azure OpenAI embeddings model
        if (config.AIEmbeddingsService == AzureOpenAIEmbeddingsConfig.ConfigSectionName)
        {
            azureOpenAI.AddDeployment(new AzureOpenAIDeployment(
                name: config.AzureOpenAIEmbeddings.DeploymentName,
                modelName: config.AzureOpenAIEmbeddings.ModelName,
                modelVersion: config.AzureOpenAIEmbeddings.ModelVersion)
            );
        }

        return azureOpenAI;
    }
}
