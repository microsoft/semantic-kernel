// Copyright (c) Microsoft. All rights reserved.

using ChatWithAgent.Configuration;

namespace ChatWithAgent.AppHost.Extensions;

/// <summary>
/// Resource builder extensions.
/// </summary>
public static class ResourceBuilderExtensions
{
    /// <summary>
    /// Adds host configuration as environment variables to the resource.
    /// </summary>
    /// <typeparam name="T">The resource type.</typeparam>
    /// <param name="builder">The resource builder.</param>
    /// <param name="config">The host configuration.</param>
    /// <returns>The <see cref="IResourceBuilder{T}"/>.</returns>
    public static IResourceBuilder<T> WithEnvironment<T>(this IResourceBuilder<T> builder, HostConfig config) where T : IResourceWithEnvironment
    {
        ArgumentNullException.ThrowIfNull(builder);
        ArgumentNullException.ThrowIfNull(config);

        // Add AI chat service configuration to the environment variables so that Api Service can access it.
        builder.WithEnvironment(nameof(config.AIChatService), config.AIChatService);

        switch (config.AIChatService)
        {
            case AzureOpenAIChatConfig.ConfigSectionName:
            {
                builder.WithEnvironment($"{HostConfig.AIServicesSectionName}__{nameof(config.AzureOpenAIChat)}__{nameof(config.AzureOpenAIChat.DeploymentName)}", config.AzureOpenAIChat.DeploymentName);
                builder.WithEnvironment($"{HostConfig.AIServicesSectionName}__{nameof(config.AzureOpenAIChat)}__{nameof(config.AzureOpenAIChat.ModelName)}", config.AzureOpenAIChat.ModelName);
                break;
            }

            case OpenAIChatConfig.ConfigSectionName:
            {
                builder.WithEnvironment($"{HostConfig.AIServicesSectionName}__{nameof(config.OpenAIChat)}__{nameof(config.OpenAIChat.ModelName)}", config.OpenAIChat.ModelName);
                break;
            }

            default:
                throw new NotSupportedException($"AI service '{config.AIChatService}' is not supported.");
        }

        // Add RAG configuration to the environment variables so that Api Service can access it.
        builder.WithEnvironment($"{nameof(config.Rag)}__{nameof(config.Rag.AIEmbeddingService)}", config.Rag.AIEmbeddingService);
        builder.WithEnvironment($"{nameof(config.Rag)}__{nameof(config.Rag.VectorStoreType)}", config.Rag.VectorStoreType);
        builder.WithEnvironment($"{nameof(config.Rag)}__{nameof(config.Rag.CollectionName)}", config.Rag.CollectionName);

        switch (config.Rag.AIEmbeddingService)
        {
            case AzureOpenAIEmbeddingsConfig.ConfigSectionName:
            {
                builder.WithEnvironment($"{HostConfig.AIServicesSectionName}__{nameof(config.AzureOpenAIEmbeddings)}__{nameof(config.AzureOpenAIEmbeddings.DeploymentName)}", config.AzureOpenAIEmbeddings.DeploymentName);
                builder.WithEnvironment($"{HostConfig.AIServicesSectionName}__{nameof(config.AzureOpenAIEmbeddings)}__{nameof(config.AzureOpenAIEmbeddings.ModelName)}", config.AzureOpenAIEmbeddings.ModelName);
                break;
            }

            case OpenAIEmbeddingsConfig.ConfigSectionName:
            {
                builder.WithEnvironment($"{HostConfig.AIServicesSectionName}__{nameof(config.OpenAIEmbeddings)}__{nameof(config.OpenAIEmbeddings.ModelName)}", config.OpenAIEmbeddings.ModelName);
                break;
            }

            default:
                throw new NotSupportedException($"AI service '{config.Rag.AIEmbeddingService}' is not supported.");
        }

        return builder;
    }

    /// <summary>
    /// Adds connection strings of source resources to a destination resource.
    /// </summary>
    /// <typeparam name="T">The type of the destination resource.</typeparam>
    /// <param name="builder">The destination resource.</param>
    /// <param name="resources">The source resource with the connection string.</param>
    /// <returns>The updated resource builder.</returns>
    public static IResourceBuilder<T> WithReferences<T>(this IResourceBuilder<T> builder, IList<IResourceBuilder<IResourceWithConnectionString>> resources) where T : IResourceWithEnvironment
    {
        ArgumentNullException.ThrowIfNull(builder);
        ArgumentNullException.ThrowIfNull(resources);

        foreach (var resource in resources)
        {
            builder.WithReference(resource);
        }

        return builder;
    }
}
