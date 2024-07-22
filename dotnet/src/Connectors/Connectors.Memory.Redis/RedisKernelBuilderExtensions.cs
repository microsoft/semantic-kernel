// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Data;
using StackExchange.Redis;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Extension methods to register Redis <see cref="IVectorStore"/> instances on the <see cref="IKernelBuilder"/>.
/// </summary>
public static class RedisKernelBuilderExtensions
{
    /// <summary>
    /// Register a Redis <see cref="IVectorStore"/> with the specified service ID.
    /// </summary>
    /// <param name="builder">The builder to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="redisConnectionConfiguration">The Redis connection configuration string. If not provided, an <see cref="IDatabase"/> instance will be requested from the dependency injection container.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddRedisVectorStore(this IKernelBuilder builder, string? redisConnectionConfiguration = default, string? serviceId = default, RedisVectorStoreOptions? options = default)
    {
        builder.Services.AddRedisVectorStore(redisConnectionConfiguration, serviceId, options);
        return builder;
    }
}
