// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Pinecone;
using Sdk = Pinecone;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register Pinecone <see cref="IVectorStore"/> instances on an <see cref="IServiceCollection"/>.
/// </summary>
public static class PineconeServiceCollectionExtensions
{
    /// <summary>
    /// Registers a Pinecone <see cref="IVectorStore"/>, retrieving <see cref="Sdk.PineconeClient"/> from the dependency injection container.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddPineconeVectorStore(
        this IServiceCollection serviceCollection,
        PineconeVectorStoreOptions? options = default,
        // If we are not constructing the PineconeClient, add the IVectorStore as transient, since we
        // cannot make assumptions about how PineconeClient is being managed.
        ServiceLifetime lifetime = ServiceLifetime.Transient)
        => AddKeyedPineconeVectorStore(serviceCollection, serviceKey: null, options, lifetime);

    /// <summary>
    /// Registers a keyed Pinecone <see cref="IVectorStore"/>, retrieving <see cref="Sdk.PineconeClient"/> from the dependency injection container.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddKeyedPineconeVectorStore(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        PineconeVectorStoreOptions? options = default,
        // If we are not constructing the PineconeClient, add the IVectorStore as transient, since we
        // cannot make assumptions about how PineconeClient is being managed.
        ServiceLifetime lifetime = ServiceLifetime.Transient)
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStore),
                serviceKey,
                (serviceProvider, _) => new PineconeVectorStore(
                    serviceProvider.GetRequiredService<Sdk.PineconeClient>(),
                    options ?? serviceProvider.GetService<PineconeVectorStoreOptions>()),
                lifetime));

        return serviceCollection;
    }

    /// <summary>
    /// Registers a Pinecone <see cref="IVectorStore"/> using the provided apikey.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="apiKey">The api key for Pinecone.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddPineconeVectorStore(
        this IServiceCollection serviceCollection,
        string apiKey,
        PineconeVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        => AddKeyedPineconeVectorStore(serviceCollection, serviceKey: null, apiKey, options, lifetime);

    /// <summary>
    /// Registers a keyed Pinecone <see cref="IVectorStore"/> using the provided apikey.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="apiKey">The api key for Pinecone.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddKeyedPineconeVectorStore(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        string apiKey,
        PineconeVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStore),
                serviceKey,
                (serviceProvider, _) => new PineconeVectorStore(
                    new Sdk.PineconeClient(apiKey),
                    options ?? serviceProvider.GetService<PineconeVectorStoreOptions>()),
                lifetime));

        return serviceCollection;
    }

    /// <summary>
    /// Registers a Pinecone <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/>,
    /// retrieving <see cref="Sdk.PineconeClient"/> from the dependency injection container.
    /// </summary>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="PineconeVectorStoreRecordCollection{TRecord}"/> will access.</param>
    /// <param name="options">Configuration options to pass to the <see cref="PineconeVectorStoreRecordCollection{TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddPineconeVectorStoreRecordCollection<TRecord>(
        this IServiceCollection serviceCollection,
        string collectionName,
        PineconeVectorStoreRecordCollectionOptions<TRecord>? options = default,
        // If we are not constructing the PineconeClient, add the IVectorStore as transient, since we
        // cannot make assumptions about how PineconeClient is being managed.
        ServiceLifetime lifetime = ServiceLifetime.Transient)
        => AddKeyedPineconeVectorStoreRecordCollection(serviceCollection, serviceKey: null, collectionName, options, lifetime);

    /// <summary>
    /// Registers a keyed Pinecone <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/>,
    /// retrieving <see cref="Sdk.PineconeClient"/> from the dependency injection container.
    /// </summary>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="PineconeVectorStoreRecordCollection{TRecord}"/> will access.</param>
    /// <param name="options">Configuration options to pass to the <see cref="PineconeVectorStoreRecordCollection{TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddKeyedPineconeVectorStoreRecordCollection<TRecord>(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        string collectionName,
        PineconeVectorStoreRecordCollectionOptions<TRecord>? options = default,
        // If we are not constructing the PineconeClient, add the IVectorStore as transient, since we
        // cannot make assumptions about how PineconeClient is being managed.
        ServiceLifetime lifetime = ServiceLifetime.Transient)
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStoreRecordCollection<string, TRecord>),
                serviceKey,
                (serviceProvider, _) => new PineconeVectorStoreRecordCollection<TRecord>(
                    serviceProvider.GetRequiredService<Sdk.PineconeClient>(),
                    collectionName,
                    options ?? serviceProvider.GetService<PineconeVectorStoreRecordCollectionOptions<TRecord>>()),
                lifetime));

        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorizedSearch<TRecord>),
                serviceKey,
                static (serviceProvider, serviceKey) => serviceProvider.GetRequiredKeyedService<IVectorStoreRecordCollection<string, TRecord>>(serviceKey),
                lifetime));

        return serviceCollection;
    }

    /// <summary>
    /// Registers a Pinecone <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/>,
    /// using the provided apikey.
    /// </summary>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="PineconeVectorStoreRecordCollection{TRecord}"/> will access.</param>
    /// <param name="apiKey">The api key for Pinecone.</param>
    /// <param name="options">Configuration options to pass to the <see cref="PineconeVectorStoreRecordCollection{TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddPineconeVectorStoreRecordCollection<TRecord>(
        this IServiceCollection serviceCollection,
        string collectionName,
        string apiKey,
        PineconeVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        => AddKeyedPineconeVectorStoreRecordCollection(serviceCollection, serviceKey: null, collectionName, apiKey, options, lifetime);

    /// <summary>
    /// Registers a keyed Pinecone <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/>,
    /// using the provided apikey.
    /// </summary>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="PineconeVectorStoreRecordCollection{TRecord}"/> will access.</param>
    /// <param name="apiKey">The api key for Pinecone.</param>
    /// <param name="options">Configuration options to pass to the <see cref="PineconeVectorStoreRecordCollection{TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddKeyedPineconeVectorStoreRecordCollection<TRecord>(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        string collectionName,
        string apiKey,
        PineconeVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStoreRecordCollection<string, TRecord>),
                serviceKey,
                (serviceProvider, _) => new PineconeVectorStoreRecordCollection<TRecord>(
                    new Sdk.PineconeClient(apiKey),
                    collectionName,
                    options ?? serviceProvider.GetService<PineconeVectorStoreRecordCollectionOptions<TRecord>>()),
                lifetime));

        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorizedSearch<TRecord>),
                serviceKey,
                static (serviceProvider, serviceKey) => serviceProvider.GetRequiredKeyedService<IVectorStoreRecordCollection<string, TRecord>>(serviceKey),
                lifetime));

        return serviceCollection;
    }
}
