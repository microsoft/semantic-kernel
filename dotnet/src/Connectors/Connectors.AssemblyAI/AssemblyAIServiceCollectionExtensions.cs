// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Options;
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
        string? serviceId = null)
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
        string? serviceId = null)
    {
        Verify.NotNull(services);
        var optionsBuilder = services.AddOptions<AssemblyAIAudioToTextServiceOptions>();
        optionsBuilder.Configure(options =>
        {
            options.ApiKey = apiKey;
            options.Endpoint = endpoint;
        });
        ValidateOptions(optionsBuilder);
        AddService(services, serviceId);
        return services;
    }

    /// <summary>
    /// Adds the AssemblyAI audio-to-text service to the kernel.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="configuration">Configuration to bind to <see cref="AssemblyAIAudioToTextServiceOptions"/></param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddAssemblyAIAudioToText(
        this IKernelBuilder builder,
        IConfiguration configuration,
        string? serviceId = null)
    {
        Verify.NotNull(builder);
        AddAssemblyAIAudioToText(builder.Services, configuration, serviceId);
        return builder;
    }

    /// <summary>
    /// Adds the AssemblyAI audio-to-text service to the kernel.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="configuration">Configuration to bind to <see cref="AssemblyAIAudioToTextServiceOptions"/></param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddAssemblyAIAudioToText(
        this IServiceCollection services,
        IConfiguration configuration,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        var optionsBuilder = services.AddOptions<AssemblyAIAudioToTextServiceOptions>();
        optionsBuilder.Bind(configuration);
        ValidateOptions(optionsBuilder);
        AddService(services, serviceId);
        return services;
    }

    /// <summary>
    /// Adds the AssemblyAI audio-to-text service to the kernel.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="configureOptions">Action to configure <see cref="AssemblyAIAudioToTextServiceOptions"/></param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddAssemblyAIAudioToText(
        this IKernelBuilder builder,
        Action<AssemblyAIAudioToTextServiceOptions> configureOptions,
        string? serviceId = null)
    {
        Verify.NotNull(builder);
        AddAssemblyAIAudioToText(builder.Services, configureOptions, serviceId);
        return builder;
    }

    /// <summary>
    /// Adds the AssemblyAI audio-to-text service to the kernel.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="configureOptions">Action to configure <see cref="AssemblyAIAudioToTextServiceOptions"/></param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddAssemblyAIAudioToText(
        this IServiceCollection services,
        Action<AssemblyAIAudioToTextServiceOptions> configureOptions,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        var optionsBuilder = services.AddOptions<AssemblyAIAudioToTextServiceOptions>();
        optionsBuilder.Configure(configureOptions);
        ValidateOptions(optionsBuilder);
        AddService(services, serviceId);
        return services;
    }

    /// <summary>
    /// Adds the AssemblyAI audio-to-text service to the kernel.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="configureOptions">Action to configure <see cref="AssemblyAIAudioToTextServiceOptions"/></param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddAssemblyAIAudioToText(
        this IServiceCollection services,
        Action<AssemblyAIAudioToTextServiceOptions, ServiceProvider> configureOptions,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        var optionsBuilder = services.AddOptions<AssemblyAIAudioToTextServiceOptions>();
        optionsBuilder.Configure(configureOptions);
        ValidateOptions(optionsBuilder);
        AddService(services, serviceId);
        return services;
    }

    /// <summary>
    /// Adds the AssemblyAI audio-to-text service to the kernel.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="configureOptions">Action to configure <see cref="AssemblyAIAudioToTextServiceOptions"/></param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddAssemblyAIAudioToText(
        this IKernelBuilder builder,
        Action<AssemblyAIAudioToTextServiceOptions, ServiceProvider> configureOptions,
        string? serviceId = null)
    {
        Verify.NotNull(builder);
        AddAssemblyAIAudioToText(builder.Services, configureOptions, serviceId);
        return builder;
    }

    private static void AddService(
        IServiceCollection services,
        string? serviceId = null
    )
    {
        services.AddKeyedSingleton<IAudioToTextService>(serviceId, (serviceProvider, _) =>
        {
            var options = serviceProvider.GetRequiredService<IOptions<AssemblyAIAudioToTextServiceOptions>>().Value;
            {
                var httpClient = HttpClientProvider.GetHttpClient(serviceProvider);
                if (!string.IsNullOrEmpty(options.Endpoint))
                {
                    httpClient.BaseAddress = new Uri(options.Endpoint!);
                }

                var service = new AssemblyAIAudioToTextService(
                    options.ApiKey,
                    httpClient
                );

                return service;
            }
        });
    }

    private static void ValidateOptions(OptionsBuilder<AssemblyAIAudioToTextServiceOptions> optionsBuilder)
    {
        optionsBuilder.Validate(
            options => !string.IsNullOrWhiteSpace(options.ApiKey),
            "AssemblyAI API key must be configured."
        );
    }
}
