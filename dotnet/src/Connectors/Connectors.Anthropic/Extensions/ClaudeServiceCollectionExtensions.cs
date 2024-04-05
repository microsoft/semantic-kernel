// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Anthropic;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extensions for adding GoogleAI generation services to the application.
/// </summary>
public static class ClaudeServiceCollectionExtensions
{
    /// <summary>
    /// Add Anthropic Claude Chat Completion and Text Generation services to the specified service collection.
    /// </summary>
    /// <param name="services">The service collection to add the Claude Text Generation service to.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="apiKey">The API key for authentication Claude API.</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddClaudeChatCompletion(
        this IServiceCollection services,
        string modelId,
        string apiKey,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(modelId);
        Verify.NotNull(apiKey);

        services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
            new ClaudeChatCompletionService(
                modelId: modelId,
                apiKey: apiKey,
                httpClient: HttpClientProvider.GetHttpClient(serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));
        return services;
    }

    /// <summary>
    /// Add Anthropic Claude Chat Completion and Text Generation services to the specified service collection.
    /// </summary>
    /// <param name="services">The service collection to add the Claude Text Generation service to.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="endpoint">Endpoint for the chat completion model</param>
    /// <param name="requestHandler">A custom request handler to be used for sending HTTP requests</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddClaudeChatCompletion(
        this IServiceCollection services,
        string modelId,
        Uri endpoint,
        Func<HttpRequestMessage, Task>? requestHandler,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(modelId);
        Verify.NotNull(endpoint);

        services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
            new ClaudeChatCompletionService(
                modelId: modelId,
                endpoint: endpoint,
                requestHandler: requestHandler,
                httpClient: HttpClientProvider.GetHttpClient(serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));
        return services;
    }
}
