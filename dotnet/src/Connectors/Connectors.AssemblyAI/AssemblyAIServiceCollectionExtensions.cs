// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.AudioToText;
using Microsoft.SemanticKernel.Connectors.AssemblyAI;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides extension methods for <see cref="IServiceCollection"/> and related classes to configure AssemblyAI connectors.
/// </summary>
public static class AssemblyAIServiceCollectionExtensions
{
    /// <summary>
    /// Adds the AssemblyAI audio-to-text service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="apiKey">AssemblyAI API key, <a href="https://www.assemblyai.com/dashboard">get your API key from the dashboard.</a></param>
    /// <param name="endpoint">The endpoint URL to the AssemblyAI API.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddAssemblyAIAudioToText(
        this IServiceCollection services,
        string apiKey,
        Uri? endpoint = null,
        string serviceId
    )
    {
Verify.NotNull(services);
if (string.IsNullOrWhiteSpace(serviceId))
{
    throw new ArgumentException("Service ID cannot be null or whitespace.", nameof(serviceId));
}
        services.AddKeyedSingleton<IAudioToTextService>(serviceId, (serviceProvider, _)
            => new AssemblyAIAudioToTextService(
                apiKey,
                endpoint,
                HttpClientProvider.GetHttpClient(serviceProvider)
            )
        );

        return services;
    }

    /// <summary>
    /// Adds the AssemblyAI file service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="apiKey">AssemblyAI API key, <a href="https://www.assemblyai.com/dashboard">get your API key from the dashboard.</a></param>
    /// <param name="endpoint">The endpoint URL to the AssemblyAI API.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddAssemblyAIFiles(
        this IServiceCollection services,
        string apiKey,
        Uri? endpoint = null,
        string? serviceId = null
    )
    {
        Verify.NotNull(services);
        services.AddKeyedSingleton(serviceId, (serviceProvider, _) =>
            new AssemblyAIFileService(
                apiKey,
                endpoint,
                HttpClientProvider.GetHttpClient(serviceProvider)
            )
        );

        return services;
    }
}
