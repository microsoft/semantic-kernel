// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Qdrant.Client;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register Qdrant <see cref="IVectorStore"/> instances on an <see cref="IServiceCollection"/>.
/// </summary>
public static class QdrantServiceCollectionExtensions
{
    /// <summary>
    /// Register a Qdrant <see cref="IVectorStore"/> with the specified service ID and where <see cref="QdrantClient"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddQdrantVectorStore(this IServiceCollection services, QdrantVectorStoreOptions? options = default, string? serviceId = default)
    {
        // If we are not constructing the QdrantClient, add the IVectorStore as transient, since we
        // cannot make assumptions about how QdrantClient is being managed.
        services.AddKeyedTransient<IVectorStore>(
            serviceId,
            (sp, obj) =>
            {
                var qdrantClient = sp.GetRequiredService<QdrantClient>();
                options ??= sp.GetService<QdrantVectorStoreOptions>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return new QdrantVectorStore(qdrantClient, options);
            });

        return services;
    }
    /// <summary>
    /// Register a Qdrant <see cref="IVectorStore"/> with the specified service ID and where <see cref="QdrantClient"/> is constructed using the provided parameters.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="host">The Qdrant service host name.</param>
    /// <param name="port">The Qdrant service port.</param>
    /// <param name="https">A value indicating whether to use HTTPS for communicating with Qdrant.</param>
    /// <param name="apiKey">The Qdrant service API key.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddQdrantVectorStore(this IServiceCollection services, string host, int port = 6334, bool https = false, string? apiKey = default, QdrantVectorStoreOptions? options = default, string? serviceId = default)
    {
        services.AddKeyedSingleton<IVectorStore>(
            serviceId,
            (sp, obj) =>
            {
                var qdrantClient = new QdrantClient(host, port, https, apiKey);
                options ??= sp.GetService<QdrantVectorStoreOptions>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return new QdrantVectorStore(qdrantClient, options);
            });

        return services;
    }

    /// <summary>
    /// Register a Qdrant <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorSearch{TRecord}"/> with the specified service ID
    /// and where the Qdrant <see cref="QdrantClient"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddQdrantVectorStoreRecordCollection<TKey, TRecord>(
        this IServiceCollection services,
        string collectionName,
        QdrantVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TKey : notnull
        where TRecord : notnull
    {
        services.AddKeyedTransient<IVectorStoreRecordCollection<TKey, TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                var qdrantClient = sp.GetRequiredService<QdrantClient>();
                options ??= sp.GetService<QdrantVectorStoreRecordCollectionOptions<TRecord>>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return (new QdrantVectorStoreRecordCollection<TKey, TRecord>(qdrantClient, collectionName, options) as IVectorStoreRecordCollection<TKey, TRecord>)!;
            });

        AddVectorizedSearch<TKey, TRecord>(services, serviceId);

        return services;
    }

    /// <summary>
    /// Register a Qdrant <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorSearch{TRecord}"/> with the specified service ID
    /// and where the Qdrant <see cref="QdrantClient"/> is constructed using the provided parameters.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="host">The Qdrant service host name.</param>
    /// <param name="port">The Qdrant service port.</param>
    /// <param name="https">A value indicating whether to use HTTPS for communicating with Qdrant.</param>
    /// <param name="apiKey">The Qdrant service API key.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddQdrantVectorStoreRecordCollection<TKey, TRecord>(
        this IServiceCollection services,
        string collectionName,
        string host,
        int port = 6334,
        bool https = false,
        string? apiKey = default,
        QdrantVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TKey : notnull
        where TRecord : notnull
    {
        services.AddKeyedSingleton<IVectorStoreRecordCollection<TKey, TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                var qdrantClient = new QdrantClient(host, port, https, apiKey);
                options ??= sp.GetService<QdrantVectorStoreRecordCollectionOptions<TRecord>>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return (new QdrantVectorStoreRecordCollection<TKey, TRecord>(qdrantClient, collectionName, options) as IVectorStoreRecordCollection<TKey, TRecord>)!;
            });

        AddVectorizedSearch<TKey, TRecord>(services, serviceId);

        return services;
    }

    /// <summary>
    /// Also register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> with the given <paramref name="serviceId"/> as a <see cref="IVectorSearch{TRecord}"/>.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="services">The service collection to register on.</param>
    /// <param name="serviceId">The service id that the registrations should use.</param>
    private static void AddVectorizedSearch<TKey, TRecord>(IServiceCollection services, string? serviceId)
        where TKey : notnull
        where TRecord : notnull
    {
        services.AddKeyedTransient<IVectorSearch<TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                return sp.GetRequiredKeyedService<IVectorStoreRecordCollection<TKey, TRecord>>(serviceId);
            });
    }
}
