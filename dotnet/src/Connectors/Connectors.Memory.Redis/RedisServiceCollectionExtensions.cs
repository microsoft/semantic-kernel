// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Redis;
using StackExchange.Redis;

namespace Microsoft.Extensions.DependencyInjection;

/// <summary>
/// Extension methods to register <see cref="RedisVectorStore"/>, <see cref="RedisJsonCollection{TKey, TRecord}"/> and <see cref="RedisHashSetCollection{TKey, TRecord}"/> instances on an <see cref="IServiceCollection"/>.
/// </summary>
public static class RedisServiceCollectionExtensions
{
    private const string DynamicCodeMessage = "This method is incompatible with NativeAOT, consult the documentation for adding collections in a way that's compatible with NativeAOT.";
    private const string UnreferencedCodeMessage = "This method is incompatible with trimming, consult the documentation for adding collections in a way that's compatible with NativeAOT.";

    /// <summary>
    /// Registers a <see cref="RedisVectorStore"/> as <see cref="VectorStore"/>
    /// with <see cref="IDatabase"/> returned by <paramref name="clientProvider"/> or retrieved from the dependency injection container if <paramref name="clientProvider"/> was not provided.
    /// </summary>
    /// <inheritdoc cref="AddKeyedRedisVectorStore(IServiceCollection, object?, Func{IServiceProvider, IDatabase}, Func{IServiceProvider, RedisVectorStoreOptions}?, ServiceLifetime)"/>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddRedisVectorStore(
        this IServiceCollection services,
        Func<IServiceProvider, IDatabase>? clientProvider = default,
        Func<IServiceProvider, RedisVectorStoreOptions>? optionsProvider = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        => AddKeyedRedisVectorStore(services, serviceKey: null, clientProvider, optionsProvider, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="RedisVectorStore"/> as <see cref="VectorStore"/>
    /// with <see cref="IDatabase"/> returned by <paramref name="clientProvider"/> or retrieved from the dependency injection container if <paramref name="clientProvider"/> was not provided.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="RedisVectorStore"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="clientProvider">The <see cref="IDatabase"/> provider.</param>
    /// <param name="optionsProvider">Options provider to further configure the <see cref="RedisVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddKeyedRedisVectorStore(
        this IServiceCollection services,
        object? serviceKey,
        Func<IServiceProvider, IDatabase>? clientProvider = default,
        Func<IServiceProvider, RedisVectorStoreOptions>? optionsProvider = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNull(services);

        services.Add(new ServiceDescriptor(typeof(RedisVectorStore), serviceKey, (sp, _) =>
        {
            var client = clientProvider is null ? sp.GetRequiredService<IDatabase>() : clientProvider(sp);
            var options = GetStoreOptions(sp, optionsProvider);

            return new RedisVectorStore(client, options);
        }, lifetime));

        services.Add(new ServiceDescriptor(typeof(VectorStore), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<RedisVectorStore>(key), lifetime));

        return services;
    }

    /// <summary>
    /// Registers a <see cref="RedisVectorStore"/> as <see cref="VectorStore"/>
    /// with <see cref="IDatabase"/> created with <paramref name="connectionConfiguration"/>.
    /// </summary>
    /// <inheritdoc cref="AddKeyedRedisVectorStore(IServiceCollection, object?, Func{IServiceProvider, IDatabase}, Func{IServiceProvider, RedisVectorStoreOptions}?, ServiceLifetime)"/>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddRedisVectorStore(
        this IServiceCollection services,
        string connectionConfiguration,
        RedisVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        => AddKeyedRedisVectorStore(services, serviceKey: null, connectionConfiguration, options, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="RedisVectorStore"/> as <see cref="VectorStore"/>
    /// with <see cref="IDatabase"/> created with <paramref name="connectionConfiguration"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="RedisVectorStore"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="connectionConfiguration">The connectionConfiguration passed to <see cref="ConnectionMultiplexer.Connect(string, TextWriter)"/>.</param>
    /// <param name="options">Options to further configure the <see cref="RedisVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddKeyedRedisVectorStore(
        this IServiceCollection services,
        object? serviceKey,
        string connectionConfiguration,
        RedisVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNullOrWhiteSpace(connectionConfiguration);

        return AddKeyedRedisVectorStore(services, serviceKey, _ => ConnectionMultiplexer.Connect(connectionConfiguration).GetDatabase(), sp => options!, lifetime);
    }

