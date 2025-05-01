// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Redis;
using StackExchange.Redis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register Redis <see cref="IVectorStore"/> instances on the <see cref="IKernelBuilder"/>.
/// </summary>
public static class RedisKernelBuilderExtensions
{
    /// <summary>
    /// Register a Redis <see cref="IVectorStore"/> with the specified service ID and where the Redis <see cref="IDatabase"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <param name="builder">The builder to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddRedisVectorStore(this IKernelBuilder builder, RedisVectorStoreOptions? options = default, string? serviceId = default)
    {
        builder.Services.AddRedisVectorStore(options, serviceId);
        return builder;
    }

    /// <summary>
    /// Register a Redis <see cref="IVectorStore"/> with the specified service ID and where the Redis <see cref="IDatabase"/> is constructed using the provided <paramref name="redisConnectionConfiguration"/>.
    /// </summary>
    /// <param name="builder">The builder to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="redisConnectionConfiguration">The Redis connection configuration string. If not provided, an <see cref="IDatabase"/> instance will be requested from the dependency injection container.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddRedisVectorStore(this IKernelBuilder builder, string redisConnectionConfiguration, RedisVectorStoreOptions? options = default, string? serviceId = default)
    {
        builder.Services.AddRedisVectorStore(redisConnectionConfiguration, options, serviceId);
        return builder;
    }

    /// <summary>
    /// Register a Redis <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> with the specified service ID
    /// and where the Redis <see cref="IDatabase"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="builder">The builder to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddRedisHashSetVectorStoreRecordCollection<TRecord>(
        this IKernelBuilder builder,
        string collectionName,
        RedisHashSetVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TRecord : notnull
    {
        builder.Services.AddRedisHashSetVectorStoreRecordCollection(collectionName, options, serviceId);
        return builder;
    }

    /// <summary>
    /// Register a Redis <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> with the specified service ID
    /// and where the Redis <see cref="IDatabase"/> is constructed using the provided <paramref name="redisConnectionConfiguration"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="builder">The builder to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="redisConnectionConfiguration">The Redis connection configuration string.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddRedisHashSetVectorStoreRecordCollection<TRecord>(
        this IKernelBuilder builder,
        string collectionName,
        string redisConnectionConfiguration,
        RedisHashSetVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TRecord : notnull
    {
        builder.Services.AddRedisHashSetVectorStoreRecordCollection(collectionName, redisConnectionConfiguration, options, serviceId);
        return builder;
    }

    /// <summary>
    /// Register a Redis <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> with the specified service ID
    /// and where the Redis <see cref="IDatabase"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="builder">The builder to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddRedisJsonVectorStoreRecordCollection<TRecord>(
        this IKernelBuilder builder,
        string collectionName,
        RedisJsonVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TRecord : notnull
    {
        builder.Services.AddRedisJsonVectorStoreRecordCollection(collectionName, options, serviceId);
        return builder;
    }

    /// <summary>
    /// Register a Redis <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> with the specified service ID
    /// and where the Redis <see cref="IDatabase"/> is constructed using the provided <paramref name="redisConnectionConfiguration"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="builder">The builder to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="redisConnectionConfiguration">The Redis connection configuration string.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddRedisJsonVectorStoreRecordCollection<TRecord>(
        this IKernelBuilder builder,
        string collectionName,
        string redisConnectionConfiguration,
        RedisJsonVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TRecord : notnull
    {
        builder.Services.AddRedisJsonVectorStoreRecordCollection(collectionName, redisConnectionConfiguration, options, serviceId);
        return builder;
    }
}
