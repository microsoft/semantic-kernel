// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Chroma;

/// <summary>
/// Extension methods for registering <see cref="ChromaMemoryStore"/>
/// </summary>
public static class ChromaMemoryStoreExtensions
{
    /// <summary>
    /// Adds a Chroma <see cref="IMemoryStore" /> implementation to the service collection.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="endpoint">The endpoint of the Chroma memory store.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddChromaMemoryStore(this IServiceCollection services, string endpoint, string? serviceId = null) =>
        services.AddKeyedSingleton<IMemoryStore>(serviceId, (provider, _) => new ChromaMemoryStore(
            HttpClientProvider.GetHttpClient(provider.GetService<HttpClient>()),
            endpoint,
            provider.GetService<ILoggerFactory>()));
}
