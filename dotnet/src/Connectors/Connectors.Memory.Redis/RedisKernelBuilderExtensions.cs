// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.Redis;
using Microsoft.SemanticKernel.Data;
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
}
