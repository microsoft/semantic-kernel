// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.AI;
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
                options ??= sp.GetService<AzureCosmosDBNoSQLVectorStoreOptions>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

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
                    ApplicationName = HttpHeaderConstant.Values.UserAgent,
                    UseSystemTextJsonSerializerWithOptions = options?.JsonSerializerOptions ?? JsonSerializerOptions.Default,
                });

                var database = cosmosClient.GetDatabase(databaseName);
                options ??= sp.GetService<AzureCosmosDBNoSQLVectorStoreOptions>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return new AzureCosmosDBNoSQLVectorStore(database, options);
            });

        return services;
    }

    /// <summary>
    /// Register an Azure CosmosDB NoSQL <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorSearch{TRecord}"/> with the specified service ID
    /// and where the Azure CosmosDB NoSQL <see cref="Database"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddAzureCosmosDBNoSQLVectorStoreRecordCollection<TRecord>(
        this IServiceCollection services,
        string collectionName,
        AzureCosmosDBNoSQLVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TRecord : notnull
    {
        services.AddKeyedTransient<IVectorStoreRecordCollection<string, TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                var database = sp.GetRequiredService<Database>();
                options ??= sp.GetService<AzureCosmosDBNoSQLVectorStoreRecordCollectionOptions<TRecord>>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return new AzureCosmosDBNoSQLVectorStoreRecordCollection<string, TRecord>(database, collectionName, options);
            });

        AddVectorizedSearch<TRecord>(services, serviceId);

        return services;
    }

    /// <summary>
    /// Register an Azure CosmosDB NoSQL <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorSearch{TRecord}"/> with the specified service ID
    /// and where the Azure CosmosDB NoSQL <see cref="Database"/> is constructed using the provided <paramref name="connectionString"/> and <paramref name="databaseName"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="connectionString">Connection string required to connect to Azure CosmosDB NoSQL.</param>
    /// <param name="databaseName">Database name for Azure CosmosDB NoSQL.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddAzureCosmosDBNoSQLVectorStoreRecordCollection<TRecord>(
        this IServiceCollection services,
        string collectionName,
        string connectionString,
        string databaseName,
        AzureCosmosDBNoSQLVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TRecord : notnull
    {
        services.AddKeyedSingleton<IVectorStoreRecordCollection<string, TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                var cosmosClient = new CosmosClient(connectionString, new()
                {
                    ApplicationName = HttpHeaderConstant.Values.UserAgent,
                    UseSystemTextJsonSerializerWithOptions = options?.JsonSerializerOptions ?? JsonSerializerOptions.Default,
                });

                var database = cosmosClient.GetDatabase(databaseName);
                options ??= sp.GetService<AzureCosmosDBNoSQLVectorStoreRecordCollectionOptions<TRecord>>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return new AzureCosmosDBNoSQLVectorStoreRecordCollection<string, TRecord>(database, collectionName, options);
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
