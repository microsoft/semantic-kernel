// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using Azure;
using Azure.Core;
using Azure.Core.Serialization;
using Azure.Search.Documents;
using Azure.Search.Documents.Indexes;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.Extensions.DependencyInjection;

/// <summary>
/// Extension methods to register <see cref="AzureAISearchVectorStore"/> and <see cref="AzureAISearchCollection{TKey, TRecord}"/> instances on an <see cref="IServiceCollection"/>.
/// </summary>
public static class AzureAISearchServiceCollectionExtensions
{
    private const string DynamicCodeMessage = "The Azure AI Search provider is currently incompatible with trimming.";
    private const string UnreferencedCodeMessage = "The Azure AI Search provider is currently incompatible with NativeAOT.";

    /// <summary>
    /// Registers a <see cref="AzureAISearchVectorStore"/> as <see cref="VectorStore"/>
    /// with <see cref="SearchIndexClient"/> returned by <paramref name="clientProvider"/>
    /// or retrieved from the dependency injection container if <paramref name="clientProvider"/> was not provided.
    /// </summary>
    /// <inheritdoc cref="AddKeyedAzureAISearchVectorStore(IServiceCollection, object?, Func{IServiceProvider, SearchIndexClient}, Func{IServiceProvider, AzureAISearchVectorStoreOptions}?, ServiceLifetime)"/>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddAzureAISearchVectorStore(
        this IServiceCollection services,
        Func<IServiceProvider, SearchIndexClient>? clientProvider = default,
        Func<IServiceProvider, AzureAISearchVectorStoreOptions>? optionsProvider = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        => AddKeyedAzureAISearchVectorStore(services, serviceKey: null, clientProvider, optionsProvider, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="AzureAISearchVectorStore"/> as <see cref="VectorStore"/>
    /// with <see cref="SearchIndexClient"/> returned by <paramref name="clientProvider"/>
    /// or retrieved from the dependency injection container if <paramref name="clientProvider"/> was not provided.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="AzureAISearchVectorStore"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="clientProvider">The <see cref="SearchIndexClient"/> provider.</param>
    /// <param name="optionsProvider">Options provider to further configure the <see cref="AzureAISearchVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddKeyedAzureAISearchVectorStore(
        this IServiceCollection services,
        object? serviceKey,
        Func<IServiceProvider, SearchIndexClient>? clientProvider = default,
        Func<IServiceProvider, AzureAISearchVectorStoreOptions>? optionsProvider = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNull(services);

        services.Add(new ServiceDescriptor(typeof(AzureAISearchVectorStore), serviceKey, (sp, _) =>
        {
            var client = clientProvider is not null ? clientProvider(sp) : sp.GetRequiredService<SearchIndexClient>();
            var options = GetStoreOptions(sp, optionsProvider);

            return new AzureAISearchVectorStore(client, options);
        }, lifetime));

        services.Add(new ServiceDescriptor(typeof(VectorStore), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<AzureAISearchVectorStore>(key), lifetime));

        return services;
    }

    /// <summary>
    /// Registers a <see cref="AzureAISearchVectorStore"/> as <see cref="VectorStore"/>
    /// using the provided <paramref name="endpoint"/> and <paramref name="tokenCredential"/>.
    /// </summary>
    /// <inheritdoc cref="AddKeyedAzureAISearchVectorStore(IServiceCollection, object?, Uri, TokenCredential, AzureAISearchVectorStoreOptions?, ServiceLifetime)"/>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddAzureAISearchVectorStore(
        this IServiceCollection services,
        Uri endpoint,
        TokenCredential tokenCredential,
        AzureAISearchVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        => AddKeyedAzureAISearchVectorStore(services, serviceKey: null, endpoint, tokenCredential, options, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="AzureAISearchVectorStore"/> as <see cref="VectorStore"/>
    /// using the provided <paramref name="endpoint"/> and <paramref name="tokenCredential"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="AzureAISearchVectorStore"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="endpoint">The service endpoint for Azure AI Search.</param>
    /// <param name="tokenCredential">The credential to authenticate to Azure AI Search with.</param>
    /// <param name="options">Optional options to further configure the <see cref="AzureAISearchVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddKeyedAzureAISearchVectorStore(
        this IServiceCollection services,
        object? serviceKey,
        Uri endpoint,
        TokenCredential tokenCredential,
        AzureAISearchVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNull(endpoint);
        Verify.NotNull(tokenCredential);

        return AddKeyedAzureAISearchVectorStore(services, serviceKey, sp =>
        {
            var searchClientOptions = BuildSearchClientOptions(options?.JsonSerializerOptions);
            return new SearchIndexClient(endpoint, tokenCredential, searchClientOptions);
        }, _ => options!, lifetime);
    }

