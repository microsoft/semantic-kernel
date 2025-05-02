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

        // Add configured AI chat service to the environment variables so that Api Service can access it.
        builder.WithEnvironment(nameof(config.AIChatService), config.AIChatService);

        switch (config.AIChatService)
        {
            case AzureOpenAIChatConfig.ConfigSectionName:
            {
                // Add Azure OpenAI chat model deployment name to environment variables so that Api Service can access it.
                builder.WithEnvironment($"{HostConfig.AIServicesSectionName}__{AzureOpenAIChatConfig.ConfigSectionName}__{nameof(config.AzureOpenAIChat.DeploymentName)}", config.AzureOpenAIChat.DeploymentName);
                break;
            }

            default:
                throw new NotSupportedException($"AI service '{config.AIChatService}' is not supported.");
        }

        return builder;
    }
}
