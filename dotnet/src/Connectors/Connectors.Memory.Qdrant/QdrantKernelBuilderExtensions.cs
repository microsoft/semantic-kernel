// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Net.Http;
using Microsoft.SemanticKernel.Connectors.Memory.Qdrant;

#pragma warning disable IDE0130
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Provides extension methods for the <see cref="KernelBuilder"/> class to configure Qdrant memory connector.
/// </summary>
[Obsolete("Memory functionality will be placed in separate Microsoft.SemanticKernel.Plugins.Memory package. This will be removed in a future release.")]
[EditorBrowsable(EditorBrowsableState.Never)]
public static class QdrantKernelBuilderExtensions
{
    /// <summary>
    /// Registers Qdrant memory connector.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance.</param>
    /// <param name="endpoint">The Qdrant Vector Database endpoint.</param>
    /// <param name="vectorSize">The size of the vectors.</param>
    /// <returns>Self instance</returns>
    [Obsolete("Memory functionality will be placed in separate Microsoft.SemanticKernel.Plugins.Memory package. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public static KernelBuilder WithQdrantMemoryStore(this KernelBuilder builder,
        string endpoint,
        int vectorSize)
    {
        builder.WithMemoryStorage((loggerFactory, httpHandlerFactory) =>
        {
            var client = new QdrantVectorDbClient(
                HttpClientProvider.GetHttpClient(httpHandlerFactory, null, loggerFactory),
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
    /// <param name="builder">The <see cref="KernelBuilder"/> instance</param>
    /// <param name="httpClient">The optional <see cref="HttpClient"/> instance used for making HTTP requests.</param>
    /// <param name="vectorSize">The size of the vectors.</param>
    /// <param name="endpoint">The Qdrant Vector Database endpoint. If not specified, the base address of the HTTP client is used.</param>
    /// <returns>Self instance</returns>
    [Obsolete("Memory functionality will be placed in separate Microsoft.SemanticKernel.Plugins.Memory package. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public static KernelBuilder WithQdrantMemoryStore(this KernelBuilder builder,
        HttpClient httpClient,
        int vectorSize,
        string? endpoint = null)
    {
        builder.WithMemoryStorage((loggerFactory, httpHandlerFactory) =>
        {
            var client = new QdrantVectorDbClient(
                HttpClientProvider.GetHttpClient(httpHandlerFactory, httpClient, loggerFactory),
                vectorSize,
                endpoint,
                loggerFactory);

            return new QdrantMemoryStore(client, loggerFactory);
        });

        return builder;
    }
}
