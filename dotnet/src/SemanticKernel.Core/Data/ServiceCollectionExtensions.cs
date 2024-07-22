// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Extension methods to register Data services on an <see cref="IServiceCollection"/>.
/// </summary>
public static class ServiceCollectionExtensions
{
    /// <summary>
    /// Register a Volatile <see cref="IVectorStore"/> with the specified service ID.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IServiceCollection AddVolatileVectorStore(this IServiceCollection services, string? serviceId = default)
    {
        services.AddKeyedSingleton<IVectorStore, VolatileVectorStore>(serviceId);
        return services;
    }
}
