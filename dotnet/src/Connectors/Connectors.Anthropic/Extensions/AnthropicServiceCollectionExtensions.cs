// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using Anthropic;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Anthropic.Services;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.TextGeneration;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods for registering Anthropic services in the dependency injection container.
/// </summary>
[Experimental("SKEXP0001")]
public static class AnthropicServiceCollectionExtensions
{
    #region IServiceCollection Extensions

    /// <summary>
    /// Adds Anthropic chat completion service to the service collection.
    /// </summary>
    /// <param name="services">The service collection to add the service to.</param>
    /// <param name="modelId">The Anthropic model ID (e.g., claude-sonnet-4-20250514).</param>
    /// <param name="apiKey">The API key for authentication.</param>
    /// <param name="baseUrl">The base URL for the API endpoint. Defaults to https://api.anthropic.com.</param>
    /// <param name="endpointId">Optional endpoint identifier for telemetry.</param>
    /// <param name="serviceId">Optional service identifier for keyed registration.</param>
    /// <returns>The service collection for chaining.</returns>
    public static IServiceCollection AddAnthropicChatCompletion(
        this IServiceCollection services,
        string modelId,
        string apiKey,
        Uri? baseUrl = null,
        string? endpointId = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        // Register the concrete service as a keyed singleton, then alias the interfaces to it.
        // This ensures a single instance is shared across IChatCompletionService and ITextGenerationService.
        services.AddKeyedSingleton<AnthropicChatCompletionService>(serviceId, (serviceProvider, _) =>
            new AnthropicChatCompletionService(
                modelId,
                apiKey,
                baseUrl,
                endpointId,
                HttpClientProvider.GetHttpClient(serviceProvider),
                serviceProvider.GetService<ILoggerFactory>()));

        services.AddKeyedSingleton<IChatCompletionService>(serviceId,
            (serviceProvider, key) => serviceProvider.GetRequiredKeyedService<AnthropicChatCompletionService>(key));
        services.AddKeyedSingleton<ITextGenerationService>(serviceId,
            (serviceProvider, key) => serviceProvider.GetRequiredKeyedService<AnthropicChatCompletionService>(key));

        return services;
    }

    /// <summary>
    /// Adds Anthropic chat completion service to the service collection using an existing AnthropicClient.
    /// </summary>
    /// <param name="services">The service collection to add the service to.</param>
    /// <param name="modelId">The Anthropic model ID (e.g., claude-sonnet-4-20250514).</param>
    /// <param name="anthropicClient">Pre-configured <see cref="AnthropicClient"/>. If null, will be resolved from the service provider.</param>
    /// <param name="serviceId">Optional service identifier for keyed registration.</param>
    /// <returns>The service collection for chaining.</returns>
    public static IServiceCollection AddAnthropicChatCompletion(
        this IServiceCollection services,
        string modelId,
        AnthropicClient? anthropicClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);

        // Register the concrete service as a keyed singleton, then alias the interfaces to it.
        // This ensures a single instance is shared across IChatCompletionService and ITextGenerationService.
        services.AddKeyedSingleton<AnthropicChatCompletionService>(serviceId, (serviceProvider, _) =>
            new AnthropicChatCompletionService(
                modelId,
                anthropicClient ?? serviceProvider.GetRequiredService<AnthropicClient>(),
                serviceProvider.GetService<ILoggerFactory>()));

        services.AddKeyedSingleton<IChatCompletionService>(serviceId,
            (serviceProvider, key) => serviceProvider.GetRequiredKeyedService<AnthropicChatCompletionService>(key));
        services.AddKeyedSingleton<ITextGenerationService>(serviceId,
            (serviceProvider, key) => serviceProvider.GetRequiredKeyedService<AnthropicChatCompletionService>(key));

        return services;
    }

    #endregion

    #region IKernelBuilder Extensions

    /// <summary>
    /// Adds Anthropic chat completion service to the kernel builder.
    /// </summary>
    /// <param name="builder">The kernel builder to add the service to.</param>
    /// <param name="modelId">The Anthropic model ID (e.g., claude-sonnet-4-20250514).</param>
    /// <param name="apiKey">The API key for authentication.</param>
    /// <param name="baseUrl">The base URL for the API endpoint. Defaults to https://api.anthropic.com.</param>
    /// <param name="endpointId">Optional endpoint identifier for telemetry.</param>
    /// <param name="serviceId">Optional service identifier for keyed registration.</param>
    /// <returns>The kernel builder for chaining.</returns>
    public static IKernelBuilder AddAnthropicChatCompletion(
        this IKernelBuilder builder,
        string modelId,
        string apiKey,
        Uri? baseUrl = null,
        string? endpointId = null,
        string? serviceId = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddAnthropicChatCompletion(modelId, apiKey, baseUrl, endpointId, serviceId);
        return builder;
    }

    /// <summary>
    /// Adds Anthropic chat completion service to the kernel builder using an existing AnthropicClient.
    /// </summary>
    /// <param name="builder">The kernel builder to add the service to.</param>
    /// <param name="modelId">The Anthropic model ID (e.g., claude-sonnet-4-20250514).</param>
    /// <param name="anthropicClient">Pre-configured <see cref="AnthropicClient"/>. If null, will be resolved from the service provider.</param>
    /// <param name="serviceId">Optional service identifier for keyed registration.</param>
    /// <returns>The kernel builder for chaining.</returns>
    public static IKernelBuilder AddAnthropicChatCompletion(
        this IKernelBuilder builder,
        string modelId,
        AnthropicClient? anthropicClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddAnthropicChatCompletion(modelId, anthropicClient, serviceId);
        return builder;
    }

    #endregion
}
