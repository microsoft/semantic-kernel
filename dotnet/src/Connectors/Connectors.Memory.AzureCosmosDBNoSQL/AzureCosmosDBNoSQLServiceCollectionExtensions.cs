// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register Azure CosmosDB NoSQL <see cref="IVectorStore"/> instances on an <see cref="IServiceCollection"/>.
/// </summary>
public static class AzureCosmosDBNoSQLServiceCollectionExtensions
{
    /// <summary>
    /// Register an Azure CosmosDB NoSQL <see cref="IVectorStore"/> with the specified service ID
    /// and where the Azure CosmosDB NoSQL <see cref="Database"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddAzureCosmosDBNoSQLVectorStore(
        this IServiceCollection services,
        AzureCosmosDBNoSQLVectorStoreOptions? options = default,
        string? serviceId = default)
    {
        // If we are not constructing Database, add the IVectorStore as transient, since we
        // cannot make assumptions about how Database is being managed.
        services.AddKeyedTransient<IVectorStore>(
            serviceId,
            (sp, obj) =>
            {
                var database = sp.GetRequiredService<Database>();
                var selectedOptions = options ?? sp.GetService<AzureCosmosDBNoSQLVectorStoreOptions>();
                return new AzureCosmosDBNoSQLVectorStore(database, options);
            });

        return services;
    }

    /// <summary>
    /// Register an Azure CosmosDB NoSQL <see cref="IVectorStore"/> with the specified service ID
    /// and where the Azure CosmosDB NoSQL <see cref="Database"/> is constructed using the provided <paramref name="connectionString"/> and <paramref name="databaseName"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="connectionString">Connection string required to connect to Azure CosmosDB NoSQL.</param>
    /// <param name="databaseName">Database name for Azure CosmosDB NoSQL.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddAzureCosmosDBNoSQLVectorStore(
        this IServiceCollection services,
        string connectionString,
        string databaseName,
        AzureCosmosDBNoSQLVectorStoreOptions? options = default,
        string? serviceId = default)
    {
        // If we are constructing Database, add the IVectorStore as singleton.
        services.AddKeyedSingleton<IVectorStore>(
            serviceId,
            (sp, obj) =>
            {
                var cosmosClient = new CosmosClient(connectionString, new()
                {
                    Serializer = new CosmosSystemTextJsonSerializer(options?.JsonSerializerOptions ?? JsonSerializerOptions.Default)
                });

                var database = cosmosClient.GetDatabase(databaseName);
                var selectedOptions = options ?? sp.GetService<AzureCosmosDBNoSQLVectorStoreOptions>();
                return new AzureCosmosDBNoSQLVectorStore(database, options);
            });

        return services;
    }
}
