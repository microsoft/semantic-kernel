// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Memory;
using Milvus.Client;

namespace Microsoft.SemanticKernel.Connectors.Milvus;

/// <summary>
/// Provides extension methods for adding a Milvus <see cref="IMemoryStore"/> to the service collection.
/// </summary>
public static class MilvusMemoryStoreExtensions
{
    /// <summary>
    /// Adds a Milvus <see cref="IMemoryStore"/> to the service collection.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="client">The Milvus client.</param>
    /// <param name="indexName">The name of the index.</param>
    /// <param name="vectorSize">The size of the vectors.</param>
    /// <param name="metricType">The similarity metric type.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddMilvusMemoryStore(
        this IServiceCollection services,
        MilvusClient client,
        string? indexName = null,
        int vectorSize = 1536,
        SimilarityMetricType metricType = SimilarityMetricType.Ip,
        string? serviceId = null) =>
            services.AddKeyedSingleton<IMemoryStore>(serviceId, (provider, _) =>
                new MilvusMemoryStore(provider.GetRequiredService<MilvusClient>(), indexName, vectorSize, metricType));

    /// <summary>
    /// Adds a Milvus <see cref="IMemoryStore"/> to the service collection.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="endpoint">The endpoint of the Milvus server.</param>
    /// <param name="apiKey">The API key for authentication.</param>
    /// <param name="indexName">The name of the index.</param>
    /// <param name="vectorSize">The size of the vectors.</param>
    /// <param name="metricType">The similarity metric type.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddMilvusMemoryStore(
        this IServiceCollection services,
        string endpoint,
        string apiKey,
        string? indexName = null,
        int vectorSize = 1536,
        SimilarityMetricType metricType = SimilarityMetricType.Ip,
        string? serviceId = null)
    {
        services.AddKeyedSingleton(serviceId, (_, _) => new MilvusClient(endpoint, apiKey));
        return services.AddMilvusMemoryStore(endpoint, apiKey, indexName, vectorSize, metricType, serviceId);
    }
}
