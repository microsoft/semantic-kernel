// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.MistralAI;

/// <summary>
/// Provides extension methods for the <see cref="IKernelBuilder"/> class to configure Mistral connectors.
/// </summary>
public static class MistralAIKernelBuilderExtensions
{
    /// <summary>
    /// Adds an Mistral chat completion service with the specified configuration.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="model">The name of the Mistral model.</param>
    /// <param name="endpoint">The endpoint URL for the chat completion service.</param>
    /// <param name="apiKey">The API key required for accessing the Mistral service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddMistralChatCompletion(
        this IServiceCollection services,
        string model,
        Uri? endpoint = null,
        string? apiKey = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(model);

        return services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
            new MistralAIChatCompletionService(model, endpoint, apiKey, HttpClientProvider.GetHttpClient(serviceProvider)));
    }

    /// <summary>
    /// Adds an Mistral chat completion service with the specified configuration.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="model">The name of the Mistral model.</param>
    /// <param name="endpoint">The endpoint URL for the chat completion service.</param>
    /// <param name="apiKey">The API key required for accessing the Mistral service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddMistralChatCompletion(
        this IServiceCollection services,
        string model,
        Uri? endpoint = null,
        string? apiKey = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(model);

        return services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
            new MistralAIChatCompletionService(model, endpoint, apiKey, HttpClientProvider.GetHttpClient(httpClient, serviceProvider)));
    }

    /// <summary>
    /// Adds an Mistral text embedding generation service with the specified configuration.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="model">The name of theMistral model.</param>
    /// <param name="endpoint">The endpoint for the text embedding generation service.</param>
    /// <param name="apiKey">The API key required for accessing the Mistral service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddMistralTextEmbeddingGeneration(
        this IKernelBuilder builder,
        string model,
        Uri? endpoint = null,
        string? apiKey = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNull(model);

        builder.Services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
            new MistralAITextEmbeddingGenerationService(model, endpoint, apiKey, HttpClientProvider.GetHttpClient(httpClient, serviceProvider)));

        return builder;
    }

    /// <summary>
    /// Adds an Mistral text embedding generation service with the specified configuration.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="model">The name of theMistral model.</param>
    /// <param name="endpoint">The endpoint for the text embedding generation service.</param>
    /// <param name="apiKey">The API key required for accessing the Mistral service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddMistralTextEmbeddingGeneration(
        this IServiceCollection services,
        string model,
        Uri? endpoint = null,
        string? apiKey = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(model);

        return services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
            new MistralAITextEmbeddingGenerationService(model, endpoint, apiKey, HttpClientProvider.GetHttpClient(serviceProvider)));
    }
}
