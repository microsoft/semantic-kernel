// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.MongoDB;
using Microsoft.SemanticKernel.Http;
using MongoDB.Driver;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register MongoDB <see cref="IVectorStore"/> instances on an <see cref="IServiceCollection"/>.
/// </summary>
public static class MongoDBServiceCollectionExtensions
{
    /// <summary>
    /// Registers a MongoDB <see cref="IVectorStore"/>, retrieving the <see cref="IMongoDatabase"/> from the dependency injection container.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddMongoDBVectorStore(
        this IServiceCollection serviceCollection,
        MongoDBVectorStoreOptions? options = default,
        // If we are not constructing MongoDatabase, add the IVectorStore as transient, since we
        // cannot make assumptions about how MongoDatabase is being managed.
        ServiceLifetime lifetime = ServiceLifetime.Transient)
        => AddKeyedMongoDBVectorStore(serviceCollection, serviceKey: null, options, lifetime);

    /// <summary>
    /// Registers a keyed MongoDB <see cref="IVectorStore"/>, retrieving the <see cref="IMongoDatabase"/> from the dependency injection container.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddKeyedMongoDBVectorStore(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        MongoDBVectorStoreOptions? options = default,
        // If we are not constructing MongoDatabase, add the IVectorStore as transient, since we
        // cannot make assumptions about how MongoDatabase is being managed.
        ServiceLifetime lifetime = ServiceLifetime.Transient)
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStore),
                serviceKey,
                (serviceProvider, _) => new MongoDBVectorStore(
                    serviceProvider.GetRequiredService<IMongoDatabase>(),
                    options ?? serviceProvider.GetService<MongoDBVectorStoreOptions>()),
                lifetime));

        return serviceCollection;
    }

    /// <summary>
    /// Registers a MongoDB <see cref="IVectorStore"/>, using the provided <paramref name="connectionString"/> and <paramref name="databaseName"/>.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="connectionString">Connection string required to connect to MongoDB.</param>
    /// <param name="databaseName">Database name for MongoDB.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddMongoDBVectorStore(
        this IServiceCollection serviceCollection,
        string connectionString,
        string databaseName,
        MongoDBVectorStoreOptions? options = default,
        // If we are constructing IMongoDatabase, add the IVectorStore as singleton, since we are managing the lifetime of it,
        // and the recommendation from Mongo is to register it with a singleton lifetime.
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    => AddKeyedMongoDBVectorStore(serviceCollection, serviceKey: null, connectionString, databaseName, options, lifetime);

    /// <summary>
    /// Registers a keyed MongoDB <see cref="IVectorStore"/>, using the provided <paramref name="connectionString"/> and <paramref name="databaseName"/>.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="connectionString">Connection string required to connect to MongoDB.</param>
    /// <param name="databaseName">Database name for MongoDB.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddKeyedMongoDBVectorStore(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        string connectionString,
        string databaseName,
        MongoDBVectorStoreOptions? options = default,
        // If we are constructing IMongoDatabase, add the IVectorStore as singleton, since we are managing the lifetime of it,
        // and the recommendation from Mongo is to register it with a singleton lifetime.
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStore),
                serviceKey,
                (serviceProvider, _) =>
                {
                    var settings = MongoClientSettings.FromConnectionString(connectionString);
                    settings.ApplicationName = HttpHeaderConstant.Values.UserAgent;

                    var mongoClient = new MongoClient(settings);
                    var database = mongoClient.GetDatabase(databaseName);

                    return new MongoDBVectorStore(database, options ?? serviceProvider.GetService<MongoDBVectorStoreOptions>());
                },
                lifetime));

        return serviceCollection;
    }

    /// <summary>
    /// Registers a MongoDB <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/>,
    /// retrieving the <see cref="IMongoDatabase"/> from the dependency injection container.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddMongoDBVectorStoreRecordCollection<TRecord>(
        this IServiceCollection serviceCollection,
        string collectionName,
        MongoDBVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Transient)
        => AddKeyedMongoDBVectorStoreRecordCollection(serviceCollection, serviceKey: null, collectionName, options, lifetime);

    /// <summary>
    /// Registers a keyed MongoDB <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/>,
    /// retrieving the <see cref="IMongoDatabase"/> from the dependency injection container.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddKeyedMongoDBVectorStoreRecordCollection<TRecord>(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        string collectionName,
        MongoDBVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Transient)
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStoreRecordCollection<string, TRecord>),
                serviceKey,
                (serviceProvider, _) => new MongoDBVectorStoreRecordCollection<TRecord>(
                    serviceProvider.GetRequiredService<IMongoDatabase>(),
                    collectionName,
                    options ?? serviceProvider.GetService<MongoDBVectorStoreRecordCollectionOptions<TRecord>>()),
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
    /// Registers a MongoDB <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/>,
    /// using the provided <paramref name="connectionString"/> and <paramref name="databaseName"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="connectionString">Connection string required to connect to MongoDB.</param>
    /// <param name="databaseName">Database name for MongoDB.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddMongoDBVectorStoreRecordCollection<TRecord>(
        this IServiceCollection serviceCollection,
        string collectionName,
        string connectionString,
        string databaseName,
        MongoDBVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    => AddKeyedMongoDBVectorStoreRecordCollection(serviceCollection, serviceKey: null, collectionName, connectionString, databaseName, options, lifetime);

    /// <summary>
    /// Registers a keyed MongoDB <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/>,
    /// using the provided <paramref name="connectionString"/> and <paramref name="databaseName"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="connectionString">Connection string required to connect to MongoDB.</param>
    /// <param name="databaseName">Database name for MongoDB.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddKeyedMongoDBVectorStoreRecordCollection<TRecord>(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        string collectionName,
        string connectionString,
        string databaseName,
        MongoDBVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStoreRecordCollection<string, TRecord>),
                serviceKey,
                (serviceProvider, _) =>
                {
                    var settings = MongoClientSettings.FromConnectionString(connectionString);
                    settings.ApplicationName = HttpHeaderConstant.Values.UserAgent;

                    var mongoClient = new MongoClient(settings);
                    var database = mongoClient.GetDatabase(databaseName);

                    var selectedOptions = options ?? serviceProvider.GetService<MongoDBVectorStoreRecordCollectionOptions<TRecord>>();

                    return new MongoDBVectorStoreRecordCollection<TRecord>(database, collectionName, selectedOptions);
                },
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
