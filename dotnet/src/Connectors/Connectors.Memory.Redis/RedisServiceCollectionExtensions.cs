// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Redis;
using StackExchange.Redis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register Redis <see cref="VectorStore"/> instances on an <see cref="IServiceCollection"/>.
/// </summary>
public static class RedisServiceCollectionExtensions
{
    /// <summary>
    /// Register a Redis <see cref="VectorStore"/> with the specified service ID and where the Redis <see cref="IDatabase"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStore"/> on.</param>
    /// <param name="options">Optional options to further configure the <see cref="VectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    [RequiresUnreferencedCode("The Redis provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The Redis provider is currently incompatible with NativeAOT.")]
    public static IServiceCollection AddRedisVectorStore(this IServiceCollection services, RedisVectorStoreOptions? options = default, string? serviceId = default)
    {
        // If we are not constructing the ConnectionMultiplexer, add the IVectorStore as transient, since we
        // cannot make assumptions about how IDatabase is being managed.
        services.AddKeyedTransient<VectorStore>(
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
    /// Register a Redis <see cref="VectorStore"/> with the specified service ID and where the Redis <see cref="IDatabase"/> is constructed using the provided <paramref name="redisConnectionConfiguration"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStore"/> on.</param>
    /// <param name="redisConnectionConfiguration">The Redis connection configuration string. If not provided, an <see cref="IDatabase"/> instance will be requested from the dependency injection container.</param>
    /// <param name="options">Optional options to further configure the <see cref="VectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    [RequiresUnreferencedCode("The Redis provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The Redis provider is currently incompatible with NativeAOT.")]
    public static IServiceCollection AddRedisVectorStore(this IServiceCollection services, string redisConnectionConfiguration, RedisVectorStoreOptions? options = default, string? serviceId = default)
    {
        // If we are constructing the ConnectionMultiplexer, add the IVectorStore as singleton, since we are managing the lifetime
        // of the ConnectionMultiplexer, and the recommendation from StackExchange.Redis is to share the ConnectionMultiplexer.
        services.AddKeyedSingleton<VectorStore>(
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
    /// Register a Redis <see cref="VectorStoreCollection{TKey, TRecord}"/> with the specified service ID
    /// and where the Redis <see cref="IDatabase"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStoreCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Optional options to further configure the <see cref="VectorStoreCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    [RequiresDynamicCode("This method is incompatible with NativeAOT, consult the documentation for adding collections in a way that's compatible with NativeAOT.")]
    [RequiresUnreferencedCode("This method is incompatible with trimming, consult the documentation for adding collections in a way that's compatible with NativeAOT.")]
    public static IServiceCollection AddRedisHashSetVectorStoreRecordCollection<TRecord>(
        this IServiceCollection services,
        string collectionName,
        RedisHashSetCollectionOptions? options = default,
        string? serviceId = default)
        where TRecord : class
    {
        services.AddKeyedTransient<VectorStoreCollection<string, TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                var database = sp.GetRequiredService<IDatabase>();
                options ??= sp.GetService<RedisHashSetCollectionOptions>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return new RedisHashSetCollection<string, TRecord>(database, collectionName, options);
            });

        AddVectorizedSearch<TRecord>(services, serviceId);

        return services;
    }

    /// <summary>
    /// Register a Redis <see cref="VectorStoreCollection{TKey, TRecord}"/> with the specified service ID
    /// and where the Redis <see cref="IDatabase"/> is constructed using the provided <paramref name="redisConnectionConfiguration"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStoreCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="redisConnectionConfiguration">The Redis connection configuration string.</param>
    /// <param name="options">Optional options to further configure the <see cref="VectorStoreCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    [RequiresDynamicCode("This method is incompatible with NativeAOT, consult the documentation for adding collections in a way that's compatible with NativeAOT.")]
    [RequiresUnreferencedCode("This method is incompatible with trimming, consult the documentation for adding collections in a way that's compatible with NativeAOT.")]
    public static IServiceCollection AddRedisHashSetVectorStoreRecordCollection<TRecord>(
        this IServiceCollection services,
        string collectionName,
        string redisConnectionConfiguration,
        RedisHashSetCollectionOptions? options = default,
        string? serviceId = default)
        where TRecord : class
    {
        services.AddKeyedSingleton<VectorStoreCollection<string, TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                var database = ConnectionMultiplexer.Connect(redisConnectionConfiguration).GetDatabase();
                options ??= sp.GetService<RedisHashSetCollectionOptions>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return new RedisHashSetCollection<string, TRecord>(database, collectionName, options);
            });

        AddVectorizedSearch<TRecord>(services, serviceId);

        return services;
    }

