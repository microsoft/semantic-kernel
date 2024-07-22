// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Data;
using StackExchange.Redis;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Extension methods to register Redis <see cref="IVectorStore"/> instances on an <see cref="IServiceCollection"/>.
/// </summary>
public static class RedisServiceCollectionExtensions
{
    /// <summary>
    /// Register a Redis <see cref="IVectorStore"/> with the specified service ID.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="redisConnectionConfiguration">The Redis connection configuration string. If not provided, an <see cref="IDatabase"/> instance will be requested from the dependency injection container.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <param name="options">Optoinal options to further configure the <see cref="IVectorStore"/>.</param>
    /// <returns>The kernel builder.</returns>
    public static IServiceCollection AddRedisVectorStore(this IServiceCollection services, string? redisConnectionConfiguration = default, string? serviceId = default, RedisVectorStoreOptions? options = default)
    {
        if (redisConnectionConfiguration == null)
        {
            // If we are not constructing the ConnectionMultiplexer, add the IVectorStore as transient, since we
            // cannot make assumptions about how IDatabase is being managed.
            services.AddKeyedTransient<IVectorStore>(
                serviceId,
                (sp, obj) =>
                {
                    var database = sp.GetRequiredService<IDatabase>();
                    var selectedOptions = options ?? sp.GetService<RedisVectorStoreOptions>();

                    return new RedisVectorStore(
                        database,
                        selectedOptions);
                });

            return services;
        }

        // If we are constructing the ConnectionMultiplexer, add the IVectorStore as singleton, since we are managing the lifetime
        // of the ConnectionMultiplexer, and the recommendation from StackExchange.Redis is to share the ConnectionMultiplexer.
        services.AddKeyedSingleton<IVectorStore>(
            serviceId,
            (sp, obj) =>
            {
                var database = ConnectionMultiplexer.Connect(redisConnectionConfiguration).GetDatabase();
                var selectedOptions = options ?? sp.GetService<RedisVectorStoreOptions>();

                return new RedisVectorStore(
                    database,
                    selectedOptions);
            });

        return services;
    }
}
