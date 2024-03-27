// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

/// <summary>
/// Extension methods for adding the Weaviate memory store to the service collection.
/// </summary>
public static class WeaviateMemoryStoreExtensions
{
    /// <summary>
    /// Adds the Weaviate memory store implementation to the service collection.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="endpoint">The Weaviate endpoint URL.</param>
    /// <param name="apiKey">The API key for accessing Weaviate.</param>
    /// <param name="apiVersion">The Weaviate API version.</param>
    /// <param name="serviceId">The service ID for the memory store.</param>
    /// <returns>The updated service collection.</returns>
    /// <remarks>The service will attempt to resolve a <see cref="HttpClient"/> or fallback to the provided <paramref name="endpoint"/> value.</remarks>
    /// <exception cref="ArgumentNullException">Thrown if the <paramref name="endpoint"/> is null and no <see cref="HttpClient"/> is provided.</exception>
    public static IServiceCollection AddWeaviateMemoryStore(
        this IServiceCollection services,
        string? endpoint = null,
        string? apiKey = null,
        string? apiVersion = null,
        string? serviceId = null) =>
            services.AddKeyedSingleton<IMemoryStore>(serviceId, (provider, _) =>
            {
                var httpClient = provider.GetService<HttpClient>();
                var loggerFactory = provider.GetService<ILoggerFactory>();
                return httpClient is null
                    ? new WeaviateMemoryStore(endpoint!, apiKey, apiVersion, loggerFactory)
                    : new WeaviateMemoryStore(httpClient, apiKey, endpoint, apiVersion, loggerFactory);
            });
}
