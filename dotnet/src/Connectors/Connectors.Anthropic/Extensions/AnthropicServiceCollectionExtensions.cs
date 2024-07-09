// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Anthropic;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extensions for adding Anthropic generation services to the application.
/// </summary>
public static class AnthropicServiceCollectionExtensions
{
    /// <summary>
    /// Add Anthropic Chat Completion and Text Generation services to the specified service collection.
    /// </summary>
    /// <param name="services">The service collection to add the Anthropic Text Generation service to.</param>
    /// <param name="modelId">The model for chat completion.</param>
    /// <param name="apiKey">The API key for authentication Anthropic API.</param>
    /// <param name="options">Optional options for the anthropic client</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddAnthropicChatCompletion(
        this IServiceCollection services,
        string modelId,
        string apiKey,
        ClientOptions? options = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(modelId);
        Verify.NotNull(apiKey);

        services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
            new AnthropicChatCompletionService(
                modelId: modelId,
                apiKey: apiKey,
                options: options,
                httpClient: HttpClientProvider.GetHttpClient(serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));
        return services;
    }

    /// <summary>
    /// Add Anthropic Chat Completion and Text Generation services to the specified service collection.
    /// </summary>
    /// <param name="services">The service collection to add the Anthropic Text Generation service to.</param>
    /// <param name="modelId">The model for chat completion.</param>
    /// <param name="endpoint">Endpoint for the chat completion model</param>
    /// <param name="options">Options for the anthropic client</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddAnthropicChatCompletion(
        this IServiceCollection services,
        string modelId,
        Uri endpoint,
        ClientOptions options,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(modelId);
        Verify.NotNull(endpoint);
        Verify.NotNull(options);

        services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
            new AnthropicChatCompletionService(
                modelId: modelId,
                endpoint: endpoint,
                options: options,
                httpClient: HttpClientProvider.GetHttpClient(serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));
        return services;
    }
}
