// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Weaviate;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register Weaviate <see cref="IVectorStore"/> instances on an <see cref="IServiceCollection"/>
/// </summary>
public static class WeaviateServiceCollectionExtensions
{
    /// <summary>
    /// Registers a Weaviate <see cref="IVectorStore"/>.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="httpClient">
    /// <see cref="HttpClient"/> that is used to interact with Weaviate API.
    /// <see cref="HttpClient.BaseAddress"/> should point to remote or local cluster and API key can be configured via <see cref="HttpClient.DefaultRequestHeaders"/>.
    /// It's also possible to provide these parameters via <see cref="WeaviateVectorStoreOptions"/>.
    /// </param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddWeaviateVectorStore(
        this IServiceCollection serviceCollection,
        HttpClient? httpClient = default,
        WeaviateVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Transient)
        => AddKeyedWeaviateVectorStore(serviceCollection, serviceKey: null, httpClient, options, lifetime);

    /// <summary>
    /// Registers a keyed Weaviate <see cref="IVectorStore"/>.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="httpClient">
    /// <see cref="HttpClient"/> that is used to interact with Weaviate API.
    /// <see cref="HttpClient.BaseAddress"/> should point to remote or local cluster and API key can be configured via <see cref="HttpClient.DefaultRequestHeaders"/>.
    /// It's also possible to provide these parameters via <see cref="WeaviateVectorStoreOptions"/>.
    /// </param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddKeyedWeaviateVectorStore(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        HttpClient? httpClient = default,
        WeaviateVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Transient)
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStore),
                serviceKey,
                (serviceProvider, _) => new WeaviateVectorStore(
                    HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                    options ?? serviceProvider.GetService<WeaviateVectorStoreOptions>()),
                lifetime));

        return serviceCollection;
    }

    /// <summary>
    /// Registers a Weaviate <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="httpClient">
    /// <see cref="HttpClient"/> that is used to interact with Weaviate API.
    /// <see cref="HttpClient.BaseAddress"/> should point to remote or local cluster and API key can be configured via <see cref="HttpClient.DefaultRequestHeaders"/>.
    /// It's also possible to provide these parameters via <see cref="WeaviateVectorStoreOptions"/>.
    /// </param>
    /// <param name="options">Options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddWeaviateVectorStoreRecordCollection<TRecord>(
        this IServiceCollection serviceCollection,
        string collectionName,
        HttpClient? httpClient = default,
        WeaviateVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Transient)
        => AddKeyedWeaviateVectorStoreRecordCollection(serviceCollection, serviceKey: null, collectionName, httpClient, options, lifetime);

    /// <summary>
    /// Registers a keyed Weaviate <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="httpClient">
    /// <see cref="HttpClient"/> that is used to interact with Weaviate API.
    /// <see cref="HttpClient.BaseAddress"/> should point to remote or local cluster and API key can be configured via <see cref="HttpClient.DefaultRequestHeaders"/>.
    /// It's also possible to provide these parameters via <see cref="WeaviateVectorStoreOptions"/>.
    /// </param>
    /// <param name="options">Options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddKeyedWeaviateVectorStoreRecordCollection<TRecord>(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        string collectionName,
        HttpClient? httpClient = default,
        WeaviateVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Transient)
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStoreRecordCollection<Guid, TRecord>),
                serviceKey,
                (serviceProvider, _) => new WeaviateVectorStoreRecordCollection<TRecord>(
                    HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                    collectionName,
                    options ?? serviceProvider.GetService<WeaviateVectorStoreRecordCollectionOptions<TRecord>>()),
                lifetime));

        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorizedSearch<TRecord>),
                serviceKey,
                static (serviceProvider, serviceKey) => serviceProvider.GetRequiredKeyedService<IVectorStoreRecordCollection<Guid, TRecord>>(serviceKey),
                lifetime));

        return serviceCollection;
    }
}
