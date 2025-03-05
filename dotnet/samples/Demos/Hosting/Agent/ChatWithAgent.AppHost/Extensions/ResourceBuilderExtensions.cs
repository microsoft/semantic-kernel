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

        // Add configured AI chat and embeddings services to the environment variables so that Api Service can access them.
        builder.WithEnvironment(nameof(config.AIChatService), config.AIChatService);
        builder.WithEnvironment(nameof(config.AIEmbeddingsService), config.AIEmbeddingsService);

        switch (config.AIChatService)
        {
            case AzureOpenAIChatConfig.ConfigSectionName:
            {
                // Add Azure OpenAI chat model deployment name to environment variables so that Api Service can access it.
                builder.WithEnvironment($"{HostConfig.AIServicesSectionName}__{AzureOpenAIChatConfig.ConfigSectionName}__{nameof(config.AzureOpenAIChat.DeploymentName)}", config.AzureOpenAIChat.DeploymentName);
                break;
            }

            case OpenAIChatConfig.ConfigSectionName:
            {
                // Add OpenAI chat model name to environment variables so that Api Service can access it.
                builder.WithEnvironment($"{HostConfig.AIServicesSectionName}__{OpenAIChatConfig.ConfigSectionName}__{nameof(config.OpenAIChat.ModelName)}", config.OpenAIChat.ModelName);
                break;
            }

            default:
                throw new NotSupportedException($"AI service '{config.AIChatService}' is not supported.");
        }

        switch (config.AIEmbeddingsService)
        {
            case AzureOpenAIEmbeddingsConfig.ConfigSectionName:
            {
                // Add Azure OpenAI embeddings model deployment name to environment variables so that Api Service can access it.
                builder.WithEnvironment($"{HostConfig.AIServicesSectionName}__{AzureOpenAIEmbeddingsConfig.ConfigSectionName}__{nameof(config.AzureOpenAIEmbeddings.DeploymentName)}", config.AzureOpenAIEmbeddings.DeploymentName);
                break;
            }

            case OpenAIEmbeddingsConfig.ConfigSectionName:
            {
                // Add OpenAI embeddings model name to environment variables so that Api Service can access it.
                builder.WithEnvironment($"{HostConfig.AIServicesSectionName}__{OpenAIEmbeddingsConfig.ConfigSectionName}__{nameof(config.OpenAIEmbeddings.ModelName)}", config.OpenAIEmbeddings.ModelName);
                break;
            }

            default:
                throw new NotSupportedException($"AI service '{config.AIEmbeddingsService}' is not supported.");
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
