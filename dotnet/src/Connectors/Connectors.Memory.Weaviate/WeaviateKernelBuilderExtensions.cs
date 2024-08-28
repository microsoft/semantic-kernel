// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

/// <summary>
/// Extension methods to register Weaviate <see cref="IVectorStore"/> instances on the <see cref="IKernelBuilder"/>.
/// </summary>
public static class WeaviateKernelBuilderExtensions
{
    /// <summary>
    /// Register a Weaviate <see cref="IVectorStore"/> with the specified service ID.
    /// </summary>
    /// <param name="builder">The builder to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="httpClient">Optional <see cref="HttpClient"/> to be used in <see cref="IVectorStore"/>. If not provided, it will be retrieved from dependency injection container.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddWeaviateVectorStore(
        this IKernelBuilder builder,
        HttpClient? httpClient = default,
        WeaviateVectorStoreOptions? options = default,
        string? serviceId = default)
    {
        builder.Services.AddWeaviateVectorStore(httpClient, options, serviceId);
        return builder;
    }

    /// <summary>
    /// Register a Weaviate <see cref="IVectorStore"/> with the specified service ID
    /// and where the <see cref="HttpClient"/> is constructed using the provided <paramref name="endpoint"/>.
    /// </summary>
    /// <param name="builder">The builder to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="endpoint">Weaviate endpoint.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddWeaviateVectorStore(
        this IKernelBuilder builder,
        Uri endpoint,
        WeaviateVectorStoreOptions? options = default,
        string? serviceId = default)
    {
        builder.Services.AddWeaviateVectorStore(endpoint, options, serviceId);
        return builder;
    }
}
