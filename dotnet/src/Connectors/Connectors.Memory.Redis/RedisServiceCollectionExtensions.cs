// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Redis;
using StackExchange.Redis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register Redis <see cref="IVectorStore"/> instances on an <see cref="IServiceCollection"/>.
/// </summary>
public static class RedisServiceCollectionExtensions
{
    /// <summary>
    /// Registers a Redis <see cref="IVectorStore"/>, retrieving the Redis <see cref="IDatabase"/> from the dependency injection container.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddRedisVectorStore(
        this IServiceCollection serviceCollection,
        RedisVectorStoreOptions? options = default,
        // If we are not constructing the ConnectionMultiplexer, add the IVectorStore as transient, since we
        // cannot make assumptions about how IDatabase is being managed.
        ServiceLifetime lifetime = ServiceLifetime.Transient)
        => AddKeyedRedisVectorStore(serviceCollection, serviceKey: null, options, lifetime);

    /// <summary>
    /// Registers a keyed Redis <see cref="IVectorStore"/>, retrieving the Redis <see cref="IDatabase"/> from the dependency injection container.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddKeyedRedisVectorStore(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        RedisVectorStoreOptions? options = default,
        // If we are not constructing the ConnectionMultiplexer, add the IVectorStore as transient, since we
        // cannot make assumptions about how IDatabase is being managed.
        ServiceLifetime lifetime = ServiceLifetime.Transient)
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStore),
                serviceKey,
                (serviceProvider, _) => new RedisVectorStore(
                    serviceProvider.GetRequiredService<IDatabase>(),
                    options ?? serviceProvider.GetService<RedisVectorStoreOptions>()),
                lifetime));

        return serviceCollection;
    }

    /// <summary>
    /// Registers a Redis <see cref="IVectorStore"/>, using the provided <paramref name="redisConnectionConfiguration"/>.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="redisConnectionConfiguration">The Redis connection configuration string. If not provided, an <see cref="IDatabase"/> instance will be requested from the dependency injection container.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddRedisVectorStore(
        this IServiceCollection serviceCollection,
        string redisConnectionConfiguration,
        RedisVectorStoreOptions? options = default,
        // If we are constructing the ConnectionMultiplexer, add the IVectorStore as singleton, since we are managing the lifetime
        // of the ConnectionMultiplexer, and the recommendation from StackExchange.Redis is to share the ConnectionMultiplexer.
        ServiceLifetime lifetime = ServiceLifetime.Transient)
        => AddKeyedRedisVectorStore(serviceCollection, serviceKey: null, redisConnectionConfiguration, options, lifetime);

    /// <summary>
    /// Registers a keyed Redis <see cref="IVectorStore"/>, using the provided <paramref name="redisConnectionConfiguration"/>.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="redisConnectionConfiguration">The Redis connection configuration string. If not provided, an <see cref="IDatabase"/> instance will be requested from the dependency injection container.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddKeyedRedisVectorStore(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        string redisConnectionConfiguration,
        RedisVectorStoreOptions? options = default,
        // If we are constructing the ConnectionMultiplexer, add the IVectorStore as singleton, since we are managing the lifetime
        // of the ConnectionMultiplexer, and the recommendation from StackExchange.Redis is to share the ConnectionMultiplexer.
        ServiceLifetime lifetime = ServiceLifetime.Transient)
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStore),
                serviceKey,
                (serviceProvider, _) => new RedisVectorStore(
                    ConnectionMultiplexer.Connect(redisConnectionConfiguration).GetDatabase(),
                    options ?? serviceProvider.GetService<RedisVectorStoreOptions>()),
                lifetime));

        return serviceCollection;
    }

    /// <summary>
    /// Registers a Redis <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>, retrieving the Redis <see cref="IDatabase"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddRedisHashSetVectorStoreRecordCollection<TRecord>(
        this IServiceCollection serviceCollection,
        string collectionName,
        RedisHashSetVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Transient)
        => AddKeyedRedisHashSetVectorStoreRecordCollection(serviceCollection, serviceKey: null, collectionName, options, lifetime);

    /// <summary>
    /// Registers a keyed Redis <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>, retrieving the Redis <see cref="IDatabase"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddKeyedRedisHashSetVectorStoreRecordCollection<TRecord>(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        string collectionName,
        RedisHashSetVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Transient)
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStoreRecordCollection<string, TRecord>),
                serviceKey,
                (serviceProvider, _) => new RedisHashSetVectorStoreRecordCollection<TRecord>(
                    serviceProvider.GetRequiredService<IDatabase>(),
                    collectionName,
                    options ?? serviceProvider.GetService<RedisHashSetVectorStoreRecordCollectionOptions<TRecord>>()),
                lifetime));

        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorizedSearch<TRecord>),
                serviceKey,
                static (serviceProvider, serviceKey) => serviceProvider.GetRequiredKeyedService<IVectorStoreRecordCollection<string, TRecord>>(serviceKey),
                lifetime));

        return serviceCollection;
    }

    /// <summary>
    /// Registers a Redis <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>, using the provided <paramref name="redisConnectionConfiguration"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="redisConnectionConfiguration">The Redis connection configuration string.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddRedisHashSetVectorStoreRecordCollection<TRecord>(
        this IServiceCollection serviceCollection,
        string collectionName,
        string redisConnectionConfiguration,
        RedisHashSetVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    => AddKeyedRedisHashSetVectorStoreRecordCollection(serviceCollection, serviceKey: null, collectionName, redisConnectionConfiguration, options, lifetime);

    /// <summary>
    /// Registers a keyed Redis <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>, using the provided <paramref name="redisConnectionConfiguration"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="redisConnectionConfiguration">The Redis connection configuration string.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddKeyedRedisHashSetVectorStoreRecordCollection<TRecord>(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        string collectionName,
        string redisConnectionConfiguration,
        RedisHashSetVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStoreRecordCollection<string, TRecord>),
                serviceKey,
                (serviceProvider, _) => new RedisHashSetVectorStoreRecordCollection<TRecord>(
                    ConnectionMultiplexer.Connect(redisConnectionConfiguration).GetDatabase(),
                    collectionName,
                    options ?? serviceProvider.GetService<RedisHashSetVectorStoreRecordCollectionOptions<TRecord>>()),
                lifetime));

        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorizedSearch<TRecord>),
                serviceKey,
                static (serviceProvider, serviceKey) => serviceProvider.GetRequiredKeyedService<IVectorStoreRecordCollection<string, TRecord>>(serviceKey),
                lifetime));

        return serviceCollection;
    }

    /// <summary>
    /// Registers a Redis <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>, retrieving the Redis <see cref="IDatabase"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddRedisJsonVectorStoreRecordCollection<TRecord>(
        this IServiceCollection serviceCollection,
        string collectionName,
        RedisJsonVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Transient)
        => AddKeyedRedisJsonVectorStoreRecordCollection(serviceCollection, serviceKey: null, collectionName, options, lifetime);

    /// <summary>
    /// Registers a keyed Redis <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>, retrieving the Redis <see cref="IDatabase"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddKeyedRedisJsonVectorStoreRecordCollection<TRecord>(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        string collectionName,
        RedisJsonVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Transient)
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStoreRecordCollection<string, TRecord>),
                serviceKey,
                (serviceProvider, _) => new RedisJsonVectorStoreRecordCollection<TRecord>(
                    serviceProvider.GetRequiredService<IDatabase>(),
                    collectionName,
                    options ?? serviceProvider.GetService<RedisJsonVectorStoreRecordCollectionOptions<TRecord>>()),
                lifetime));

        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorizedSearch<TRecord>),
                serviceKey,
                static (serviceProvider, serviceKey) => serviceProvider.GetRequiredKeyedService<IVectorStoreRecordCollection<string, TRecord>>(serviceKey),
                lifetime));

        return serviceCollection;
    }

    /// <summary>
    /// Registers a Redis <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> using the provided <paramref name="redisConnectionConfiguration"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="redisConnectionConfiguration">The Redis connection configuration string.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddRedisJsonVectorStoreRecordCollection<TRecord>(
        this IServiceCollection serviceCollection,
        string collectionName,
        string redisConnectionConfiguration,
        RedisJsonVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        => AddKeyedRedisJsonVectorStoreRecordCollection(serviceCollection, serviceKey: null, collectionName, redisConnectionConfiguration, options, lifetime);

    /// <summary>
    /// Registers a keyed Redis <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> using the provided <paramref name="redisConnectionConfiguration"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="redisConnectionConfiguration">The Redis connection configuration string.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddKeyedRedisJsonVectorStoreRecordCollection<TRecord>(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        string collectionName,
        string redisConnectionConfiguration,
        RedisJsonVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStoreRecordCollection<string, TRecord>),
                serviceKey,
                (serviceProvider, _) => new RedisJsonVectorStoreRecordCollection<TRecord>(
                    ConnectionMultiplexer.Connect(redisConnectionConfiguration).GetDatabase(),
                    collectionName,
                    options ?? serviceProvider.GetService<RedisJsonVectorStoreRecordCollectionOptions<TRecord>>()),
                lifetime));

        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorizedSearch<TRecord>),
                serviceKey,
                static (serviceProvider, serviceKey) => serviceProvider.GetRequiredKeyedService<IVectorStoreRecordCollection<string, TRecord>>(serviceKey),
                lifetime));

        return serviceCollection;
    }
}
