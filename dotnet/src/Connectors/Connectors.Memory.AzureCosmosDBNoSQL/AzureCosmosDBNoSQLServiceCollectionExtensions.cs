// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register Azure CosmosDB NoSQL <see cref="IVectorStore"/> instances on an <see cref="IServiceCollection"/>.
/// </summary>
public static class AzureCosmosDBNoSQLServiceCollectionExtensions
{
    /// <summary>
    /// Registers an Azure CosmosDB NoSQL <see cref="IVectorStore"/>, retrieving the <see cref="Database"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddAzureCosmosDBNoSQLVectorStore(
        this IServiceCollection serviceCollection,
        AzureCosmosDBNoSQLVectorStoreOptions? options = default,
        // If we are not constructing Database, add the IVectorStore as transient, since we
        // cannot make assumptions about how Database is being managed.
        ServiceLifetime lifetime = ServiceLifetime.Transient)
        => AddKeyedAzureCosmosDBNoSQLVectorStore(serviceCollection, serviceKey: null, options, lifetime);

    /// <summary>
    /// Registers a keyed Azure CosmosDB NoSQL <see cref="IVectorStore"/>, retrieving the <see cref="Database"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddKeyedAzureCosmosDBNoSQLVectorStore(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        AzureCosmosDBNoSQLVectorStoreOptions? options = default,
        // If we are not constructing Database, add the IVectorStore as transient, since we
        // cannot make assumptions about how Database is being managed.
        ServiceLifetime lifetime = ServiceLifetime.Transient)
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStore),
                serviceKey,
                (serviceProvider, _) => new AzureCosmosDBNoSQLVectorStore(
                    serviceProvider.GetRequiredService<Database>(),
                    options ?? serviceProvider.GetService<AzureCosmosDBNoSQLVectorStoreOptions>()),
                lifetime));

        return serviceCollection;
    }

    /// <summary>
    /// Registers an Azure CosmosDB NoSQL <see cref="IVectorStore"/>, using the provided <paramref name="connectionString"/> and <paramref name="databaseName"/>.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="connectionString">Connection string required to connect to Azure CosmosDB NoSQL.</param>
    /// <param name="databaseName">Database name for Azure CosmosDB NoSQL.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddAzureCosmosDBNoSQLVectorStore(
        this IServiceCollection serviceCollection,
        string connectionString,
        string databaseName,
        AzureCosmosDBNoSQLVectorStoreOptions? options = default,
        // If we are constructing Database, add the IVectorStore as singleton.
        ServiceLifetime lifetime = ServiceLifetime.Transient)
    => AddKeyedAzureCosmosDBNoSQLVectorStore(serviceCollection, serviceKey: null, connectionString, databaseName, options, lifetime);

    /// <summary>
    /// Registers a keyed Azure CosmosDB NoSQL <see cref="IVectorStore"/>, using the provided <paramref name="connectionString"/> and <paramref name="databaseName"/>.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="connectionString">Connection string required to connect to Azure CosmosDB NoSQL.</param>
    /// <param name="databaseName">Database name for Azure CosmosDB NoSQL.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddKeyedAzureCosmosDBNoSQLVectorStore(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        string connectionString,
        string databaseName,
        AzureCosmosDBNoSQLVectorStoreOptions? options = default,
        // If we are constructing Database, add the IVectorStore as singleton.
        ServiceLifetime lifetime = ServiceLifetime.Transient)
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStore),
                serviceKey,
                (serviceProvider, _) =>
                {
                    var cosmosClient = new CosmosClient(connectionString, new()
                    {
                        ApplicationName = HttpHeaderConstant.Values.UserAgent,
                        UseSystemTextJsonSerializerWithOptions = options?.JsonSerializerOptions ?? JsonSerializerOptions.Default,
                    });

                    var database = cosmosClient.GetDatabase(databaseName);
                    options ??= serviceProvider.GetService<AzureCosmosDBNoSQLVectorStoreOptions>();

                    return new AzureCosmosDBNoSQLVectorStore(database, options);
                },
                lifetime));

        return serviceCollection;
    }

    /// <summary>
    /// Registers an Azure CosmosDB NoSQL <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/>,
    /// retrieving the <see cref="Database"/> from the dependency injection container.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddAzureCosmosDBNoSQLVectorStoreRecordCollection<TRecord>(
        this IServiceCollection serviceCollection,
        string collectionName,
        AzureCosmosDBNoSQLVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Transient)
        => AddKeyedAzureCosmosDBNoSQLVectorStoreRecordCollection(serviceCollection, serviceKey: null, collectionName, options, lifetime);

    /// <summary>
    /// Registers a keyed Azure CosmosDB NoSQL <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/>,
    /// retrieving the <see cref="Database"/> from the dependency injection container.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddKeyedAzureCosmosDBNoSQLVectorStoreRecordCollection<TRecord>(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        string collectionName,
        AzureCosmosDBNoSQLVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Transient)
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStoreRecordCollection<string, TRecord>),
                serviceKey,
                (serviceProvider, _) => new AzureCosmosDBNoSQLVectorStoreRecordCollection<TRecord>(
                    serviceProvider.GetRequiredService<Database>(),
                    collectionName,
                    options ?? serviceProvider.GetService<AzureCosmosDBNoSQLVectorStoreRecordCollectionOptions<TRecord>>()),
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
    /// Register an Azure CosmosDB NoSQL <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/>,
    /// using the provided <paramref name="connectionString"/> and <paramref name="databaseName"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="connectionString">Connection string required to connect to Azure CosmosDB NoSQL.</param>
    /// <param name="databaseName">Database name for Azure CosmosDB NoSQL.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddAzureCosmosDBNoSQLVectorStoreRecordCollection<TRecord>(
        this IServiceCollection serviceCollection,
        string collectionName,
        string connectionString,
        string databaseName,
        AzureCosmosDBNoSQLVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        => AddKeyedAzureCosmosDBNoSQLVectorStoreRecordCollection(serviceCollection, serviceKey: null, collectionName, connectionString, databaseName, options, lifetime);

    /// <summary>
    /// Register a keyed Azure CosmosDB NoSQL <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/>,
    /// using the provided <paramref name="connectionString"/> and <paramref name="databaseName"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="connectionString">Connection string required to connect to Azure CosmosDB NoSQL.</param>
    /// <param name="databaseName">Database name for Azure CosmosDB NoSQL.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddKeyedAzureCosmosDBNoSQLVectorStoreRecordCollection<TRecord>(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        string collectionName,
        string connectionString,
        string databaseName,
        AzureCosmosDBNoSQLVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStoreRecordCollection<string, TRecord>),
                serviceKey,
                (serviceProvider, _) =>
                {
                    var cosmosClient = new CosmosClient(connectionString, new()
                    {
                        ApplicationName = HttpHeaderConstant.Values.UserAgent,
                        UseSystemTextJsonSerializerWithOptions = options?.JsonSerializerOptions ?? JsonSerializerOptions.Default,
                    });

                    var database = cosmosClient.GetDatabase(databaseName);
                    options ??= serviceProvider.GetService<AzureCosmosDBNoSQLVectorStoreRecordCollectionOptions<TRecord>>();

                    return new AzureCosmosDBNoSQLVectorStoreRecordCollection<TRecord>(database, collectionName, options);
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