    /// <summary>
    /// Registers a <see cref="AzureAISearchVectorStore"/> as <see cref="VectorStore"/>
    /// using the provided <paramref name="endpoint"/> and <paramref name="keyCredential"/>.
    /// </summary>
    /// <inheritdoc cref="AddKeyedAzureAISearchVectorStore(IServiceCollection, object?, Uri, AzureKeyCredential, AzureAISearchVectorStoreOptions?, ServiceLifetime)"/>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddAzureAISearchVectorStore(
        this IServiceCollection services,
        Uri endpoint,
        AzureKeyCredential keyCredential,
        AzureAISearchVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        => AddKeyedAzureAISearchVectorStore(services, serviceKey: null, endpoint, keyCredential, options, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="AzureAISearchVectorStore"/> as <see cref="VectorStore"/>
    /// using the provided <paramref name="endpoint"/> and <paramref name="keyCredential"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="AzureAISearchVectorStore"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="endpoint">The service endpoint for Azure AI Search.</param>
    /// <param name="keyCredential">The credential to authenticate to Azure AI Search with.</param>
    /// <param name="options">Optional options to further configure the <see cref="AzureAISearchVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddKeyedAzureAISearchVectorStore(
        this IServiceCollection services,
        object? serviceKey,
        Uri endpoint,
        AzureKeyCredential keyCredential,
        AzureAISearchVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNull(endpoint);
        Verify.NotNull(keyCredential);

        return AddKeyedAzureAISearchVectorStore(services, serviceKey, sp =>
        {
            var searchClientOptions = BuildSearchClientOptions(options?.JsonSerializerOptions);
            return new SearchIndexClient(endpoint, keyCredential, searchClientOptions);
        }, _ => options!, lifetime);
    }

    /// <summary>
    /// Registers a <see cref="AzureAISearchCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>
    /// with <see cref="SearchIndexClient"/> returned by <paramref name="clientProvider"/>
    /// or retrieved from the dependency injection container if <paramref name="clientProvider"/> was not provided.
    /// </summary>
    /// <inheritdoc cref="AddKeyedAzureAISearchCollection{TRecord}(IServiceCollection, object?, string, Func{IServiceProvider, SearchIndexClient}, Func{IServiceProvider, AzureAISearchCollectionOptions}?, ServiceLifetime)"/>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddAzureAISearchCollection<TRecord>(
        this IServiceCollection services,
        string name,
        Func<IServiceProvider, SearchIndexClient>? clientProvider = default,
        Func<IServiceProvider, AzureAISearchCollectionOptions>? optionsProvider = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
        => AddKeyedAzureAISearchCollection<TRecord>(services, serviceKey: null, name, clientProvider, optionsProvider, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="AzureAISearchCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>
    /// with <see cref="SearchIndexClient"/> returned by <paramref name="clientProvider"/>
    /// or retrieved from the dependency injection container if <paramref name="clientProvider"/> was not provided.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="AzureAISearchCollection{TKey, TRecord}"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the collection.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="clientProvider">The <see cref="SearchIndexClient"/> provider.</param>
    /// <param name="optionsProvider">Options provider to further configure the <see cref="AzureAISearchCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddKeyedAzureAISearchCollection<TRecord>(
        this IServiceCollection services,
        object? serviceKey,
        string name,
        Func<IServiceProvider, SearchIndexClient>? clientProvider = default,
        Func<IServiceProvider, AzureAISearchCollectionOptions>? optionsProvider = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(name);

        services.Add(new ServiceDescriptor(typeof(AzureAISearchCollection<string, TRecord>), serviceKey, (sp, _) =>
        {
            var client = clientProvider is not null ? clientProvider(sp) : sp.GetRequiredService<SearchIndexClient>();
            var options = GetCollectionOptions(sp, optionsProvider);

            return new AzureAISearchCollection<string, TRecord>(client, name, options);
        }, lifetime));

        services.Add(new ServiceDescriptor(typeof(VectorStoreCollection<string, TRecord>), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<AzureAISearchCollection<string, TRecord>>(key), lifetime));

        services.Add(new ServiceDescriptor(typeof(IVectorSearchable<TRecord>), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<AzureAISearchCollection<string, TRecord>>(key), lifetime));

        services.Add(new ServiceDescriptor(typeof(IKeywordHybridSearchable<TRecord>), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<AzureAISearchCollection<string, TRecord>>(key), lifetime));

        return services;
    }

