// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
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
    /// Register a Redis <see cref="IVectorStore"/> with the specified service ID and where the Redis <see cref="IDatabase"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddRedisVectorStore(this IServiceCollection services, RedisVectorStoreOptions? options = default, string? serviceId = default)
    {
        // If we are not constructing the ConnectionMultiplexer, add the IVectorStore as transient, since we
        // cannot make assumptions about how IDatabase is being managed.
        services.AddKeyedTransient<IVectorStore>(
            serviceId,
            (sp, obj) =>
            {
                var database = sp.GetRequiredService<IDatabase>();
                options ??= sp.GetService<RedisVectorStoreOptions>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return new RedisVectorStore(database, options);
            });

        return services;
    }

    /// <summary>
    /// Register a Redis <see cref="IVectorStore"/> with the specified service ID and where the Redis <see cref="IDatabase"/> is constructed using the provided <paramref name="redisConnectionConfiguration"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="redisConnectionConfiguration">The Redis connection configuration string. If not provided, an <see cref="IDatabase"/> instance will be requested from the dependency injection container.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddRedisVectorStore(this IServiceCollection services, string redisConnectionConfiguration, RedisVectorStoreOptions? options = default, string? serviceId = default)
    {
        // If we are constructing the ConnectionMultiplexer, add the IVectorStore as singleton, since we are managing the lifetime
        // of the ConnectionMultiplexer, and the recommendation from StackExchange.Redis is to share the ConnectionMultiplexer.
        services.AddKeyedSingleton<IVectorStore>(
            serviceId,
            (sp, obj) =>
            {
                var database = ConnectionMultiplexer.Connect(redisConnectionConfiguration).GetDatabase();
                options ??= sp.GetService<RedisVectorStoreOptions>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return new RedisVectorStore(database, options);
            });

        return services;
    }

    /// <summary>
    /// Register a Redis <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> with the specified service ID
    /// and where the Redis <see cref="IDatabase"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddRedisHashSetVectorStoreRecordCollection<TRecord>(
        this IServiceCollection services,
        string collectionName,
        RedisHashSetVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TRecord : notnull
    {
        services.AddKeyedTransient<IVectorStoreRecordCollection<string, TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                var database = sp.GetRequiredService<IDatabase>();
                options ??= sp.GetService<RedisHashSetVectorStoreRecordCollectionOptions<TRecord>>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return new RedisHashSetVectorStoreRecordCollection<string, TRecord>(database, collectionName, options);
            });

        AddVectorizedSearch<TRecord>(services, serviceId);

        return services;
    }

    /// <summary>
    /// Register a Redis <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> with the specified service ID
    /// and where the Redis <see cref="IDatabase"/> is constructed using the provided <paramref name="redisConnectionConfiguration"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="redisConnectionConfiguration">The Redis connection configuration string.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddRedisHashSetVectorStoreRecordCollection<TRecord>(
        this IServiceCollection services,
        string collectionName,
        string redisConnectionConfiguration,
        RedisHashSetVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TRecord : notnull
    {
        services.AddKeyedSingleton<IVectorStoreRecordCollection<string, TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                var database = ConnectionMultiplexer.Connect(redisConnectionConfiguration).GetDatabase();
                options ??= sp.GetService<RedisHashSetVectorStoreRecordCollectionOptions<TRecord>>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return new RedisHashSetVectorStoreRecordCollection<string, TRecord>(database, collectionName, options);
            });

        AddVectorizedSearch<TRecord>(services, serviceId);

        return services;
    }

    /// <summary>
    /// Register a Redis <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> with the specified service ID
    /// and where the Redis <see cref="IDatabase"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddRedisJsonVectorStoreRecordCollection<TRecord>(
        this IServiceCollection services,
        string collectionName,
        RedisJsonVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TRecord : notnull
    {
        services.AddKeyedTransient<IVectorStoreRecordCollection<string, TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                var database = sp.GetRequiredService<IDatabase>();
                options ??= sp.GetService<RedisJsonVectorStoreRecordCollectionOptions<TRecord>>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return new RedisJsonVectorStoreRecordCollection<string, TRecord>(database, collectionName, options);
            });

        AddVectorizedSearch<TRecord>(services, serviceId);

        return services;
    }

    /// <summary>
    /// Register a Redis <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> with the specified service ID
    /// and where the Redis <see cref="IDatabase"/> is constructed using the provided <paramref name="redisConnectionConfiguration"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="redisConnectionConfiguration">The Redis connection configuration string.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddRedisJsonVectorStoreRecordCollection<TRecord>(
        this IServiceCollection services,
        string collectionName,
        string redisConnectionConfiguration,
        RedisJsonVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TRecord : notnull
    {
        services.AddKeyedSingleton<IVectorStoreRecordCollection<string, TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                var database = ConnectionMultiplexer.Connect(redisConnectionConfiguration).GetDatabase();
                options ??= sp.GetService<RedisJsonVectorStoreRecordCollectionOptions<TRecord>>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return new RedisJsonVectorStoreRecordCollection<string, TRecord>(database, collectionName, options);
            });

        AddVectorizedSearch<TRecord>(services, serviceId);

        return services;
    }

    /// <summary>
    /// Also register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> with the given <paramref name="serviceId"/> as a <see cref="IVectorSearch{TRecord}"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="services">The service collection to register on.</param>
    /// <param name="serviceId">The service id that the registrations should use.</param>
    private static void AddVectorizedSearch<TRecord>(IServiceCollection services, string? serviceId) where TRecord : notnull
    {
        services.AddKeyedTransient<IVectorSearch<TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                return sp.GetRequiredKeyedService<IVectorStoreRecordCollection<string, TRecord>>(serviceId);
            });
    }
}
