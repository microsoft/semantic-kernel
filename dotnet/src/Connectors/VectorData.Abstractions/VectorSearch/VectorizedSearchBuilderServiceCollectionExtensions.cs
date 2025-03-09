// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;

namespace Microsoft.Extensions.VectorData;

/// <summary>Provides extension methods for registering <see cref="IVectorizedSearch{TRecord}"/> with a <see cref="IServiceCollection"/>.</summary>
[Experimental("SKEXP0020")]
public static class VectorizedSearchBuilderServiceCollectionExtensions
{
    /// <summary>Registers a singleton <see cref="IVectorizedSearch{TRecord}"/> in the <see cref="IServiceCollection"/>.</summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the search should be added.</param>
    /// <param name="innerSearch">The inner <see cref="IVectorizedSearch{TRecord}"/> that represents the underlying backend.</param>
    /// <param name="lifetime">The service lifetime for the search. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>A <see cref="VectorizedSearchBuilder{TRecord}"/> that can be used to build a pipeline around the inner search.</returns>
    /// <remarks>The search is registered as a singleton service.</remarks>
    public static VectorizedSearchBuilder<TRecord> AddVectorizedSearch<TRecord>(
        this IServiceCollection serviceCollection,
        IVectorizedSearch<TRecord> innerSearch,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNull(serviceCollection);
        Verify.NotNull(innerSearch);

        return AddVectorizedSearch(serviceCollection, _ => innerSearch, lifetime);
    }

    /// <summary>Registers a singleton <see cref="IVectorizedSearch{TRecord}"/> in the <see cref="IServiceCollection"/>.</summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the search should be added.</param>
    /// <param name="innerSearchFactory">A callback that produces the inner <see cref="IVectorizedSearch{TRecord}"/> that represents the underlying backend.</param>
    /// <param name="lifetime">The service lifetime for the search. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>A <see cref="VectorizedSearchBuilder{TRecord}"/> that can be used to build a pipeline around the inner search.</returns>
    /// <remarks>The search is registered as a singleton service.</remarks>
    public static VectorizedSearchBuilder<TRecord> AddVectorizedSearch<TRecord>(
        this IServiceCollection serviceCollection,
        Func<IServiceProvider, IVectorizedSearch<TRecord>> innerSearchFactory,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNull(serviceCollection);
        Verify.NotNull(innerSearchFactory);

        var builder = new VectorizedSearchBuilder<TRecord>(innerSearchFactory);
        serviceCollection.Add(new ServiceDescriptor(typeof(IVectorizedSearch<TRecord>), builder.Build, lifetime));
        return builder;
    }

    /// <summary>Registers a keyed singleton <see cref="IVectorizedSearch{TRecord}"/> in the <see cref="IServiceCollection"/>.</summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the search should be added.</param>
    /// <param name="serviceKey">The key with which to associate the search.</param>
    /// <param name="innerSearch">The inner <see cref="IVectorizedSearch{TRecord}"/> that represents the underlying backend.</param>
    /// <param name="lifetime">The service lifetime for the search. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>A <see cref="VectorizedSearchBuilder{TRecord}"/> that can be used to build a pipeline around the inner search.</returns>
    /// <remarks>The search is registered as a scoped service.</remarks>
    public static VectorizedSearchBuilder<TRecord> AddKeyedVectorizedSearch<TRecord>(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        IVectorizedSearch<TRecord> innerSearch,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNull(serviceCollection);
        Verify.NotNull(innerSearch);

        return AddKeyedVectorizedSearch(serviceCollection, serviceKey, _ => innerSearch, lifetime);
    }

    /// <summary>Registers a keyed singleton <see cref="IVectorizedSearch{TRecord}"/> in the <see cref="IServiceCollection"/>.</summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the search should be added.</param>
    /// <param name="serviceKey">The key with which to associate the search.</param>
    /// <param name="innerSearchFactory">A callback that produces the inner <see cref="IVectorizedSearch{TRecord}"/> that represents the underlying backend.</param>
    /// <param name="lifetime">The service lifetime for the search. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>A <see cref="VectorizedSearchBuilder{TRecord}"/> that can be used to build a pipeline around the inner search.</returns>
    /// <remarks>The search is registered as a scoped service.</remarks>
    public static VectorizedSearchBuilder<TRecord> AddKeyedVectorizedSearch<TRecord>(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        Func<IServiceProvider, IVectorizedSearch<TRecord>> innerSearchFactory,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNull(serviceCollection);
        Verify.NotNull(innerSearchFactory);

        var builder = new VectorizedSearchBuilder<TRecord>(innerSearchFactory);
        serviceCollection.Add(new ServiceDescriptor(typeof(IVectorizedSearch<TRecord>), serviceKey, factory: (services, serviceKey) => builder.Build(services), lifetime));
        return builder;
    }
}
