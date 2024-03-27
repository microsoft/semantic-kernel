// Copyright (c) Microsoft. All rights reserved.

using Kusto.Data;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Kusto;

/// <summary>
/// Provides extension methods for registering the <see cref="KustoMemoryStore"/> class.
/// </summary>
public static class KustoMemoryStoreExtensions
{
    /// <summary>
    /// Adds a Kusto <see cref="IMemoryStore"/> to the service collection.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="database">The Kusto database name.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddKustoMemoryStore(this IServiceCollection services, string database, string? serviceId = null) =>
        services.AddKeyedSingleton<IMemoryStore>(serviceId, (provider, _) =>
        {
            var builder = provider.GetRequiredService<KustoConnectionStringBuilder>();
            return new KustoMemoryStore(builder, database);
        });
}
