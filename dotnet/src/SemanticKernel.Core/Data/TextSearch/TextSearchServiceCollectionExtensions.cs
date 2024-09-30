// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Embeddings;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register <see cref="ITextSearch"/> for use with <see cref="IServiceCollection"/>.
/// </summary>
public static class TextSearchServiceCollectionExtensions
{
    /// <summary>
    /// Register an <see cref="ITextSearch"/> instance with the specified service ID.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="ITextSearch"/> on.</param>
    /// <param name="textSearch">Instance of <see cref="ITextSearch"/> to register.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    public static IServiceCollection AddTextSearch(
        this IServiceCollection services,
        ITextSearch textSearch,
        string? serviceId = default)
    {
        ITextSearch Factory(IServiceProvider serviceProvider, object? _) => textSearch;
        services.AddKeyedSingleton<ITextSearch>(serviceId, (Func<IServiceProvider, object?, ITextSearch>)Factory);
        return services;
    }

    /// <summary>
    /// Register an <see cref="IVectorizableTextSearch{TRecord}"/> instance with the specified service ID.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="ITextSearch"/> on.</param>
    /// <param name="vectorTextSearch">Instance of <see cref="IVectorizableTextSearch{TRecord}"/> to register.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    public static IServiceCollection AddVectorStoreTextSearch<TRecord>(
        this IServiceCollection services,
        VectorStoreTextSearch<TRecord> vectorTextSearch,
        string? serviceId = default)
        where TRecord : class
    {
        VectorStoreTextSearch<TRecord> Factory(IServiceProvider serviceProvider, object? _) => vectorTextSearch;
        services.AddKeyedSingleton<VectorStoreTextSearch<TRecord>>(serviceId, (Func<IServiceProvider, object?, VectorStoreTextSearch<TRecord>>)Factory);
        return services;
    }

    /// <summary>
    /// Register a <see cref="VectorStoreTextSearch{TRecord}"/> instance with the specified service ID.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="ITextSearch"/> on.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    public static IServiceCollection AddVectorStoreTextSearch<TRecord>(
        this IServiceCollection services,
        string? serviceId = default)
        where TRecord : class
    {
        // If we are not constructing the dependent services, add the VectorStoreTextSearch as transient, since we
        // cannot make assumptions about how dependent services are being managed.
        services.AddKeyedTransient<VectorStoreTextSearch<TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                var stringMapper = sp.GetRequiredService<ITextSearchStringMapper>();
                var resultMapper = sp.GetRequiredService<ITextSearchResultMapper>();
                var options = sp.GetService<VectorStoreTextSearchOptions>();

                var vectorizableTextSearch = sp.GetService<IVectorizableTextSearch<TRecord>>();
                if (vectorizableTextSearch is not null)
                {
                    return new VectorStoreTextSearch<TRecord>(
                        vectorizableTextSearch,
                        stringMapper,
                        resultMapper,
                        options);
                }

                var vectorizedSearch = sp.GetService<IVectorizedSearch<TRecord>>();
                var generationService = sp.GetService<ITextEmbeddingGenerationService>();
                if (vectorizedSearch is not null && generationService is not null)
                {
                    return new VectorStoreTextSearch<TRecord>(
                        vectorizedSearch,
                        generationService,
                        stringMapper,
                        resultMapper,
                        options);
                }

                throw new InvalidOperationException("No IVectorizableTextSearch<TRecord> or IVectorizedSearch<TRecord> and ITextEmbeddingGenerationService registered.");
            });

        return services;
    }
}
