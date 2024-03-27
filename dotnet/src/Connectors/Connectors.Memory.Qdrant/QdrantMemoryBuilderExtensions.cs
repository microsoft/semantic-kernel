// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// Provides extension methods for the <see cref="MemoryBuilder"/> class to configure Qdrant connector.
/// </summary>
public static class QdrantMemoryBuilderExtensions
{
    /// <summary>
    /// Registers Qdrant memory connector.
    /// </summary>
    /// <param name="builder">The <see cref="MemoryBuilder"/> instance.</param>
    /// <param name="vectorSize">The size of the vectors.</param>
    /// <param name="endpoint">The Qdrant Vector Database endpoint.</param>
    /// <param name="serviceId">A local identifier for the given memory store.</param>
    /// <returns>Updated Memory builder including Qdrant memory connector.</returns>
    public static MemoryBuilder WithQdrantMemoryStore(
        this MemoryBuilder builder,
        int vectorSize,
        string? endpoint = null,
        string? serviceId = null)
    {
        builder.Services.AddKeyedSingleton(serviceId, (provider, _) =>
        {
            var client = new QdrantVectorDbClient(
                HttpClientProvider.GetHttpClient(provider.GetService<HttpClient>()),
                vectorSize,
                endpoint,
                provider.GetService<ILoggerFactory>());
            return client;
        });

        builder.Services.AddKeyedSingleton<IMemoryStore, QdrantMemoryStore>(serviceId);

        return builder;
    }
}
