// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

#pragma warning disable SKEXP0001 // IMemoryStore is experimental (but we're obsoleting)

/// <summary>
/// Provides extension methods for the <see cref="MemoryBuilder"/> class to configure Qdrant connector.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and QdrantVectorStore")]
public static class QdrantMemoryBuilderExtensions
{
    /// <summary>
    /// Registers Qdrant memory connector.
    /// </summary>
    /// <param name="builder">The <see cref="MemoryBuilder"/> instance.</param>
    /// <param name="endpoint">The Qdrant Vector Database endpoint.</param>
    /// <param name="vectorSize">The size of the vectors.</param>
    /// <returns>Updated Memory builder including Qdrant memory connector.</returns>
    public static MemoryBuilder WithQdrantMemoryStore(
        this MemoryBuilder builder,
        string endpoint,
        int vectorSize)
    {
        builder.WithMemoryStore((loggerFactory, injectedClient) =>
        {
            var client = new QdrantVectorDbClient(
                HttpClientProvider.GetHttpClient(injectedClient),
                vectorSize,
                endpoint,
                loggerFactory);

            return new QdrantMemoryStore(client, loggerFactory);
        });

        return builder;
    }

    /// <summary>
    /// Registers Qdrant memory connector.
    /// </summary>
    /// <param name="builder">The <see cref="MemoryBuilder"/> instance.</param>
    /// <param name="httpClient">The optional <see cref="HttpClient"/> instance used for making HTTP requests.</param>
    /// <param name="vectorSize">The size of the vectors.</param>
    /// <param name="endpoint">The Qdrant Vector Database endpoint. If not specified, the base address of the HTTP client is used.</param>
    /// <returns>Updated Memory builder including Qdrant memory connector.</returns>
    public static MemoryBuilder WithQdrantMemoryStore(
        this MemoryBuilder builder,
        HttpClient httpClient,
        int vectorSize,
        string? endpoint = null)
    {
        builder.WithMemoryStore((loggerFactory, injectedClient) =>
        {
            var client = new QdrantVectorDbClient(
                HttpClientProvider.GetHttpClient(httpClient ?? injectedClient),
                vectorSize,
                endpoint,
                loggerFactory);

            return new QdrantMemoryStore(client, loggerFactory);
        });

        return builder;
    }
}
