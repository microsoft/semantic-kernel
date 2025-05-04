﻿// Copyright (c) Microsoft. All rights reserved.

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
    /// Register an InMemory <see cref="VectorStore"/> with the specified service ID.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStore"/> on.</param>
    /// <param name="options">Optional options to further configure the <see cref="VectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddInMemoryVectorStore(this IServiceCollection services, InMemoryVectorStoreOptions? options = default, string? serviceId = default)
    {
        services.AddKeyedTransient<VectorStore>(
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
        services.AddKeyedSingleton<VectorStore>(serviceId, (sp, obj) => sp.GetRequiredKeyedService<InMemoryVectorStore>(serviceId));
        return services;
    }

    /// <summary>
    /// Register an InMemory <see cref="VectorStoreCollection{TKey, TRecord}"/> and <see cref="IVectorSearch{TRecord}"/> with the specified service ID.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStoreCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Optional options to further configure the <see cref="VectorStoreCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddInMemoryVectorStoreRecordCollection<TKey, TRecord>(
        this IServiceCollection services,
        string collectionName,
        InMemoryCollectionOptions<TKey, TRecord>? options = default,
        string? serviceId = default)
        where TKey : notnull
        where TRecord : notnull
    {
        services.AddKeyedSingleton<VectorStoreCollection<TKey, TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                options ??= sp.GetService<InMemoryCollectionOptions<TKey, TRecord>>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };
                return (new InMemoryCollection<TKey, TRecord>(collectionName, options) as VectorStoreCollection<TKey, TRecord>)!;
            });

        services.AddKeyedSingleton<IVectorSearch<TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                return sp.GetRequiredKeyedService<VectorStoreCollection<TKey, TRecord>>(serviceId);
            });

        return services;
    }
}
