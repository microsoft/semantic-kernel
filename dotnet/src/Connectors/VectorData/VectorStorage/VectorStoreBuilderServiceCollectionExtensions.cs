// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;

namespace Microsoft.Extensions.VectorData;

/// <summary>Provides extension methods for registering <see cref="IVectorStore"/> with a <see cref="IServiceCollection"/>.</summary>
[Experimental("SKEXP0020")]
public static class VectorStoreBuilderServiceCollectionExtensions
{
    /// <summary>Registers a singleton <see cref="IVectorStore"/> in the <see cref="IServiceCollection"/>.</summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the store should be added.</param>
    /// <param name="innerStore">The inner <see cref="IVectorStore"/> that represents the underlying backend.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>A <see cref="VectorStoreBuilder"/> that can be used to build a pipeline around the inner store.</returns>
    /// <remarks>The store is registered as a singleton service.</remarks>
    public static VectorStoreBuilder AddVectorStore(
        this IServiceCollection serviceCollection,
        IVectorStore innerStore,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNull(serviceCollection);
        Verify.NotNull(innerStore);

        return AddVectorStore(serviceCollection, _ => innerStore, lifetime);
    }

    /// <summary>Registers a singleton <see cref="IVectorStore"/> in the <see cref="IServiceCollection"/>.</summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the store should be added.</param>
    /// <param name="innerStoreFactory">A callback that produces the inner <see cref="IVectorStore"/> that represents the underlying backend.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>A <see cref="VectorStoreBuilder"/> that can be used to build a pipeline around the inner store.</returns>
    /// <remarks>The store is registered as a singleton service.</remarks>
    public static VectorStoreBuilder AddVectorStore(
        this IServiceCollection serviceCollection,
        Func<IServiceProvider, IVectorStore> innerStoreFactory,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNull(serviceCollection);
        Verify.NotNull(innerStoreFactory);

        var builder = new VectorStoreBuilder(innerStoreFactory);
        serviceCollection.Add(new ServiceDescriptor(typeof(IVectorStore), builder.Build, lifetime));
        return builder;
    }

    /// <summary>Registers a keyed singleton <see cref="IVectorStore"/> in the <see cref="IServiceCollection"/>.</summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the store.</param>
    /// <param name="innerStore">The inner <see cref="IVectorStore"/> that represents the underlying backend.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>A <see cref="VectorStoreBuilder"/> that can be used to build a pipeline around the inner store.</returns>
    /// <remarks>The store is registered as a scoped service.</remarks>
    public static VectorStoreBuilder AddKeyedVectorStore(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        IVectorStore innerStore,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNull(serviceCollection);
        Verify.NotNull(innerStore);

        return AddKeyedVectorStore(serviceCollection, serviceKey, _ => innerStore, lifetime);
    }

    /// <summary>Registers a keyed singleton <see cref="IVectorStore"/> in the <see cref="IServiceCollection"/>.</summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the store.</param>
    /// <param name="innerStoreFactory">A callback that produces the inner <see cref="IVectorStore"/> that represents the underlying backend.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>A <see cref="VectorStoreBuilder"/> that can be used to build a pipeline around the inner store.</returns>
    /// <remarks>The store is registered as a scoped service.</remarks>
    public static VectorStoreBuilder AddKeyedVectorStore(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        Func<IServiceProvider, IVectorStore> innerStoreFactory,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNull(serviceCollection);
        Verify.NotNull(innerStoreFactory);

        var builder = new VectorStoreBuilder(innerStoreFactory);
        serviceCollection.Add(new ServiceDescriptor(typeof(IVectorStore), serviceKey, factory: (services, serviceKey) => builder.Build(services), lifetime));
        return builder;
    }
}
