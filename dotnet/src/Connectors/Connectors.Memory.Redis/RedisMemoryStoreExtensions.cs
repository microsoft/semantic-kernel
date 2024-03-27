// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Memory;
using StackExchange.Redis;
using static NRedisStack.Search.Schema.VectorField;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Extension methods for adding <see cref="RedisMemoryStore"/> to the <see cref="IServiceCollection"/>.
/// </summary>
public static class RedisMemoryStoreExtensions
{
    /// <summary>
    /// Adds <see cref="RedisMemoryStore"/> to the <see cref="IServiceCollection"/> with the specified configuration using a previously registered <see cref="IDatabase"/>.
    /// </summary>
    /// <param name="services">The IServiceCollection to add the RedisMemoryStore to.</param>
    /// <param name="vectorSize">The size of the vector.</param>
    /// <param name="vectorIndexAlgorithm">The vector index algorithm.</param>
    /// <param name="vectorDistanceMetric">The vector distance metric.</param>
    /// <param name="queryDialect">The query dialect.</param>
    /// <param name="serviceId">The service identifier.</param>
    /// <returns>The updated IServiceCollection.</returns>
    public static IServiceCollection AddRedisMemoryStore(
        this IServiceCollection services,
        int vectorSize = RedisMemoryStore.DefaultVectorSize,
        VectorAlgo vectorIndexAlgorithm = RedisMemoryStore.DefaultIndexAlgorithm,
        VectorDistanceMetric vectorDistanceMetric = RedisMemoryStore.DefaultDistanceMetric,
        int queryDialect = RedisMemoryStore.DefaultQueryDialect,
        string? serviceId = null) =>
            services.AddKeyedSingleton<IMemoryStore>(serviceId, (provider, _) =>
                new RedisMemoryStore(provider.GetRequiredService<IDatabase>(), vectorSize, vectorIndexAlgorithm, vectorDistanceMetric, queryDialect));

    /// <summary>
    /// Adds RedisMemoryStore to the IServiceCollection with the specified configuration.
    /// </summary>
    /// <param name="services">The IServiceCollection to add the RedisMemoryStore to.</param>
    /// <param name="connectionString">The Redis connection string.</param>
    /// <param name="vectorSize">The size of the vector.</param>
    /// <param name="vectorIndexAlgorithm">The vector index algorithm.</param>
    /// <param name="vectorDistanceMetric">The vector distance metric.</param>
    /// <param name="queryDialect">The query dialect.</param>
    /// <param name="serviceId">The service identifier.</param>
    /// <returns>The updated IServiceCollection.</returns>
    public static IServiceCollection AddRedisMemoryStore(
        this IServiceCollection services,
        string connectionString,
        int vectorSize = RedisMemoryStore.DefaultVectorSize,
        VectorAlgo vectorIndexAlgorithm = RedisMemoryStore.DefaultIndexAlgorithm,
        VectorDistanceMetric vectorDistanceMetric = RedisMemoryStore.DefaultDistanceMetric,
        int queryDialect = RedisMemoryStore.DefaultQueryDialect,
        string? serviceId = null) =>
            services.AddKeyedSingleton<IMemoryStore>(serviceId, (provider, _) =>
                new RedisMemoryStore(connectionString, vectorSize, vectorIndexAlgorithm, vectorDistanceMetric, queryDialect));
}
