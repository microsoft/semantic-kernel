// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
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
    /// Add Anthropic Chat Completion to the added in service collection.
    /// </summary>
    /// <param name="services">The target service collection.</param>
    /// <param name="modelId">Model identifier.</param>
    /// <param name="apiKey">API key.</param>
    /// <param name="options">Optional options for the anthropic client</param>
    /// <param name="serviceId">Service identifier.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddAnthropicChatCompletion(
        this IServiceCollection services,
        string modelId,
        string apiKey,
        AnthropicClientOptions? options = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);

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
    /// Add Anthropic Chat Completion to the added in service collection.
    /// </summary>
    /// <param name="services">The target service collection.</param>
    /// <param name="modelId">Model identifier.</param>
    /// <param name="bearerTokenProvider">Bearer token provider.</param>
    /// <param name="endpoint">Vertex AI Anthropic endpoint.</param>
    /// <param name="options">Optional options for the anthropic client</param>
    /// <param name="serviceId">Service identifier.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddAnthropicVertexAIChatCompletion(
        this IServiceCollection services,
        string modelId,
        Func<ValueTask<string>> bearerTokenProvider,
        Uri? endpoint = null,
        VertexAIAnthropicClientOptions? options = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);

        services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
            new AnthropicChatCompletionService(
                modelId: modelId,
                bearerTokenProvider: bearerTokenProvider,
                endpoint: endpoint,
                options: options ?? new VertexAIAnthropicClientOptions(),
                httpClient: HttpClientProvider.GetHttpClient(serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));

        return services;
    }
}
