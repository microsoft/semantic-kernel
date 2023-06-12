// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.SemanticKernel.Connectors.Memory.Qdrant;

#pragma warning disable IDE0130
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Provides extension methods for the <see cref="KernelBuilder"/> class to configure Qdrant memory connector.
/// </summary>
public static class QdrantKernelBuilderExtensions
{
    /// <summary>
    /// Registers Qdrant memory connector.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance.</param>
    /// <param name="endpoint">The Qdrant Vector Database endpoint.</param>
    /// <param name="vectorSize">The size of the vectors.</param>
    /// <returns>Self instance</returns>
    public static KernelBuilder WithQdrantMemoryStore(this KernelBuilder builder,
        string endpoint,
        int vectorSize)
    {
        builder.WithMemoryStorage((parameters) =>
        {
            var client = new QdrantVectorDbClient(
                HttpClientProvider.GetHttpClient(parameters.Config, null, parameters.Logger),
                vectorSize,
                endpoint,
                parameters.Logger);

            return new QdrantMemoryStore(client, parameters.Logger);
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
    public static KernelBuilder WithQdrantMemoryStore(this KernelBuilder builder,
        HttpClient httpClient,
        int vectorSize,
        string? endpoint = null)
    {
        builder.WithMemoryStorage((parameters) =>
        {
            var client = new QdrantVectorDbClient(
                HttpClientProvider.GetHttpClient(parameters.Config, httpClient, parameters.Logger),
                vectorSize,
                endpoint,
                parameters.Logger);

            return new QdrantMemoryStore(client, parameters.Logger);
        });

        return builder;
    }
}
