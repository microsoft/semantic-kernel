﻿// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Qdrant.Client;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register Qdrant <see cref="VectorStore"/> instances on an <see cref="IServiceCollection"/>.
/// </summary>
public static class QdrantServiceCollectionExtensions
{
    /// <summary>
    /// Register a Qdrant <see cref="VectorStore"/> with the specified service ID and where <see cref="QdrantClient"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStore"/> on.</param>
    /// <param name="options">Optional options to further configure the <see cref="VectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddQdrantVectorStore(this IServiceCollection services, QdrantVectorStoreOptions? options = default, string? serviceId = default)
    {
        // If we are not constructing the QdrantClient, add the IVectorStore as transient, since we
        // cannot make assumptions about how QdrantClient is being managed.
        services.AddKeyedTransient<VectorStore>(
            serviceId,
            (sp, obj) =>
            {
                var qdrantClient = sp.GetRequiredService<QdrantClient>();
                options ??= sp.GetService<QdrantVectorStoreOptions>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                // The client was restored from the DI container, so we do not own it.
                return new QdrantVectorStore(qdrantClient, ownsClient: false, options);
            });

        return services;
    }
    /// <summary>
    /// Register a Qdrant <see cref="VectorStore"/> with the specified service ID and where <see cref="QdrantClient"/> is constructed using the provided parameters.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStore"/> on.</param>
    /// <param name="host">The Qdrant service host name.</param>
    /// <param name="port">The Qdrant service port.</param>
    /// <param name="https">A value indicating whether to use HTTPS for communicating with Qdrant.</param>
    /// <param name="apiKey">The Qdrant service API key.</param>
    /// <param name="options">Optional options to further configure the <see cref="VectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddQdrantVectorStore(this IServiceCollection services, string host, int port = 6334, bool https = false, string? apiKey = default, QdrantVectorStoreOptions? options = default, string? serviceId = default)
    {
        services.AddKeyedSingleton<VectorStore>(
            serviceId,
            (sp, obj) =>
            {
                var qdrantClient = new QdrantClient(host, port, https, apiKey);
                options ??= sp.GetService<QdrantVectorStoreOptions>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                // We created the client, so we own it.
                return new QdrantVectorStore(qdrantClient, ownsClient: true, options);
            });

        return services;
    }

    /// <summary>
    /// Register a Qdrant <see cref="VectorStoreCollection{TKey, TRecord}"/> and <see cref="IVectorSearchable{TRecord}"/> with the specified service ID
    /// and where the Qdrant <see cref="QdrantClient"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStoreCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Optional options to further configure the <see cref="VectorStoreCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    [RequiresDynamicCode("This method is incompatible with NativeAOT, consult the documentation for adding collections in a way that's compatible with NativeAOT.")]
    [RequiresUnreferencedCode("This method is incompatible with trimming, consult the documentation for adding collections in a way that's compatible with NativeAOT.")]
    public static IServiceCollection AddQdrantVectorStoreRecordCollection<TKey, TRecord>(
        this IServiceCollection services,
        string collectionName,
        QdrantCollectionOptions? options = default,
        string? serviceId = default)
        where TKey : notnull
        where TRecord : class
    {
        services.AddKeyedTransient<VectorStoreCollection<TKey, TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                var qdrantClient = sp.GetRequiredService<QdrantClient>();
                options ??= sp.GetService<QdrantCollectionOptions>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                // The client was restored from the DI container, so we do not own it.
                return (new QdrantCollection<TKey, TRecord>(qdrantClient, collectionName, ownsClient: false, options) as VectorStoreCollection<TKey, TRecord>)!;
            });

        AddVectorizedSearch<TKey, TRecord>(services, serviceId);

        return services;
    }

    /// <summary>
    /// Register a Qdrant <see cref="VectorStoreCollection{TKey, TRecord}"/> and <see cref="IVectorSearchable{TRecord}"/> with the specified service ID
    /// and where the Qdrant <see cref="QdrantClient"/> is constructed using the provided parameters.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStoreCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="host">The Qdrant service host name.</param>
    /// <param name="port">The Qdrant service port.</param>
    /// <param name="https">A value indicating whether to use HTTPS for communicating with Qdrant.</param>
    /// <param name="apiKey">The Qdrant service API key.</param>
    /// <param name="options">Optional options to further configure the <see cref="VectorStoreCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    [RequiresDynamicCode("This method is incompatible with NativeAOT, consult the documentation for adding collections in a way that's compatible with NativeAOT.")]
    [RequiresUnreferencedCode("This method is incompatible with trimming, consult the documentation for adding collections in a way that's compatible with NativeAOT.")]
    public static IServiceCollection AddQdrantVectorStoreRecordCollection<TKey, TRecord>(
        this IServiceCollection services,
        string collectionName,
        string host,
        int port = 6334,
        bool https = false,
        string? apiKey = default,
        QdrantCollectionOptions? options = default,
        string? serviceId = default)
        where TKey : notnull
        where TRecord : class
    {
        services.AddKeyedSingleton<VectorStoreCollection<TKey, TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                var qdrantClient = new QdrantClient(host, port, https, apiKey);
                options ??= sp.GetService<QdrantCollectionOptions>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                // We created the client, so we own it.
                return (new QdrantCollection<TKey, TRecord>(qdrantClient, collectionName, ownsClient: true, options) as VectorStoreCollection<TKey, TRecord>)!;
            });

        AddVectorizedSearch<TKey, TRecord>(services, serviceId);

        return services;
    }

    /// <summary>
    /// Also register the <see cref="VectorStoreCollection{TKey, TRecord}"/> with the given <paramref name="serviceId"/> as a <see cref="IVectorSearchable{TRecord}"/>.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="services">The service collection to register on.</param>
    /// <param name="serviceId">The service id that the registrations should use.</param>
    private static void AddVectorizedSearch<TKey, TRecord>(IServiceCollection services, string? serviceId)
        where TKey : notnull
        where TRecord : class
    {
        services.AddKeyedTransient<IVectorSearchable<TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                return sp.GetRequiredKeyedService<VectorStoreCollection<TKey, TRecord>>(serviceId);
            });
    }
}
