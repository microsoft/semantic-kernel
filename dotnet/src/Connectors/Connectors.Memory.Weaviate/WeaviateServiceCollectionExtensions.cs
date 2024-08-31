// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Connectors.Weaviate;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register Weaviate <see cref="IVectorStore"/> instances on an <see cref="IServiceCollection"/>
/// </summary>
public static class WeaviateServiceCollectionExtensions
{
    /// <summary>
    /// Register a Weaviate <see cref="IVectorStore"/> with the specified service ID.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="httpClient">Optional <see cref="HttpClient"/> to be used in <see cref="IVectorStore"/>. If not provided, it will be retrieved from dependency injection container.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddWeaviateVectorStore(
        this IServiceCollection services,
        HttpClient? httpClient = default,
        WeaviateVectorStoreOptions? options = default,
        string? serviceId = default)
    {
        services.AddKeyedTransient<IVectorStore>(
            serviceId,
            (sp, obj) =>
            {
                var selectedHttpClient = HttpClientProvider.GetHttpClient(httpClient, sp);
                var selectedOptions = options ?? sp.GetService<WeaviateVectorStoreOptions>();
                return new WeaviateVectorStore(selectedHttpClient, options);
            });

        return services;
    }

    /// <summary>
    /// Register a Weaviate <see cref="IVectorStore"/> with the specified service ID
    /// and where the <see cref="HttpClient"/> is constructed using the provided <paramref name="endpoint"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="endpoint">Weaviate endpoint.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddWeaviateVectorStore(
        this IServiceCollection services,
        Uri endpoint,
        WeaviateVectorStoreOptions? options = default,
        string? serviceId = default)
    {
        services.AddKeyedSingleton<IVectorStore>(
            serviceId,
            (sp, obj) =>
            {
                var httpClient = HttpClientProvider.GetHttpClient();

                httpClient.BaseAddress = endpoint;

                var selectedOptions = options ?? sp.GetService<WeaviateVectorStoreOptions>();
                return new WeaviateVectorStore(httpClient, options);
            });

        return services;
    }
}
