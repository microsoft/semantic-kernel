// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// Extension methods for adding <see cref="QdrantMemoryStore"/> to the service collection.
/// </summary>
public static class QdrantMemoryStoreExtensions
{
    /// <summary>
    /// Adds the <see cref="QdrantMemoryStore"/> implementation of IMemoryStore to the service collection.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="serviceId">The optional service identifier.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddQdrantMemoryStore(this IServiceCollection services, string? serviceId = null) =>
        services.AddKeyedSingleton<IMemoryStore, QdrantMemoryStore>(serviceId);

    /// <summary>
    /// Adds the <see cref="QdrantMemoryStore"/> implementation of IMemoryStore to the service collection.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="endpoint">The endpoint of the QdrantVectorDbClient.</param>
    /// <param name="vectorSize">The size of the vectors.</param>
    /// <param name="serviceId">The optional service identifier.</param>
    /// <returns>The updated service collection.</returns>
    /// <remarks>This method will also register a <see cref="IQdrantVectorDbClient"/> instance in the container, using either the provided endpoint or a pre-configured <see cref="HttpClient"/>.</remarks>
    /// <exception cref="ArgumentNullException">The <paramref name="endpoint"/> cannot be <c>null</c> when no <c>HttpClient</c> is configured.</exception>
    public static IServiceCollection AddQdrantMemoryStore(
        this IServiceCollection services,
        string? endpoint,
        int vectorSize,
        string? serviceId = null)
    {
        services.AddKeyedSingleton<IQdrantVectorDbClient>(serviceId, (provider, _) =>
        {
            var httpClient = provider.GetService<HttpClient>();
            var loggerFactory = provider.GetService<ILoggerFactory>();

            if (httpClient is null)
            {
                if (endpoint is null)
                {
                    throw new ArgumentNullException(nameof(endpoint), "When no HttpClient is registered the endpoint must be provided");
                }

                return new QdrantVectorDbClient(endpoint, vectorSize, loggerFactory);
            }

            return new QdrantVectorDbClient(httpClient, vectorSize, endpoint, loggerFactory);
        });

        return services.AddQdrantMemoryStore(serviceId);
    }
}