    /// <summary>
    /// Register a Redis <see cref="VectorStoreCollection{TKey, TRecord}"/> with the specified service ID
    /// and where the Redis <see cref="IDatabase"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStoreCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Optional options to further configure the <see cref="VectorStoreCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    [RequiresDynamicCode("This method is incompatible with NativeAOT, consult the documentation for adding collections in a way that's compatible with NativeAOT.")]
    [RequiresUnreferencedCode("This method is incompatible with trimming, consult the documentation for adding collections in a way that's compatible with NativeAOT.")]
    public static IServiceCollection AddRedisJsonVectorStoreRecordCollection<TRecord>(
        this IServiceCollection services,
        string collectionName,
        RedisJsonCollectionOptions? options = default,
        string? serviceId = default)
        where TRecord : class
    {
        services.AddKeyedTransient<VectorStoreCollection<string, TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                var database = sp.GetRequiredService<IDatabase>();
                options ??= sp.GetService<RedisJsonCollectionOptions>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return new RedisJsonCollection<string, TRecord>(database, collectionName, options);
            });

        AddVectorizedSearch<TRecord>(services, serviceId);

        return services;
    }

    /// <summary>
    /// Register a Redis <see cref="VectorStoreCollection{TKey, TRecord}"/> with the specified service ID
    /// and where the Redis <see cref="IDatabase"/> is constructed using the provided <paramref name="redisConnectionConfiguration"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStoreCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="redisConnectionConfiguration">The Redis connection configuration string.</param>
    /// <param name="options">Optional options to further configure the <see cref="VectorStoreCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    [RequiresDynamicCode("This method is incompatible with NativeAOT, consult the documentation for adding collections in a way that's compatible with NativeAOT.")]
    [RequiresUnreferencedCode("This method is incompatible with trimming, consult the documentation for adding collections in a way that's compatible with NativeAOT.")]
    public static IServiceCollection AddRedisJsonVectorStoreRecordCollection<TRecord>(
        this IServiceCollection services,
        string collectionName,
        string redisConnectionConfiguration,
        RedisJsonCollectionOptions? options = default,
        string? serviceId = default)
        where TRecord : class
    {
        services.AddKeyedSingleton<VectorStoreCollection<string, TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                var database = ConnectionMultiplexer.Connect(redisConnectionConfiguration).GetDatabase();
                options ??= sp.GetService<RedisJsonCollectionOptions>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return new RedisJsonCollection<string, TRecord>(database, collectionName, options);
            });

        AddVectorizedSearch<TRecord>(services, serviceId);

        return services;
    }

    /// <summary>
    /// Also register the <see cref="VectorStoreCollection{TKey, TRecord}"/> with the given <paramref name="serviceId"/> as a <see cref="IVectorSearchable{TRecord}"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="services">The service collection to register on.</param>
    /// <param name="serviceId">The service id that the registrations should use.</param>
    private static void AddVectorizedSearch<TRecord>(IServiceCollection services, string? serviceId) where TRecord : class
    {
        services.AddKeyedTransient<IVectorSearchable<TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                return sp.GetRequiredKeyedService<VectorStoreCollection<string, TRecord>>(serviceId);
            });
    }
}
