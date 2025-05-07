// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.MistralAI;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods for adding MistralAI embedding generator to a service collection.
/// </summary>
public static partial class MistralAIServiceCollectionExtensions
{
    /// <summary>
    /// Adds a MistralAI embedding generator service to the service collection.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">The name of the MistralAI modelId.</param>
    /// <param name="apiKey">The API key required for accessing the MistralAI service.</param>
    /// <param name="endpoint">Optional uri endpoint including the port where MistralAI server is hosted. Default is https://api.mistral.ai.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have, if supported by the model.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddMistralEmbeddingGenerator(
        this IServiceCollection services,
        string modelId,
        string apiKey,
        Uri? endpoint = null,
        string? serviceId = null,
        int? dimensions = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        return services.AddKeyedSingleton<IEmbeddingGenerator<string, Embedding<float>>>(serviceId, (serviceProvider, _) =>
            new MistralAIEmbeddingGenerator(
                modelId,
                apiKey,
                endpoint,
                dimensions,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>()));
    }
}
