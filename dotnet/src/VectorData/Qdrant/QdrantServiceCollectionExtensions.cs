// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Qdrant.Client;

namespace Microsoft.Extensions.DependencyInjection;

/// <summary>
/// Extension methods to register <see cref="QdrantVectorStore"/> and <see cref="QdrantCollection{TKey, TRecord}"/>  instances on an <see cref="IServiceCollection"/>.
/// </summary>
public static class QdrantServiceCollectionExtensions
{
    private const string DynamicCodeMessage = "This method is incompatible with NativeAOT, consult the documentation for adding collections in a way that's compatible with NativeAOT.";
    private const string UnreferencedCodeMessage = "This method is incompatible with trimming, consult the documentation for adding collections in a way that's compatible with NativeAOT.";

    /// <summary>
    /// Registers a <see cref="QdrantVectorStore"/> as <see cref="VectorStore"/>
    /// with <see cref="QdrantClient"/> returned by <paramref name="clientProvider"/>
    /// or retrieved from the dependency injection container if <paramref name="clientProvider"/> was not provided.
    /// </summary>
    /// <inheritdoc cref="AddKeyedQdrantVectorStore(IServiceCollection, object?, Func{IServiceProvider, QdrantClient}, Func{IServiceProvider, QdrantVectorStoreOptions}?, ServiceLifetime)"/>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddQdrantVectorStore(
        this IServiceCollection services,
        Func<IServiceProvider, QdrantClient>? clientProvider = default,
        Func<IServiceProvider, QdrantVectorStoreOptions>? optionsProvider = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        => AddKeyedQdrantVectorStore(services, serviceKey: null, clientProvider, optionsProvider, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="QdrantVectorStore"/> as <see cref="VectorStore"/>
    /// with <see cref="QdrantClient"/> returned by <paramref name="clientProvider"/> or retrieved from the dependency injection container if <paramref name="clientProvider"/> was not provided.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="QdrantVectorStore"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="clientProvider">The <see cref="QdrantClient"/> provider.</param>
    /// <param name="optionsProvider">Options provider to further configure the <see cref="QdrantVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddKeyedQdrantVectorStore(
        this IServiceCollection services,
        object? serviceKey,
        Func<IServiceProvider, QdrantClient>? clientProvider = default,
        Func<IServiceProvider, QdrantVectorStoreOptions>? optionsProvider = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNull(services);

        services.Add(new ServiceDescriptor(typeof(QdrantVectorStore), serviceKey, (sp, _) =>
        {
            var client = clientProvider is null ? sp.GetRequiredService<QdrantClient>() : clientProvider(sp);
            var options = GetStoreOptions(sp, optionsProvider);

            // The client was restored from the DI container, so we do not own it.
            return new QdrantVectorStore(client, ownsClient: false, options);
        }, lifetime));

        services.Add(new ServiceDescriptor(typeof(VectorStore), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<QdrantVectorStore>(key), lifetime));

        return services;
    }

    /// <summary>
    /// Registers a <see cref="QdrantVectorStore"/> as <see cref="VectorStore"/>
    /// with <see cref="QdrantClient"/> created with <paramref name="host"/>, <paramref name="port"/>,
    /// <paramref name="https"/> and <paramref name="https"/>.
    /// </summary>
    /// <inheritdoc cref="AddKeyedQdrantVectorStore(IServiceCollection, object?, Func{IServiceProvider, QdrantClient}, Func{IServiceProvider, QdrantVectorStoreOptions}?, ServiceLifetime)"/>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddQdrantVectorStore(
        this IServiceCollection services,
        string host,
        int port = 6334,
        bool https = true,
        string? apiKey = default,
        QdrantVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        => AddKeyedQdrantVectorStore(services, serviceKey: null, host, port, https, apiKey, options, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="QdrantVectorStore"/> as <see cref="VectorStore"/>
    /// with <see cref="QdrantClient"/> created with <paramref name="host"/>, <paramref name="port"/>,
    /// <paramref name="https"/> and <paramref name="https"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="QdrantVectorStore"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="host">The host to connect to.</param>
    /// <param name="port">The port to connect to. Defaults to 6334.</param>
    /// <param name="https">Whether to encrypt the connection using HTTPS. Defaults to <c>true</c>.</param>
    /// <param name="apiKey">The API key to use.</param>
    /// <param name="options">Options to further configure the <see cref="QdrantVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddKeyedQdrantVectorStore(
        this IServiceCollection services,
        object? serviceKey,
        string host,
        int port = 6334,
        bool https = true,
        string? apiKey = default,
        QdrantVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNullOrWhiteSpace(host);

        return AddKeyedQdrantVectorStore(services, serviceKey, _ => new QdrantClient(host, port, https, apiKey), sp => options!, lifetime);
    }

