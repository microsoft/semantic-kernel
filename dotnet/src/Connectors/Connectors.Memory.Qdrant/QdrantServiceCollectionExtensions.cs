// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Data;
using Qdrant.Client;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// Extension methods to register Qdrant <see cref="IVectorStore"/> instances on an <see cref="IServiceCollection"/>.
/// </summary>
public static class QdrantServiceCollectionExtensions
{
    /// <summary>
    /// Register a Qdrant <see cref="IVectorStore"/> with the specified service ID.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="host">The Qdrant service host name.</param>
    /// <param name="port">The Qdrant service port.</param>
    /// <param name="https">A value indicating whether to use HTTPS for communicating with Qdrant.</param>
    /// <param name="apiKey">The Qdrant service API key.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <returns>The kernel builder.</returns>
    public static IServiceCollection AddQdrantVectorStore(this IServiceCollection services, string? host = default, int port = 6334, bool https = false, string? apiKey = default, string? serviceId = default, QdrantVectorStoreOptions? options = default)
    {
        services.AddKeyedTransient<IVectorStore>(
            serviceId,
            (sp, obj) =>
            {
                var qdrantClient = host == null ? sp.GetRequiredService<QdrantClient>() : new QdrantClient(host, port, https, apiKey);
                var selectedOptions = options ?? sp.GetService<QdrantVectorStoreOptions>();

                return new QdrantVectorStore(
                    qdrantClient,
                    selectedOptions);
            });

        return services;
    }
}
