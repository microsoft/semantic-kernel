// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;
using Microsoft.SemanticKernel.Data;
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
                var selectedOptions = options ?? sp.GetService<AzureCosmosDBMongoDBVectorStoreOptions>();

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
                var mongoClient = new MongoClient(settings);
                var database = mongoClient.GetDatabase(databaseName);

                var selectedOptions = options ?? sp.GetService<AzureCosmosDBMongoDBVectorStoreOptions>();

                return new AzureCosmosDBMongoDBVectorStore(database, options);
            });

        return services;
    }
}
