// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.InMemory;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register Data services on an <see cref="IServiceCollection"/>.
/// </summary>
[Experimental("SKEXP0001")]
public static class ServiceCollectionExtensions
{
    /// <summary>
    /// Register a InMemory <see cref="IVectorStore"/> with the specified service ID.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddInMemoryVectorStore(this IServiceCollection services, string? serviceId = default)
    {
        services.AddKeyedSingleton<InMemoryVectorStore, InMemoryVectorStore>(serviceId);
        services.AddKeyedSingleton<IVectorStore>(serviceId, (sp, obj) => sp.GetRequiredKeyedService<InMemoryVectorStore>(serviceId));
        return services;
    }
}
