// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Pinecone;
using Pinecone;

namespace Microsoft.Extensions.DependencyInjection;

/// <summary>
/// Extension methods to register <see cref="PineconeVectorStore"/> and <see cref="PineconeCollection{TKey, TRecord}"/> instances on an <see cref="IServiceCollection"/>.
/// </summary>
public static class PineconeServiceCollectionExtensions
{
    private const string DynamicCodeMessage = "This method is incompatible with NativeAOT, consult the documentation for adding collections in a way that's compatible with NativeAOT.";
    private const string UnreferencedCodeMessage = "This method is incompatible with trimming, consult the documentation for adding collections in a way that's compatible with NativeAOT.";

    /// <summary>
    /// Registers a <see cref="PineconeVectorStore"/> as <see cref="VectorStore"/>
    /// with <see cref="PineconeClient"/> retrieved from the dependency injection container.
    /// </summary>
    /// <inheritdoc cref="AddKeyedPineconeVectorStore(IServiceCollection, object?, PineconeVectorStoreOptions?, ServiceLifetime)"/>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddPineconeVectorStore(
        this IServiceCollection services,
        PineconeVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        => AddKeyedPineconeVectorStore(services, serviceKey: null, options, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="PineconeVectorStore"/> as <see cref="VectorStore"/>
    /// with <see cref="PineconeClient"/> retrieved from the dependency injection container.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="PineconeVectorStore"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="options">Optional options to further configure the <see cref="PineconeVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddKeyedPineconeVectorStore(
        this IServiceCollection services,
        object? serviceKey,
        PineconeVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNull(services);

        services.Add(new ServiceDescriptor(typeof(PineconeVectorStore), serviceKey, (sp, _) =>
        {
            var database = sp.GetRequiredService<PineconeClient>();
            options = GetStoreOptions(sp, _ => options);

            return new PineconeVectorStore(database, options);
        }, lifetime));

        services.Add(new ServiceDescriptor(typeof(VectorStore), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<PineconeVectorStore>(key), lifetime));

        return services;
    }

    /// <summary>
    /// Registers a <see cref="PineconeVectorStore"/> as <see cref="VectorStore"/>
    /// using the provided <paramref name="apiKey"/> and <paramref name="clientOptions"/>.
    /// </summary>
    /// <inheritdoc cref="AddKeyedPineconeVectorStore(IServiceCollection, object?, string, ClientOptions, PineconeVectorStoreOptions?, ServiceLifetime)"/>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddPineconeVectorStore(
        this IServiceCollection services,
        string apiKey,
        ClientOptions? clientOptions = default,
        PineconeVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        => AddKeyedPineconeVectorStore(services, serviceKey: null, apiKey, clientOptions, options, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="PineconeVectorStore"/> as <see cref="VectorStore"/>
    /// using the provided <paramref name="apiKey"/> and <paramref name="clientOptions"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="PineconeVectorStore"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="apiKey">API Key required to connect to PineconeDB.</param>
    /// <param name="clientOptions">The <see cref="ClientOptions"/> to configure <see cref="PineconeClient"/>.</param>
    /// <param name="options">Optional options to further configure the <see cref="PineconeVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddKeyedPineconeVectorStore(
        this IServiceCollection services,
        object? serviceKey,
        string apiKey,
        ClientOptions? clientOptions = default,
        PineconeVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(apiKey);

        services.Add(new ServiceDescriptor(typeof(PineconeVectorStore), serviceKey, (sp, _) =>
        {
            options = GetStoreOptions(sp, _ => options);
            PineconeClient client = new(apiKey, clientOptions);

            return new PineconeVectorStore(client, options);
        }, lifetime));

        services.Add(new ServiceDescriptor(typeof(VectorStore), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<PineconeVectorStore>(key), lifetime));

        return services;
    }

    /// <summary>
    /// Registers a <see cref="PineconeCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>
    /// with <see cref="PineconeClient"/> retrieved from the dependency injection container.
    /// </summary>
    /// <inheritdoc cref="AddKeyedPineconeVectorStore(IServiceCollection, object?, PineconeVectorStoreOptions?, ServiceLifetime)"/>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddPineconeCollection<TRecord>(
        this IServiceCollection services,
        string name,
        PineconeCollectionOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
        => AddKeyedPineconeCollection<TRecord>(services, serviceKey: null, name, options, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="PineconeCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>
    /// with <see cref="PineconeClient"/> retrieved from the dependency injection container.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="PineconeCollection{TKey, TRecord}"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the collection.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="options">Optional options to further configure the <see cref="PineconeCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddKeyedPineconeCollection<TRecord>(
        this IServiceCollection services,
        object? serviceKey,
        string name,
        PineconeCollectionOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(name);

        services.Add(new ServiceDescriptor(typeof(PineconeCollection<string, TRecord>), serviceKey, (sp, _) =>
        {
            var database = sp.GetRequiredService<PineconeClient>();
            options = GetCollectionOptions(sp, _ => options);

            return new PineconeCollection<string, TRecord>(database, name, options);
        }, lifetime));

        AddAbstractions<string, TRecord>(services, serviceKey, lifetime);

        return services;
    }

