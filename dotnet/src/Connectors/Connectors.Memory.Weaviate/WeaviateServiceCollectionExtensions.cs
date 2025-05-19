// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Weaviate;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.Extensions.DependencyInjection;

/// <summary>
/// Extension methods to register <see cref="WeaviateVectorStore"/> and <see cref="WeaviateCollection{TKey, TRecord}"/> instances on an <see cref="IServiceCollection"/>
/// </summary>
public static class WeaviateServiceCollectionExtensions
{
    private const string DynamicCodeMessage = "This method is incompatible with NativeAOT, consult the documentation for adding collections in a way that's compatible with NativeAOT.";
    private const string UnreferencedCodeMessage = "This method is incompatible with trimming, consult the documentation for adding collections in a way that's compatible with NativeAOT.";

    /// <summary>
    /// Registers a <see cref="WeaviateVectorStore"/> as <see cref="VectorStore"/>
    /// with <see cref="HttpClient"/> returned by <paramref name="clientProvider"/>
    /// or retrieved from the dependency injection container if <paramref name="clientProvider"/> was not provided.
    /// </summary>
    /// <inheritdoc cref="AddKeyedWeaviateVectorStore(IServiceCollection, object?, Func{IServiceProvider, HttpClient}, Func{IServiceProvider, WeaviateVectorStoreOptions}?, ServiceLifetime)"/>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddWeaviateVectorStore(
        this IServiceCollection services,
        Func<IServiceProvider, HttpClient>? clientProvider = default,
        Func<IServiceProvider, WeaviateVectorStoreOptions>? optionsProvider = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        => AddKeyedWeaviateVectorStore(services, serviceKey: null, clientProvider, optionsProvider, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="WeaviateVectorStore"/> as <see cref="VectorStore"/>
    /// with <see cref="HttpClient"/> returned by <paramref name="clientProvider"/>
    /// or retrieved from the dependency injection container if <paramref name="clientProvider"/> was not provided.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="WeaviateVectorStore"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="clientProvider">The <see cref="HttpClient"/> provider.</param>
    /// <param name="optionsProvider">Options provider to further configure the <see cref="WeaviateVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddKeyedWeaviateVectorStore(
        this IServiceCollection services,
        object? serviceKey,
        Func<IServiceProvider, HttpClient>? clientProvider = default,
        Func<IServiceProvider, WeaviateVectorStoreOptions>? optionsProvider = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNull(services);

        services.Add(new ServiceDescriptor(typeof(WeaviateVectorStore), serviceKey, (sp, _) =>
        {
            var client = HttpClientProvider.GetHttpClient(clientProvider?.Invoke(sp), sp);
            var options = GetStoreOptions(sp, optionsProvider ?? (static s => s.GetService<WeaviateVectorStoreOptions>()!));

            return new WeaviateVectorStore(client, options);
        }, lifetime));

        services.Add(new ServiceDescriptor(typeof(VectorStore), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<WeaviateVectorStore>(key), lifetime));

        return services;
    }

    /// <summary>
    /// Registers a <see cref="WeaviateVectorStore"/> as <see cref="VectorStore"/>
    /// with <see cref="WeaviateVectorStoreOptions"/> created with <paramref name="endpoint"/>, <paramref name="apiKey"/>.
    /// </summary>
    /// <inheritdoc cref="AddKeyedWeaviateVectorStore(IServiceCollection, object?, Func{IServiceProvider, HttpClient}, Func{IServiceProvider, WeaviateVectorStoreOptions}?, ServiceLifetime)"/>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddWeaviateVectorStore(
        this IServiceCollection services,
        Uri endpoint,
        string? apiKey,
        WeaviateVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        => AddKeyedWeaviateVectorStore(services, serviceKey: null, endpoint, apiKey, options, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="WeaviateVectorStore"/> as <see cref="VectorStore"/>
    /// with <see cref="WeaviateVectorStoreOptions"/> created with <paramref name="endpoint"/>, <paramref name="apiKey"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="WeaviateVectorStore"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="endpoint">The endpoint to connect to.</param>
    /// <param name="apiKey">The API key to use.</param>
    /// <param name="options">Options to further configure the <see cref="WeaviateVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddKeyedWeaviateVectorStore(
        this IServiceCollection services,
        object? serviceKey,
        Uri endpoint,
        string? apiKey,
        WeaviateVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNull(endpoint);

        WeaviateVectorStoreOptions copy = new(options)
        {
            Endpoint = endpoint,
            ApiKey = apiKey
        };

        return AddKeyedWeaviateVectorStore(services, serviceKey, sp => HttpClientProvider.GetHttpClient(null, sp), sp => copy, lifetime);
    }

