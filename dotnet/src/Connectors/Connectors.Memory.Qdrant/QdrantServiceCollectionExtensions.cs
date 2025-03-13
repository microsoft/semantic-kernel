// Copyright (c) Microsoft. All rights reserved.

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
    /// Registers a Qdrant <see cref="IVectorStore"/>, retrieving the <see cref="QdrantClient"/> from the dependency injection container.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddQdrantVectorStore(
        this IServiceCollection serviceCollection,
        QdrantVectorStoreOptions? options = default,
        // If we are not constructing the QdrantClient, add the IVectorStore as transient, since we
        // cannot make assumptions about how QdrantClient is being managed.
        ServiceLifetime lifetime = ServiceLifetime.Transient)
    => AddKeyedQdrantVectorStore(serviceCollection, serviceKey: null, options, lifetime);

    /// <summary>
    /// Registers a keyed Qdrant <see cref="IVectorStore"/>, retrieving the <see cref="QdrantClient"/> from the dependency injection container.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddKeyedQdrantVectorStore(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        QdrantVectorStoreOptions? options = default,
        // If we are not constructing the QdrantClient, add the IVectorStore as transient, since we
        // cannot make assumptions about how QdrantClient is being managed.
        ServiceLifetime lifetime = ServiceLifetime.Transient)
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStore),
                serviceKey,
                (serviceProvider, _) => new QdrantVectorStore(
                    serviceProvider.GetRequiredService<QdrantClient>(),
                    options ?? serviceProvider.GetService<QdrantVectorStoreOptions>()),
                lifetime));

        return serviceCollection;
    }

    /// <summary>
    /// Registers a Qdrant <see cref="IVectorStore"/> using the provided parameters.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="host">The Qdrant service host name.</param>
    /// <param name="port">The Qdrant service port.</param>
    /// <param name="https">A value indicating whether to use HTTPS for communicating with Qdrant.</param>
    /// <param name="apiKey">The Qdrant service API key.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddQdrantVectorStore(
        this IServiceCollection serviceCollection,
        string host,
        int port = 6334,
        bool https = false,
        string? apiKey = default,
        QdrantVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        => AddKeyedQdrantVectorStore(serviceCollection, serviceKey: null, host, port, https, apiKey, options, lifetime);

    /// <summary>
    /// Registers a keyed Qdrant <see cref="IVectorStore"/> using the provided parameters.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="host">The Qdrant service host name.</param>
    /// <param name="port">The Qdrant service port.</param>
    /// <param name="https">A value indicating whether to use HTTPS for communicating with Qdrant.</param>
    /// <param name="apiKey">The Qdrant service API key.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddKeyedQdrantVectorStore(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        string host,
        int port = 6334,
        bool https = false,
        string? apiKey = default,
        QdrantVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStore),
                serviceKey,
                (serviceProvider, _) => new QdrantVectorStore(
                    new QdrantClient(host, port, https, apiKey),
                    options ?? serviceProvider.GetService<QdrantVectorStoreOptions>()),
                lifetime));

        return serviceCollection;
    }

    /// <summary>
    /// Registers a Qdrant <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/>,
    /// retrieving the <see cref="QdrantClient"/> from the dependency injection container.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddQdrantVectorStoreRecordCollection<TKey, TRecord>(
        this IServiceCollection serviceCollection,
        string collectionName,
        QdrantVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Transient)
        where TKey : notnull
        => AddKeyedQdrantVectorStoreRecordCollection<TKey, TRecord>(serviceCollection, serviceKey: null, collectionName, options, lifetime);

    /// <summary>
    /// Registers a keyed Qdrant <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/>,
    /// retrieving the <see cref="QdrantClient"/> from the dependency injection container.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddKeyedQdrantVectorStoreRecordCollection<TKey, TRecord>(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        string collectionName,
        QdrantVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Transient)
        where TKey : notnull
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStoreRecordCollection<TKey, TRecord>),
                serviceKey,
                (serviceProvider, _) => new QdrantVectorStoreRecordCollection<TRecord>(
                    serviceProvider.GetRequiredService<QdrantClient>(),
                    collectionName,
                    options ?? serviceProvider.GetService<QdrantVectorStoreRecordCollectionOptions<TRecord>>()),
                lifetime));

        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorizedSearch<TRecord>),
                serviceKey,
                static (serviceProvider, serviceKey) => serviceProvider.GetRequiredKeyedService<IVectorStoreRecordCollection<TKey, TRecord>>(serviceKey),
                lifetime));
        return serviceCollection;
    }

    /// <summary>
    /// Registers a Qdrant <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/>, using the provided parameters.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="host">The Qdrant service host name.</param>
    /// <param name="port">The Qdrant service port.</param>
    /// <param name="https">A value indicating whether to use HTTPS for communicating with Qdrant.</param>
    /// <param name="apiKey">The Qdrant service API key.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddQdrantVectorStoreRecordCollection<TKey, TRecord>(
        this IServiceCollection serviceCollection,
        string collectionName,
        string host,
        int port = 6334,
        bool https = false,
        string? apiKey = default,
        QdrantVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        => AddKeyedQdrantVectorStoreRecordCollection<TKey, TRecord>(serviceCollection, serviceKey: null, collectionName, host, port, https, apiKey, options, lifetime);

    /// <summary>
    /// Registers a keyed Qdrant <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/>, using the provided parameters.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="host">The Qdrant service host name.</param>
    /// <param name="port">The Qdrant service port.</param>
    /// <param name="https">A value indicating whether to use HTTPS for communicating with Qdrant.</param>
    /// <param name="apiKey">The Qdrant service API key.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddKeyedQdrantVectorStoreRecordCollection<TKey, TRecord>(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        string collectionName,
        string host,
        int port = 6334,
        bool https = false,
        string? apiKey = default,
        QdrantVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStoreRecordCollection<TKey, TRecord>),
                serviceKey,
                (serviceProvider, _) => new QdrantVectorStoreRecordCollection<TRecord>(
                    new QdrantClient(host, port, https, apiKey),
                    collectionName,
                    options ?? serviceProvider.GetService<QdrantVectorStoreRecordCollectionOptions<TRecord>>()),
                lifetime));

        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorizedSearch<TRecord>),
                serviceKey,
                static (serviceProvider, serviceKey) => serviceProvider.GetRequiredKeyedService<IVectorStoreRecordCollection<TKey, TRecord>>(serviceKey),
                lifetime));

        return serviceCollection;
    }
}
