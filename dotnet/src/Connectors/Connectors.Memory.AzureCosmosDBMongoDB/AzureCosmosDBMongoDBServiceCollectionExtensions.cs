// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;
using Microsoft.SemanticKernel.Http;
using MongoDB.Driver;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register Azure CosmosDB MongoDB <see cref="IVectorStore"/> instances on an <see cref="IServiceCollection"/>.
/// </summary>
public static class AzureCosmosDBMongoDBServiceCollectionExtensions
{
    /// <summary>
    /// Register a Azure CosmosDB MongoDB <see cref="IVectorStore"/> with the specified service ID
    /// and where the Azure CosmosDB MongoDB <see cref="IMongoDatabase"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddAzureCosmosDBMongoDBVectorStore(
        this IServiceCollection services,
        AzureCosmosDBMongoDBVectorStoreOptions? options = default,
        string? serviceId = default)
    {
        // If we are not constructing MongoDatabase, add the IVectorStore as transient, since we
        // cannot make assumptions about how MongoDatabase is being managed.
        services.AddKeyedTransient<IVectorStore>(
            serviceId,
            (sp, obj) =>
            {
                var database = sp.GetRequiredService<IMongoDatabase>();
                options ??= sp.GetService<AzureCosmosDBMongoDBVectorStoreOptions>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return new AzureCosmosDBMongoDBVectorStore(database, options);
            });

        return services;
    }

    /// <summary>
    /// Register a Azure CosmosDB MongoDB <see cref="IVectorStore"/> with the specified service ID
    /// and where the Azure CosmosDB MongoDB <see cref="IMongoDatabase"/> is constructed using the provided <paramref name="connectionString"/> and <paramref name="databaseName"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="connectionString">Connection string required to connect to Azure CosmosDB MongoDB.</param>
    /// <param name="databaseName">Database name for Azure CosmosDB MongoDB.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddAzureCosmosDBMongoDBVectorStore(
        this IServiceCollection services,
        string connectionString,
        string databaseName,
        AzureCosmosDBMongoDBVectorStoreOptions? options = default,
        string? serviceId = default)
    {
        // If we are constructing IMongoDatabase, add the IVectorStore as singleton, since we are managing the lifetime of it,
        // and the recommendation from Mongo is to register it with a singleton lifetime.
        services.AddKeyedSingleton<IVectorStore>(
            serviceId,
            (sp, obj) =>
            {
                var settings = MongoClientSettings.FromConnectionString(connectionString);
                settings.ApplicationName = HttpHeaderConstant.Values.UserAgent;

                var mongoClient = new MongoClient(settings);
                var database = mongoClient.GetDatabase(databaseName);

                options ??= sp.GetService<AzureCosmosDBMongoDBVectorStoreOptions>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return new AzureCosmosDBMongoDBVectorStore(database, options);
            });

        return services;
    }

    /// <summary>
    /// Register an Azure CosmosDB MongoDB <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorSearch{TRecord}"/> with the specified service ID
    /// and where the Azure CosmosDB MongoDB <see cref="IMongoDatabase"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddAzureCosmosDBMongoDBVectorStoreRecordCollection<TRecord>(
        this IServiceCollection services,
        string collectionName,
        AzureCosmosDBMongoDBVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TRecord : notnull
    {
        services.AddKeyedTransient<IVectorStoreRecordCollection<string, TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                var database = sp.GetRequiredService<IMongoDatabase>();
                options ??= sp.GetService<AzureCosmosDBMongoDBVectorStoreRecordCollectionOptions<TRecord>>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return new AzureCosmosDBMongoDBVectorStoreRecordCollection<string, TRecord>(database, collectionName, options);
            });

        AddVectorizedSearch<TRecord>(services, serviceId);

        return services;
    }

    /// <summary>
    /// Register an Azure CosmosDB MongoDB <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorSearch{TRecord}"/> with the specified service ID
    /// and where the Azure CosmosDB MongoDB <see cref="IMongoDatabase"/> is constructed using the provided <paramref name="connectionString"/> and <paramref name="databaseName"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="connectionString">Connection string required to connect to Azure CosmosDB MongoDB.</param>
    /// <param name="databaseName">Database name for Azure CosmosDB MongoDB.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddAzureCosmosDBMongoDBVectorStoreRecordCollection<TRecord>(
        this IServiceCollection services,
        string collectionName,
        string connectionString,
        string databaseName,
        AzureCosmosDBMongoDBVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TRecord : notnull
    {
        services.AddKeyedSingleton<IVectorStoreRecordCollection<string, TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                var settings = MongoClientSettings.FromConnectionString(connectionString);
                settings.ApplicationName = HttpHeaderConstant.Values.UserAgent;

                var mongoClient = new MongoClient(settings);
                var database = mongoClient.GetDatabase(databaseName);

                options ??= sp.GetService<AzureCosmosDBMongoDBVectorStoreRecordCollectionOptions<TRecord>>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return new AzureCosmosDBMongoDBVectorStoreRecordCollection<string, TRecord>(database, collectionName, options);
            });

        AddVectorizedSearch<TRecord>(services, serviceId);

        return services;
    }

    /// <summary>
    /// Also register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> with the given <paramref name="serviceId"/> as a <see cref="IVectorSearch{TRecord}"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="services">The service collection to register on.</param>
    /// <param name="serviceId">The service id that the registrations should use.</param>
    private static void AddVectorizedSearch<TRecord>(IServiceCollection services, string? serviceId) where TRecord : notnull
    {
        services.AddKeyedTransient<IVectorSearch<TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                return sp.GetRequiredKeyedService<IVectorStoreRecordCollection<string, TRecord>>(serviceId);
            });
    }
}