    /// <summary>
    /// Registers a <see cref="WeaviateCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>
    /// with <see cref="HttpClient"/> returned by <paramref name="clientProvider"/>
    /// or retrieved from the dependency injection container if <paramref name="clientProvider"/> was not provided.
    /// </summary>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddWeaviateCollection<TRecord>(
        this IServiceCollection services,
        string name,
        Func<IServiceProvider, HttpClient>? clientProvider = default,
        Func<IServiceProvider, WeaviateCollectionOptions>? optionsProvider = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
        => AddKeyedWeaviateCollection<TRecord>(services, serviceKey: null, name, clientProvider, optionsProvider, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="WeaviateCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>
    /// with <see cref="HttpClient"/> returned by <paramref name="clientProvider"/>
    /// or retrieved from the dependency injection container if <paramref name="clientProvider"/> was not provided.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="WeaviateCollection{TKey, TRecord}"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the collection.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="clientProvider">The <see cref="HttpClient"/> provider.</param>
    /// <param name="optionsProvider">Options provider to further configure the <see cref="WeaviateCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddKeyedWeaviateCollection<TRecord>(
        this IServiceCollection services,
        object? serviceKey,
        string name,
        Func<IServiceProvider, HttpClient>? clientProvider = default,
        Func<IServiceProvider, WeaviateCollectionOptions>? optionsProvider = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(name);

        services.Add(new ServiceDescriptor(typeof(WeaviateCollection<Guid, TRecord>), serviceKey, (sp, _) =>
        {
            var client = HttpClientProvider.GetHttpClient(clientProvider?.Invoke(sp), sp);
            var options = GetCollectionOptions(sp, optionsProvider ?? (static s => s.GetService<WeaviateCollectionOptions>()!));

            return new WeaviateCollection<Guid, TRecord>(client, name, options);
        }, lifetime));

        services.Add(new ServiceDescriptor(typeof(VectorStoreCollection<Guid, TRecord>), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<WeaviateCollection<Guid, TRecord>>(key), lifetime));

        services.Add(new ServiceDescriptor(typeof(IVectorSearchable<TRecord>), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<WeaviateCollection<Guid, TRecord>>(key), lifetime));

        services.Add(new ServiceDescriptor(typeof(IKeywordHybridSearchable<TRecord>), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<WeaviateCollection<Guid, TRecord>>(key), lifetime));

        return services;
    }

    /// <summary>
    /// Registers a <see cref="WeaviateCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>
    /// with <see cref="WeaviateCollectionOptions"/> created with <paramref name="endpoint"/>, <paramref name="apiKey"/>.
    /// </summary>
    /// <inheritdoc cref="AddKeyedWeaviateCollection{TRecord}(IServiceCollection, object?, string, Uri, string?, WeaviateCollectionOptions?, ServiceLifetime)"/>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddWeaviateCollection<TRecord>(
        this IServiceCollection services,
        string name,
        Uri endpoint,
        string? apiKey,
        WeaviateCollectionOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
        => AddKeyedWeaviateCollection<TRecord>(services, serviceKey: null, name, endpoint, apiKey, options, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="WeaviateCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>
    /// with <see cref="WeaviateCollectionOptions"/> created with <paramref name="endpoint"/>, <paramref name="apiKey"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="WeaviateCollection{TKey, TRecord}"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the collection.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="endpoint">The endpoint to connect to.</param>
    /// <param name="apiKey">The API key to use.</param>
    /// <param name="options">Options to further configure the <see cref="WeaviateCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddKeyedWeaviateCollection<TRecord>(
        this IServiceCollection services,
        object? serviceKey,
        string name,
        Uri endpoint,
        string? apiKey,
        WeaviateCollectionOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
    {
        Verify.NotNull(endpoint);

        WeaviateCollectionOptions copy = new(options)
        {
            Endpoint = endpoint,
            ApiKey = apiKey
        };

        return AddKeyedWeaviateCollection<TRecord>(services, serviceKey, name, sp => HttpClientProvider.GetHttpClient(null, sp), sp => copy, lifetime);
    }

    private static WeaviateVectorStoreOptions? GetStoreOptions(IServiceProvider sp, Func<IServiceProvider, WeaviateVectorStoreOptions?>? optionsProvider)
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

    private static WeaviateCollectionOptions? GetCollectionOptions(IServiceProvider sp, Func<IServiceProvider, WeaviateCollectionOptions?>? optionsProvider)
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