    /// <summary>
    /// Registers a <see cref="AzureAISearchCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>
    /// using the provided <paramref name="endpoint"/> and <paramref name="tokenCredential"/>.
    /// </summary>
    /// <inheritdoc cref="AddKeyedAzureAISearchCollection(IServiceCollection, object?, string, Uri, TokenCredential, AzureAISearchCollectionOptions?, ServiceLifetime)"/>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddAzureAISearchCollection<TRecord>(
        this IServiceCollection services,
        string name,
        Uri endpoint,
        TokenCredential tokenCredential,
        AzureAISearchCollectionOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
        => AddKeyedAzureAISearchCollection<TRecord>(services, serviceKey: null, name, endpoint, tokenCredential, options, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="AzureAISearchCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>
    /// using the provided <paramref name="endpoint"/> and <paramref name="tokenCredential"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="AzureAISearchCollection{TKey, TRecord}"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the collection.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="endpoint">The service endpoint for Azure AI Search.</param>
    /// <param name="tokenCredential">The credential to authenticate to Azure AI Search with.</param>
    /// <param name="options">Optional options to further configure the <see cref="AzureAISearchCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddKeyedAzureAISearchCollection<TRecord>(
        this IServiceCollection services,
        object? serviceKey,
        string name,
        Uri endpoint,
        TokenCredential tokenCredential,
        AzureAISearchCollectionOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
    {
        Verify.NotNull(endpoint);
        Verify.NotNull(tokenCredential);

        return AddKeyedAzureAISearchCollection<TRecord>(services, serviceKey, name, sp =>
        {
            var searchClientOptions = BuildSearchClientOptions(options?.JsonSerializerOptions);
            return new SearchIndexClient(endpoint, tokenCredential, searchClientOptions);
        }, _ => options!, lifetime);
    }

    /// <summary>
    /// Registers a <see cref="AzureAISearchCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>
    /// using the provided <paramref name="endpoint"/> and <paramref name="keyCredential"/>.
    /// </summary>
    /// <inheritdoc cref="AddKeyedAzureAISearchCollection(IServiceCollection, object?, string, Uri, AzureKeyCredential, AzureAISearchCollectionOptions?, ServiceLifetime)"/>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddAzureAISearchCollection<TRecord>(
        this IServiceCollection services,
        string name,
        Uri endpoint,
        AzureKeyCredential keyCredential,
        AzureAISearchCollectionOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
        => AddKeyedAzureAISearchCollection<TRecord>(services, serviceKey: null, name, endpoint, keyCredential, options, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="AzureAISearchCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>
    /// using the provided <paramref name="endpoint"/> and <paramref name="keyCredential"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="AzureAISearchCollection{TKey, TRecord}"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the collection.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="endpoint">The service endpoint for Azure AI Search.</param>
    /// <param name="keyCredential">The credential to authenticate to Azure AI Search with.</param>
    /// <param name="options">Optional options to further configure the <see cref="AzureAISearchCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddKeyedAzureAISearchCollection<TRecord>(
        this IServiceCollection services,
        object? serviceKey,
        string name,
        Uri endpoint,
        AzureKeyCredential keyCredential,
        AzureAISearchCollectionOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
    {
        Verify.NotNull(endpoint);
        Verify.NotNull(keyCredential);

        return AddKeyedAzureAISearchCollection<TRecord>(services, serviceKey, name, sp =>
        {
            var searchClientOptions = BuildSearchClientOptions(options?.JsonSerializerOptions);
            return new SearchIndexClient(endpoint, keyCredential, searchClientOptions);
        }, _ => options!, lifetime);
    }

    /// <summary>
    /// Build a <see cref="SearchClientOptions"/> instance, using the provided <see cref="JsonSerializerOptions"/> if it's not null and add the SK user agent string.
    /// </summary>
    /// <param name="jsonSerializerOptions">Optional <see cref="JsonSerializerOptions"/> to add to the options if provided.</param>
    /// <returns>The <see cref="SearchClientOptions"/>.</returns>
    private static SearchClientOptions BuildSearchClientOptions(JsonSerializerOptions? jsonSerializerOptions)
    {
        var searchClientOptions = new SearchClientOptions();
        searchClientOptions.Diagnostics.ApplicationId = HttpHeaderConstant.Values.UserAgent;
        if (jsonSerializerOptions != null)
        {
            searchClientOptions.Serializer = new JsonObjectSerializer(jsonSerializerOptions);
        }

        return searchClientOptions;
    }

    private static AzureAISearchVectorStoreOptions? GetStoreOptions(IServiceProvider sp, Func<IServiceProvider, AzureAISearchVectorStoreOptions?>? optionsProvider)
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

    private static AzureAISearchCollectionOptions? GetCollectionOptions(IServiceProvider sp, Func<IServiceProvider, AzureAISearchCollectionOptions?>? optionsProvider)
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
