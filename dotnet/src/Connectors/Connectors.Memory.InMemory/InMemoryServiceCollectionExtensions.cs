// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.InMemory;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register Data services on an <see cref="IServiceCollection"/>.
/// </summary>
[Experimental("SKEXP0001")]
public static class InMemoryServiceCollectionExtensions
{
    /// <summary>
    /// Register an InMemory <see cref="IVectorStore"/> with the specified service ID.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddInMemoryVectorStore(this IServiceCollection services, InMemoryVectorStoreOptions? options = default, string? serviceId = default)
    {
        services.AddKeyedTransient<IVectorStore>(
            serviceId,
            (sp, obj) =>
            {
                options ??= sp.GetService<InMemoryVectorStoreOptions>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return new InMemoryVectorStore(options);
            });

        services.AddKeyedSingleton<InMemoryVectorStore, InMemoryVectorStore>(serviceId);
        services.AddKeyedSingleton<IVectorStore>(serviceId, (sp, obj) => sp.GetRequiredKeyedService<InMemoryVectorStore>(serviceId));
        return services;
    }

    /// <summary>
    /// Register an InMemory <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorSearch{TRecord}"/> with the specified service ID.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddInMemoryVectorStoreRecordCollection<TKey, TRecord>(
        this IServiceCollection services,
        string collectionName,
        InMemoryVectorStoreRecordCollectionOptions<TKey, TRecord>? options = default,
        string? serviceId = default)
        where TKey : notnull
        where TRecord : notnull
    {
        services.AddKeyedSingleton<IVectorStoreRecordCollection<TKey, TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                options ??= sp.GetService<InMemoryVectorStoreRecordCollectionOptions<TKey, TRecord>>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };
                return (new InMemoryVectorStoreRecordCollection<TKey, TRecord>(collectionName, options) as IVectorStoreRecordCollection<TKey, TRecord>)!;
            });

        services.AddKeyedSingleton<IVectorSearch<TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                return sp.GetRequiredKeyedService<IVectorStoreRecordCollection<TKey, TRecord>>(serviceId);
            });

        return services;
    }
}