    /// <summary>
    /// Registers a <see cref="RedisJsonCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>
    /// with <see cref="IDatabase"/> returned by <paramref name="clientProvider"/> or retrieved from the dependency injection container if <paramref name="clientProvider"/> was not provided.
    /// </summary>
    /// <inheritdoc cref="AddKeyedRedisJsonCollection{TRecord}(IServiceCollection, object?, string, Func{IServiceProvider, IDatabase}, Func{IServiceProvider, RedisJsonCollectionOptions}?, ServiceLifetime)"/>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddRedisJsonCollection<TRecord>(
        this IServiceCollection services,
        string name,
        Func<IServiceProvider, IDatabase>? clientProvider = default,
        Func<IServiceProvider, RedisJsonCollectionOptions>? optionsProvider = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
        => AddKeyedRedisJsonCollection<TRecord>(services, serviceKey: null, name, clientProvider, optionsProvider, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="RedisJsonCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>
    /// with <see cref="IDatabase"/> returned by <paramref name="clientProvider"/> or retrieved from the dependency injection container if <paramref name="clientProvider"/> was not provided.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="RedisJsonCollection{TKey, TRecord}"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the collection.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="clientProvider">The <see cref="IDatabase"/> provider.</param>
    /// <param name="optionsProvider">Options provider to further configure the <see cref="RedisJsonCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddKeyedRedisJsonCollection<TRecord>(
        this IServiceCollection services,
        object? serviceKey,
        string name,
        Func<IServiceProvider, IDatabase>? clientProvider = default,
        Func<IServiceProvider, RedisJsonCollectionOptions>? optionsProvider = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(name);

        services.Add(new ServiceDescriptor(typeof(RedisJsonCollection<string, TRecord>), serviceKey, (sp, _) =>
        {
            var client = clientProvider is null ? sp.GetRequiredService<IDatabase>() : clientProvider(sp);
            var options = GetCollectionOptions(sp, optionsProvider);

            return new RedisJsonCollection<string, TRecord>(client, name, options);
        }, lifetime));

        services.Add(new ServiceDescriptor(typeof(VectorStoreCollection<string, TRecord>), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<RedisJsonCollection<string, TRecord>>(key), lifetime));

        services.Add(new ServiceDescriptor(typeof(IVectorSearchable<TRecord>), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<RedisJsonCollection<string, TRecord>>(key), lifetime));

        return services;
    }

