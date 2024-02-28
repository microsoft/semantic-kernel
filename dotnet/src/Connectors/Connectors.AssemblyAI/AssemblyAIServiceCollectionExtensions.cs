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
    /// Adds the AssemblyAI audio-to-text service to the kernel.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="apiKey">AssemblyAI API key, <a href="https://www.assemblyai.com/dashboard">get your API key from the dashboard.</a></param>
    /// <param name="endpoint">The endpoint URL to the AssemblyAI API.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddAssemblyAIAudioToText(
        this IKernelBuilder builder,
        string apiKey,
        string? endpoint = null,
        string? serviceId = null
    )
    {
        Verify.NotNull(builder);
        AddAssemblyAIAudioToText(builder.Services, apiKey, endpoint, serviceId);
        return builder;
    }

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
        string? endpoint = null,
        string? serviceId = null
    )
    {
        Verify.NotNull(services);
        ValidateOptions(apiKey);
        services.AddKeyedSingleton<IAudioToTextService>(serviceId, (serviceProvider, _) =>
        {
            var httpClient = HttpClientProvider.GetHttpClient(serviceProvider);
            if (!string.IsNullOrEmpty(endpoint))
            {
                httpClient.BaseAddress = new Uri(endpoint!);
            }

            var service = new AssemblyAIAudioToTextService(
                apiKey,
                httpClient
            );

            return service;
        });
        return services;
    }

    private static void ValidateOptions(
        string apiKey
    )
    {
        if (string.IsNullOrWhiteSpace(apiKey))
        {
            throw new ArgumentException("AssemblyAI API key must be configured.", nameof(apiKey));
        }
    }
}