    /// <summary>
    /// Registers a <see cref="QdrantCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>
    /// with <see cref="QdrantClient"/> returned by <paramref name="clientProvider"/> or retrieved from the dependency injection container if <paramref name="clientProvider"/> was not provided.
    /// </summary>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddQdrantCollection<TKey, TRecord>(
        this IServiceCollection services,
        string name,
        Func<IServiceProvider, QdrantClient>? clientProvider = default,
        Func<IServiceProvider, QdrantCollectionOptions>? optionsProvider = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : class
        => AddKeyedQdrantCollection<TKey, TRecord>(services, serviceKey: null, name, clientProvider, optionsProvider, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="QdrantCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>
    /// with <see cref="QdrantClient"/> returned by <paramref name="clientProvider"/> or retrieved from the dependency injection container if <paramref name="clientProvider"/> was not provided.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="QdrantCollection{TKey, TRecord}"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the collection.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="clientProvider">The <see cref="QdrantClient"/> provider.</param>
    /// <param name="optionsProvider">Options provider to further configure the <see cref="QdrantCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddKeyedQdrantCollection<TKey, TRecord>(
        this IServiceCollection services,
        object? serviceKey,
        string name,
        Func<IServiceProvider, QdrantClient>? clientProvider = default,
        Func<IServiceProvider, QdrantCollectionOptions>? optionsProvider = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : class
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(name);

        services.Add(new ServiceDescriptor(typeof(QdrantCollection<TKey, TRecord>), serviceKey, (sp, _) =>
        {
            var client = clientProvider is null ? sp.GetRequiredService<QdrantClient>() : clientProvider(sp);
            var options = GetCollectionOptions(sp, optionsProvider);

            // The client was restored from the DI container, so we do not own it.
            return new QdrantCollection<TKey, TRecord>(client, name, ownsClient: false, options);
        }, lifetime));

        services.Add(new ServiceDescriptor(typeof(VectorStoreCollection<TKey, TRecord>), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<QdrantCollection<TKey, TRecord>>(key), lifetime));

        services.Add(new ServiceDescriptor(typeof(IVectorSearchable<TRecord>), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<QdrantCollection<TKey, TRecord>>(key), lifetime));

        services.Add(new ServiceDescriptor(typeof(IKeywordHybridSearchable<TRecord>), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<QdrantCollection<TKey, TRecord>>(key), lifetime));

        return services;
    }

    /// <summary>
    /// Registers a <see cref="QdrantCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>
    /// with <see cref="QdrantClient"/> created with <paramref name="host"/>, <paramref name="port"/>,
    /// <paramref name="https"/> and <paramref name="https"/>.
    /// </summary>
    /// <inheritdoc cref="AddKeyedQdrantCollection{TKey, TRecord}(IServiceCollection, object?, string, string, int, bool, string?, QdrantCollectionOptions?, ServiceLifetime)"/>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddQdrantCollection<TKey, TRecord>(
        this IServiceCollection services,
        string name,
        string host,
        int port = 6334,
        bool https = true,
        string? apiKey = default,
        QdrantCollectionOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : class
        => AddKeyedQdrantCollection<TKey, TRecord>(services, serviceKey: null, name, host, port, https, apiKey, options, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="QdrantCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>
    /// with <see cref="QdrantClient"/> created with <paramref name="host"/>, <paramref name="port"/>,
    /// <paramref name="https"/> and <paramref name="https"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="QdrantCollection{TKey, TRecord}"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the collection.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="host">The host to connect to.</param>
    /// <param name="port">The port to connect to. Defaults to 6334.</param>
    /// <param name="https">Whether to encrypt the connection using HTTPS. Defaults to <c>true</c>.</param>
    /// <param name="apiKey">The API key to use.</param>
    /// <param name="options">Options to further configure the <see cref="QdrantCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddKeyedQdrantCollection<TKey, TRecord>(
        this IServiceCollection services,
        object? serviceKey,
        string name,
        string host,
        int port = 6334,
        bool https = true,
        string? apiKey = default,
        QdrantCollectionOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : class
    {
        Verify.NotNullOrWhiteSpace(host);

        return AddKeyedQdrantCollection<TKey, TRecord>(services, serviceKey, name, _ => new QdrantClient(host, port, https, apiKey), sp => options!, lifetime);
    }

    private static QdrantVectorStoreOptions? GetStoreOptions(IServiceProvider sp, Func<IServiceProvider, QdrantVectorStoreOptions?>? optionsProvider)
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

    private static QdrantCollectionOptions? GetCollectionOptions(IServiceProvider sp, Func<IServiceProvider, QdrantCollectionOptions?>? optionsProvider)
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
