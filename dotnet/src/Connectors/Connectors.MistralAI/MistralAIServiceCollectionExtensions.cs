// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.MistralAI;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides extension methods for the <see cref="IServiceCollection"/> interface to configure Mistral connectors.
/// </summary>
public static class MistralAIServiceCollectionExtensions
{
    /// <summary>
    /// Adds an Mistral chat completion service with the specified configuration.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">The name of the Mistral modelId.</param>
    /// <param name="apiKey">The API key required for accessing the Mistral service.</param>
    /// <param name="endpoint">Optional  uri endpoint including the port where MistralAI server is hosted. Default is https://api.mistral.ai.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddMistralChatCompletion(
        this IServiceCollection services,
        string modelId,
        string apiKey,
        Uri? endpoint = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(services);

        services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
        {
            var resolvedHttpClient = HttpClientProvider.GetHttpClient(httpClient, serviceProvider);

            if (httpClient == null && serviceProvider?.GetService<HttpClient>() == null)
            {
                if (!resolvedHttpClient.DefaultRequestHeaders.Contains("extra-parameters"))
                {
                    resolvedHttpClient.DefaultRequestHeaders.Add("extra-parameters", "pass-through");
                }
            }

            return new MistralAIChatCompletionService(
                modelId,
                apiKey,
                endpoint,
                resolvedHttpClient,
                serviceProvider?.GetService<ILoggerFactory>());
        });

        return services;
    }

    /// <summary>
    /// Adds an Mistral text embedding generation service with the specified configuration.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">The name of theMistral modelId.</param>
    /// <param name="apiKey">The API key required for accessing the Mistral service.</param>
    /// <param name="endpoint">Optional  uri endpoint including the port where MistralAI server is hosted. Default is https://api.mistral.ai.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddMistralTextEmbeddingGeneration(
        this IServiceCollection services,
        string modelId,
        string apiKey,
        Uri? endpoint = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(services);

        return services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
            new MistralAITextEmbeddingGenerationService(modelId, apiKey, endpoint, HttpClientProvider.GetHttpClient(httpClient, serviceProvider)));
    }
}