    /// <summary>
    /// Registers a <see cref="PineconeCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey,TRecord}"/>
    /// using the provided <paramref name="apiKey"/> and <paramref name="clientOptions"/>.
    /// </summary>
    /// <inheritdoc cref="AddKeyedPineconeCollection{TRecord}(IServiceCollection, object?, string, string, ClientOptions, PineconeCollectionOptions?, ServiceLifetime)"/>
    [RequiresUnreferencedCode(UnreferencedCodeMessage)]
    [RequiresDynamicCode(DynamicCodeMessage)]
    public static IServiceCollection AddPineconeCollection<TRecord>(
        this IServiceCollection services,
        string name,
        string apiKey,
        ClientOptions? clientOptions = default,
        PineconeCollectionOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
        => AddKeyedPineconeCollection<TRecord>(services, serviceKey: null, name, apiKey, clientOptions, options, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="PineconeCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey,TRecord}"/>
    /// using the provided <paramref name="apiKey"/> and <paramref name="clientOptions"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="PineconeCollection{TKey, TRecord}"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the collection.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="apiKey">API Key required to connect to PineconeDB.</param>
    /// <param name="clientOptions">The <see cref="ClientOptions"/> to configure <see cref="PineconeClient"/>.</param>
    /// <param name="options">Optional options to further configure the <see cref="PineconeCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(UnreferencedCodeMessage)]
    [RequiresDynamicCode(DynamicCodeMessage)]
    public static IServiceCollection AddKeyedPineconeCollection<TRecord>(
        this IServiceCollection services,
        object? serviceKey,
        string name,
        string apiKey,
        ClientOptions? clientOptions = default,
        PineconeCollectionOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
    {
        Verify.NotNullOrWhiteSpace(apiKey);

        return AddKeyedPineconeCollection<TRecord>(services, serviceKey, name, _ => apiKey, _ => clientOptions!, _ => options!, lifetime);
    }

    /// <summary>
    /// Registers a <see cref="PineconeCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey,TRecord}"/>
    /// using the provided <paramref name="apiKeyProvider"/> and <paramref name="clientOptionsProvider"/>.
    /// </summary>
    /// <inheritdoc cref="AddKeyedPineconeCollection{TRecord}(IServiceCollection, object?, string, Func{IServiceProvider, string}, Func{IServiceProvider, ClientOptions}, Func{IServiceProvider, PineconeCollectionOptions}?, ServiceLifetime)"/>
    [RequiresUnreferencedCode(UnreferencedCodeMessage)]
    [RequiresDynamicCode(DynamicCodeMessage)]
    public static IServiceCollection AddPineconeCollection<TRecord>(
        this IServiceCollection services,
        string name,
        Func<IServiceProvider, string> apiKeyProvider,
        Func<IServiceProvider, ClientOptions>? clientOptionsProvider = default,
        Func<IServiceProvider, PineconeCollectionOptions>? optionsProvider = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
        => AddKeyedPineconeCollection<TRecord>(services, serviceKey: null, name, apiKeyProvider, clientOptionsProvider, optionsProvider, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="PineconeCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey,TRecord}"/>
    /// using the provided <paramref name="apiKeyProvider"/> and <paramref name="clientOptionsProvider"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStoreCollection{TKey, TRecord}"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the collection.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="apiKeyProvider">The API Key provider.</param>
    /// <param name="clientOptionsProvider">The <see cref="ClientOptions" /> provider to configure <see cref="PineconeClient"/>.</param>
    /// <param name="optionsProvider">Options provider to further configure the collection.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(UnreferencedCodeMessage)]
    [RequiresDynamicCode(DynamicCodeMessage)]
    public static IServiceCollection AddKeyedPineconeCollection<TRecord>(
        this IServiceCollection services,
        object? serviceKey,
        string name,
        Func<IServiceProvider, string> apiKeyProvider,
        Func<IServiceProvider, ClientOptions>? clientOptionsProvider = default,
        Func<IServiceProvider, PineconeCollectionOptions>? optionsProvider = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(name);
        Verify.NotNull(apiKeyProvider);

        services.Add(new ServiceDescriptor(typeof(PineconeCollection<string, TRecord>), serviceKey, (sp, _) =>
        {
            var options = GetCollectionOptions(sp, optionsProvider);
            PineconeClient client = new(apiKeyProvider(sp), clientOptionsProvider?.Invoke(sp));

            return new PineconeCollection<string, TRecord>(client, name, options);
        }, lifetime));

        AddAbstractions<string, TRecord>(services, serviceKey, lifetime);

        return services;
    }

    private static void AddAbstractions<TKey, TRecord>(IServiceCollection services, object? serviceKey, ServiceLifetime lifetime)
        where TKey : notnull
        where TRecord : class
    {
        services.Add(new ServiceDescriptor(typeof(VectorStoreCollection<TKey, TRecord>), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<PineconeCollection<TKey, TRecord>>(key), lifetime));

        services.Add(new ServiceDescriptor(typeof(IVectorSearchable<TRecord>), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<PineconeCollection<TKey, TRecord>>(key), lifetime));
    }

    private static PineconeVectorStoreOptions? GetStoreOptions(IServiceProvider sp, Func<IServiceProvider, PineconeVectorStoreOptions?>? optionsProvider)
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

    private static PineconeCollectionOptions? GetCollectionOptions(IServiceProvider sp, Func<IServiceProvider, PineconeCollectionOptions?>? optionsProvider)
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
