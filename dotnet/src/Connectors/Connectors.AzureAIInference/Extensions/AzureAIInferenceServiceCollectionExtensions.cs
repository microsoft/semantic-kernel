// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Azure.AI.Inference;
using Azure.Core;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AzureAIInference;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides extension methods for <see cref="IServiceCollection"/> to configure Azure AI Inference connectors.
/// </summary>
public static class AzureAIInferenceServiceCollectionExtensions
{
    /// <summary>
    /// Adds the <see cref="AzureAIInferenceChatCompletionService"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">Target Model Id for endpoints supporting more than one model</param>
    /// <param name="apiKey">API Key</param>
    /// <param name="endpoint">Endpoint / Target URI</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddAzureAIInferenceChatCompletion(
        this IServiceCollection services,
        string? modelId = null,
        string? apiKey = null,
        Uri? endpoint = null,
        HttpClient? httpClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);

        AzureAIInferenceChatCompletionService Factory(IServiceProvider serviceProvider, object? _) =>
            new(modelId,
                apiKey,
                endpoint,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>());

        services.AddKeyedSingleton<IChatCompletionService>(serviceId, (Func<IServiceProvider, object?, AzureAIInferenceChatCompletionService>)Factory);

        return services;
    }

    /// <summary>
    /// Adds the <see cref="AzureAIInferenceChatCompletionService"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">Target Model Id for endpoints supporting more than one model</param>
    /// <param name="credential">Token credential, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="endpoint">Endpoint / Target URI</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddAzureAIInferenceChatCompletion(
        this IServiceCollection services,
        string? modelId,
        TokenCredential credential,
        Uri? endpoint = null,
        HttpClient? httpClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);

        AzureAIInferenceChatCompletionService Factory(IServiceProvider serviceProvider, object? _) =>
            new(modelId,
                credential,
                endpoint,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>());

        services.AddKeyedSingleton<IChatCompletionService>(serviceId, (Func<IServiceProvider, object?, AzureAIInferenceChatCompletionService>)Factory);

        return services;
    }

    /// <summary>
    /// Adds the <see cref="AzureAIInferenceChatCompletionService"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">Azure AI Inference model id</param>
    /// <param name="chatClient"><see cref="ChatCompletionsClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddAzureAIInferenceChatCompletion(this IServiceCollection services,
        string modelId,
        ChatCompletionsClient? chatClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);

        AzureAIInferenceChatCompletionService Factory(IServiceProvider serviceProvider, object? _) =>
            new(modelId, chatClient ?? serviceProvider.GetRequiredService<ChatCompletionsClient>(), serviceProvider.GetService<ILoggerFactory>());

        services.AddKeyedSingleton<IChatCompletionService>(serviceId, (Func<IServiceProvider, object?, AzureAIInferenceChatCompletionService>)Factory);

        return services;
    }
}
