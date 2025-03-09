// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.DependencyInjection;

namespace Microsoft.Extensions.VectorData;

/// <summary>Provides extension methods for registering <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> with a <see cref="IServiceCollection"/>.</summary>
[Experimental("SKEXP0020")]
public static class VectorStoreRecordCollectionBuilderServiceCollectionExtensions
{
    /// <summary>Registers a singleton <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> in the <see cref="IServiceCollection"/>.</summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the collection should be added.</param>
    /// <param name="innerCollection">The inner <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> that represents the underlying backend.</param>
    /// <param name="lifetime">The service lifetime for the collection. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>A <see cref="VectorStoreRecordCollectionBuilder{TKey, TRecord}"/> that can be used to build a pipeline around the inner collection.</returns>
    /// <remarks>The collection is registered as a singleton service.</remarks>
    public static VectorStoreRecordCollectionBuilder<TKey, TRecord> AddVectorStoreRecordCollection<TKey, TRecord>(
        this IServiceCollection serviceCollection,
        IVectorStoreRecordCollection<TKey, TRecord> innerCollection,
        ServiceLifetime lifetime = ServiceLifetime.Singleton) where TKey : notnull
    {
        return AddVectorStoreRecordCollection(serviceCollection, _ => innerCollection, lifetime);
    }

    /// <summary>Registers a singleton <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> in the <see cref="IServiceCollection"/>.</summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the collection should be added.</param>
    /// <param name="innerCollectionFactory">A callback that produces the inner <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> that represents the underlying backend.</param>
    /// <param name="lifetime">The service lifetime for the collection. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>A <see cref="VectorStoreRecordCollectionBuilder{TKey, TRecord}"/> that can be used to build a pipeline around the inner collection.</returns>
    /// <remarks>The collection is registered as a singleton service.</remarks>
    public static VectorStoreRecordCollectionBuilder<TKey, TRecord> AddVectorStoreRecordCollection<TKey, TRecord>(
        this IServiceCollection serviceCollection,
        Func<IServiceProvider, IVectorStoreRecordCollection<TKey, TRecord>> innerCollectionFactory,
        ServiceLifetime lifetime = ServiceLifetime.Singleton) where TKey : notnull
    {
        var builder = new VectorStoreRecordCollectionBuilder<TKey, TRecord>(innerCollectionFactory);
        serviceCollection.Add(new ServiceDescriptor(typeof(IVectorStoreRecordCollection<TKey, TRecord>), builder.Build, lifetime));
        return builder;
    }

    /// <summary>Registers a keyed singleton <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> in the <see cref="IServiceCollection"/>.</summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the collection should be added.</param>
    /// <param name="serviceKey">The key with which to associate the collection.</param>
    /// <param name="innerCollection">The inner <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> that represents the underlying backend.</param>
    /// <param name="lifetime">The service lifetime for the collection. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>A <see cref="VectorStoreRecordCollectionBuilder{TKey, TRecord}"/> that can be used to build a pipeline around the inner collection.</returns>
    /// <remarks>The collection is registered as a scoped service.</remarks>
    public static VectorStoreRecordCollectionBuilder<TKey, TRecord> AddKeyedVectorStoreRecordCollection<TKey, TRecord>(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        IVectorStoreRecordCollection<TKey, TRecord> innerCollection,
        ServiceLifetime lifetime = ServiceLifetime.Singleton) where TKey : notnull
    {
        return AddKeyedVectorStoreRecordCollection(serviceCollection, serviceKey, _ => innerCollection, lifetime);
    }

    /// <summary>Registers a keyed singleton <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> in the <see cref="IServiceCollection"/>.</summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the collection should be added.</param>
    /// <param name="serviceKey">The key with which to associate the collection.</param>
    /// <param name="innerCollectionFactory">A callback that produces the inner <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> that represents the underlying backend.</param>
    /// <param name="lifetime">The service lifetime for the collection. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>A <see cref="VectorStoreRecordCollectionBuilder{TKey, TRecord}"/> that can be used to build a pipeline around the inner collection.</returns>
    /// <remarks>The collection is registered as a scoped service.</remarks>
    public static VectorStoreRecordCollectionBuilder<TKey, TRecord> AddKeyedVectorStoreRecordCollection<TKey, TRecord>(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        Func<IServiceProvider, IVectorStoreRecordCollection<TKey, TRecord>> innerCollectionFactory,
        ServiceLifetime lifetime = ServiceLifetime.Singleton) where TKey : notnull
    {
        var builder = new VectorStoreRecordCollectionBuilder<TKey, TRecord>(innerCollectionFactory);
        serviceCollection.Add(new ServiceDescriptor(typeof(IVectorStoreRecordCollection<TKey, TRecord>), serviceKey, factory: (services, serviceKey) => builder.Build(services), lifetime));
        return builder;
    }
}
