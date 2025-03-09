// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.DependencyInjection;

namespace Microsoft.Extensions.VectorData;

/// <summary>Provides extension methods for registering <see cref="IKeywordHybridSearch{TRecord}"/> with a <see cref="IServiceCollection"/>.</summary>
[Experimental("SKEXP0020")]
public static class KeywordHybridSearchBuilderServiceCollectionExtensions
{
    /// <summary>Registers a singleton <see cref="IKeywordHybridSearch{TRecord}"/> in the <see cref="IServiceCollection"/>.</summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the search should be added.</param>
    /// <param name="innerSearch">The inner <see cref="IKeywordHybridSearch{TRecord}"/> that represents the underlying backend.</param>
    /// <param name="lifetime">The service lifetime for the search. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>A <see cref="KeywordHybridSearchBuilder{TRecord}"/> that can be used to build a pipeline around the inner search.</returns>
    /// <remarks>The search is registered as a singleton service.</remarks>
    public static KeywordHybridSearchBuilder<TRecord> AddKeywordHybridSearch<TRecord>(
        this IServiceCollection serviceCollection,
        IKeywordHybridSearch<TRecord> innerSearch,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        return AddKeywordHybridSearch(serviceCollection, _ => innerSearch, lifetime);
    }

    /// <summary>Registers a singleton <see cref="IKeywordHybridSearch{TRecord}"/> in the <see cref="IServiceCollection"/>.</summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the search should be added.</param>
    /// <param name="innerSearchFactory">A callback that produces the inner <see cref="IKeywordHybridSearch{TRecord}"/> that represents the underlying backend.</param>
    /// <param name="lifetime">The service lifetime for the search. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>A <see cref="KeywordHybridSearchBuilder{TRecord}"/> that can be used to build a pipeline around the inner search.</returns>
    /// <remarks>The search is registered as a singleton service.</remarks>
    public static KeywordHybridSearchBuilder<TRecord> AddKeywordHybridSearch<TRecord>(
        this IServiceCollection serviceCollection,
        Func<IServiceProvider, IKeywordHybridSearch<TRecord>> innerSearchFactory,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        var builder = new KeywordHybridSearchBuilder<TRecord>(innerSearchFactory);
        serviceCollection.Add(new ServiceDescriptor(typeof(IKeywordHybridSearch<TRecord>), builder.Build, lifetime));
        return builder;
    }

    /// <summary>Registers a keyed singleton <see cref="IKeywordHybridSearch{TRecord}"/> in the <see cref="IServiceCollection"/>.</summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the search should be added.</param>
    /// <param name="serviceKey">The key with which to associate the search.</param>
    /// <param name="innerSearch">The inner <see cref="IKeywordHybridSearch{TRecord}"/> that represents the underlying backend.</param>
    /// <param name="lifetime">The service lifetime for the search. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>A <see cref="KeywordHybridSearchBuilder{TRecord}"/> that can be used to build a pipeline around the inner search.</returns>
    /// <remarks>The search is registered as a scoped service.</remarks>
    public static KeywordHybridSearchBuilder<TRecord> AddKeyedKeywordHybridSearch<TRecord>(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        IKeywordHybridSearch<TRecord> innerSearch,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        return AddKeyedKeywordHybridSearch(serviceCollection, serviceKey, _ => innerSearch, lifetime);
    }

    /// <summary>Registers a keyed singleton <see cref="IKeywordHybridSearch{TRecord}"/> in the <see cref="IServiceCollection"/>.</summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the search should be added.</param>
    /// <param name="serviceKey">The key with which to associate the search.</param>
    /// <param name="innerSearchFactory">A callback that produces the inner <see cref="IKeywordHybridSearch{TRecord}"/> that represents the underlying backend.</param>
    /// <param name="lifetime">The service lifetime for the search. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>A <see cref="KeywordHybridSearchBuilder{TRecord}"/> that can be used to build a pipeline around the inner search.</returns>
    /// <remarks>The search is registered as a scoped service.</remarks>
    public static KeywordHybridSearchBuilder<TRecord> AddKeyedKeywordHybridSearch<TRecord>(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        Func<IServiceProvider, IKeywordHybridSearch<TRecord>> innerSearchFactory,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        var builder = new KeywordHybridSearchBuilder<TRecord>(innerSearchFactory);
        serviceCollection.Add(new ServiceDescriptor(typeof(IKeywordHybridSearch<TRecord>), serviceKey, factory: (services, serviceKey) => builder.Build(services), lifetime));
        return builder;
    }
}
