// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.DependencyInjection;

namespace Microsoft.Extensions.VectorData;

/// <summary>Provides extension methods for registering <see cref="IVectorizableTextSearch{TRecord}"/> with a <see cref="IServiceCollection"/>.</summary>
[Experimental("SKEXP0020")]
public static class VectorizableTextSearchBuilderServiceCollectionExtensions
{
    /// <summary>Registers a singleton <see cref="IVectorizableTextSearch{TRecord}"/> in the <see cref="IServiceCollection"/>.</summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the search should be added.</param>
    /// <param name="innerSearch">The inner <see cref="IVectorizableTextSearch{TRecord}"/> that represents the underlying backend.</param>
    /// <param name="lifetime">The service lifetime for the search. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>A <see cref="VectorizableTextSearchBuilder{TRecord}"/> that can be used to build a pipeline around the inner search.</returns>
    /// <remarks>The search is registered as a singleton service.</remarks>
    public static VectorizableTextSearchBuilder<TRecord> AddVectorizableTextSearch<TRecord>(
        this IServiceCollection serviceCollection,
        IVectorizableTextSearch<TRecord> innerSearch,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        return AddVectorizableTextSearch(serviceCollection, _ => innerSearch, lifetime);
    }

    /// <summary>Registers a singleton <see cref="IVectorizableTextSearch{TRecord}"/> in the <see cref="IServiceCollection"/>.</summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the search should be added.</param>
    /// <param name="innerSearchFactory">A callback that produces the inner <see cref="IVectorizableTextSearch{TRecord}"/> that represents the underlying backend.</param>
    /// <param name="lifetime">The service lifetime for the search. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>A <see cref="VectorizableTextSearchBuilder{TRecord}"/> that can be used to build a pipeline around the inner search.</returns>
    /// <remarks>The search is registered as a singleton service.</remarks>
    public static VectorizableTextSearchBuilder<TRecord> AddVectorizableTextSearch<TRecord>(
        this IServiceCollection serviceCollection,
        Func<IServiceProvider, IVectorizableTextSearch<TRecord>> innerSearchFactory,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        var builder = new VectorizableTextSearchBuilder<TRecord>(innerSearchFactory);
        serviceCollection.Add(new ServiceDescriptor(typeof(IVectorizableTextSearch<TRecord>), builder.Build, lifetime));
        return builder;
    }

    /// <summary>Registers a keyed singleton <see cref="IVectorizableTextSearch{TRecord}"/> in the <see cref="IServiceCollection"/>.</summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the search should be added.</param>
    /// <param name="serviceKey">The key with which to associate the search.</param>
    /// <param name="innerSearch">The inner <see cref="IVectorizableTextSearch{TRecord}"/> that represents the underlying backend.</param>
    /// <param name="lifetime">The service lifetime for the search. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>A <see cref="VectorizableTextSearchBuilder{TRecord}"/> that can be used to build a pipeline around the inner search.</returns>
    /// <remarks>The search is registered as a scoped service.</remarks>
    public static VectorizableTextSearchBuilder<TRecord> AddKeyedVectorizableTextSearch<TRecord>(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        IVectorizableTextSearch<TRecord> innerSearch,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        return AddKeyedVectorizableTextSearch(serviceCollection, serviceKey, _ => innerSearch, lifetime);
    }

    /// <summary>Registers a keyed singleton <see cref="IVectorizableTextSearch{TRecord}"/> in the <see cref="IServiceCollection"/>.</summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the search should be added.</param>
    /// <param name="serviceKey">The key with which to associate the search.</param>
    /// <param name="innerSearchFactory">A callback that produces the inner <see cref="IVectorizableTextSearch{TRecord}"/> that represents the underlying backend.</param>
    /// <param name="lifetime">The service lifetime for the search. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>A <see cref="VectorizableTextSearchBuilder{TRecord}"/> that can be used to build a pipeline around the inner search.</returns>
    /// <remarks>The search is registered as a scoped service.</remarks>
    public static VectorizableTextSearchBuilder<TRecord> AddKeyedVectorizableTextSearch<TRecord>(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        Func<IServiceProvider, IVectorizableTextSearch<TRecord>> innerSearchFactory,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        var builder = new VectorizableTextSearchBuilder<TRecord>(innerSearchFactory);
        serviceCollection.Add(new ServiceDescriptor(typeof(IVectorizableTextSearch<TRecord>), serviceKey, factory: (services, serviceKey) => builder.Build(services), lifetime));
        return builder;
    }
}