    /// <summary>
    /// Registers a <see cref="RedisJsonCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>
    /// with <see cref="IDatabase"/> created with <paramref name="connectionConfiguration"/>.
    /// </summary>
    /// <inheritdoc cref="AddKeyedRedisJsonCollection{TRecord}(IServiceCollection, object?, string, string, RedisJsonCollectionOptions, ServiceLifetime)"/>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddRedisJsonCollection<TRecord>(
        this IServiceCollection services,
        string name,
        string connectionConfiguration,
        RedisJsonCollectionOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
        => AddKeyedRedisJsonCollection<TRecord>(services, serviceKey: null, name, connectionConfiguration, options, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="RedisJsonCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>
    /// with <see cref="IDatabase"/> created with <paramref name="connectionConfiguration"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="RedisJsonCollection{TKey, TRecord}"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the collection.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="connectionConfiguration">The connectionConfiguration passed to <see cref="ConnectionMultiplexer.Connect(string, TextWriter)"/>.</param>
    /// <param name="options">Options to further configure the <see cref="RedisJsonCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddKeyedRedisJsonCollection<TRecord>(
        this IServiceCollection services,
        object? serviceKey,
        string name,
        string connectionConfiguration,
        RedisJsonCollectionOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
    {
        Verify.NotNullOrWhiteSpace(connectionConfiguration);

        return AddKeyedRedisJsonCollection<TRecord>(
            services,
            serviceKey,
            name,
            _ => ConnectionMultiplexer.Connect(connectionConfiguration).GetDatabase(),
            sp => options!,
            lifetime);
    }

    /// <summary>
    /// Registers a <see cref="RedisHashSetCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>
    /// with <see cref="IDatabase"/> returned by <paramref name="clientProvider"/> or retrieved from the dependency injection container if <paramref name="clientProvider"/> was not provided.
    /// </summary>
    /// <inheritdoc cref="AddKeyedRedisHashSetCollection{TRecord}(IServiceCollection, object?, string, Func{IServiceProvider, IDatabase}, Func{IServiceProvider, RedisHashSetCollectionOptions}?, ServiceLifetime)"/>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddRedisHashSetCollection<TRecord>(
        this IServiceCollection services,
        string name,
        Func<IServiceProvider, IDatabase>? clientProvider = default,
        Func<IServiceProvider, RedisHashSetCollectionOptions>? optionsProvider = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
        => AddKeyedRedisHashSetCollection<TRecord>(services, serviceKey: null, name, clientProvider, optionsProvider, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="RedisHashSetCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>
    /// with <see cref="IDatabase"/> returned by <paramref name="clientProvider"/> or retrieved from the dependency injection container if <paramref name="clientProvider"/> was not provided.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="RedisHashSetCollection{TKey, TRecord}"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the collection.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="clientProvider">The <see cref="IDatabase"/> provider.</param>
    /// <param name="optionsProvider">Options provider to further configure the <see cref="RedisHashSetCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddKeyedRedisHashSetCollection<TRecord>(
        this IServiceCollection services,
        object? serviceKey,
        string name,
        Func<IServiceProvider, IDatabase>? clientProvider = default,
        Func<IServiceProvider, RedisHashSetCollectionOptions>? optionsProvider = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(name);

        services.Add(new ServiceDescriptor(typeof(RedisHashSetCollection<string, TRecord>), serviceKey, (sp, _) =>
        {
            var client = clientProvider is null ? sp.GetRequiredService<IDatabase>() : clientProvider(sp);
            var options = GetCollectionOptions(sp, optionsProvider);

            return new RedisHashSetCollection<string, TRecord>(client, name, options);
        }, lifetime));

        services.Add(new ServiceDescriptor(typeof(VectorStoreCollection<string, TRecord>), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<RedisHashSetCollection<string, TRecord>>(key), lifetime));

        services.Add(new ServiceDescriptor(typeof(IVectorSearchable<TRecord>), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<RedisHashSetCollection<string, TRecord>>(key), lifetime));

        return services;
    }

    /// <summary>
    /// Registers a <see cref="RedisHashSetCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>
    /// with <see cref="IDatabase"/> created with <paramref name="connectionConfiguration"/>.
    /// </summary>
    /// <inheritdoc cref="AddKeyedRedisHashSetCollection{TRecord}(IServiceCollection, object?, string, string, RedisHashSetCollectionOptions, ServiceLifetime)"/>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddRedisHashSetCollection<TRecord>(
        this IServiceCollection services,
        string name,
        string connectionConfiguration,
        RedisHashSetCollectionOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
        => AddKeyedRedisHashSetCollection<TRecord>(services, serviceKey: null, name, connectionConfiguration, options, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="RedisHashSetCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>
    /// with <see cref="IDatabase"/> created with <paramref name="connectionConfiguration"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="RedisHashSetCollection{TKey, TRecord}"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the collection.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="connectionConfiguration">The connectionConfiguration passed to <see cref="ConnectionMultiplexer.Connect(string, TextWriter)"/>.</param>
    /// <param name="options">Options to further configure the <see cref="RedisHashSetCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddKeyedRedisHashSetCollection<TRecord>(
        this IServiceCollection services,
        object? serviceKey,
        string name,
        string connectionConfiguration,
        RedisHashSetCollectionOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
    {
        Verify.NotNullOrWhiteSpace(connectionConfiguration);

        return AddKeyedRedisHashSetCollection<TRecord>(
            services,
            serviceKey,
            name,
            _ => ConnectionMultiplexer.Connect(connectionConfiguration).GetDatabase(),
            sp => options!,
            lifetime);
    }

    private static RedisVectorStoreOptions? GetStoreOptions(IServiceProvider sp, Func<IServiceProvider, RedisVectorStoreOptions?>? optionsProvider)
    {
        var options = optionsProvider?.Invoke(sp);
        if (options?.EmbeddingGenerator is not null)
        {
            return options; // The user has provided everything, there is nothing to change.
        }

        var embeddingGenerator = sp.GetService<IEmbeddingGenerator>();
        return embeddingGenerator is null
            ? options // There is nothing to change.
            : new(options) { EmbeddingGenerator = embeddingGenerator }; // Create a brand new copy in order to avoid modifying the original options.
    }

    private static RedisJsonCollectionOptions? GetCollectionOptions(IServiceProvider sp, Func<IServiceProvider, RedisJsonCollectionOptions?>? optionsProvider)
    {
        var options = optionsProvider?.Invoke(sp);
        if (options?.EmbeddingGenerator is not null)
        {
            return options; // The user has provided everything, there is nothing to change.
        }

        var embeddingGenerator = sp.GetService<IEmbeddingGenerator>();
        return embeddingGenerator is null
            ? options // There is nothing to change.
            : new(options) { EmbeddingGenerator = embeddingGenerator }; // Create a brand new copy in order to avoid modifying the original options.
    }

    private static RedisHashSetCollectionOptions? GetCollectionOptions(IServiceProvider sp, Func<IServiceProvider, RedisHashSetCollectionOptions?>? optionsProvider)
    {
        var options = optionsProvider?.Invoke(sp);
        if (options?.EmbeddingGenerator is not null)
        {
            return options; // The user has provided everything, there is nothing to change.
        }

        var embeddingGenerator = sp.GetService<IEmbeddingGenerator>();
        return embeddingGenerator is null
            ? options // There is nothing to change.
            : new(options) { EmbeddingGenerator = embeddingGenerator }; // Create a brand new copy in order to avoid modifying the original options.
    }
}
