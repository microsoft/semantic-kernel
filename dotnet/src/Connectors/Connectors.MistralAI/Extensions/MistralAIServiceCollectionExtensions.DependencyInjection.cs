// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.MistralAI;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.Extensions.DependencyInjection;

/// <summary>
/// Extension methods for adding MistralAI embedding generator to a service collection.
/// </summary>
public static class MistralAIServiceCollectionExtensions
{
    /// <summary>
    /// Adds a MistralAI embedding generator service to the service collection.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">The name of the MistralAI modelId.</param>
    /// <param name="apiKey">The API key required for accessing the MistralAI service.</param>
    /// <param name="endpoint">Optional uri endpoint including the port where MistralAI server is hosted. Default is https://api.mistral.ai.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddMistralEmbeddingGenerator(
        this IServiceCollection services,
        string modelId,
        string apiKey,
        Uri? endpoint = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

#pragma warning disable CS0618 // Type or member is obsolete
        return services.AddKeyedSingleton<IEmbeddingGenerator<string, Embedding<float>>>(serviceId, (serviceProvider, _) =>
            new MistralAITextEmbeddingGenerationService(
                modelId,
                apiKey,
                endpoint,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>())
            .AsEmbeddingGenerator());
#pragma warning restore CS0618 // Type or member is obsolete
    }
}
