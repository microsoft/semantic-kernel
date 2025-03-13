// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;
using MongoDB.Driver;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register Azure CosmosDB MongoDB <see cref="IVectorStore"/> instances on the <see cref="IKernelBuilder"/>.
/// </summary>
[Obsolete("Call the corresponding method on the Services property of your IKernelBuilder instance.")]
public static class AzureCosmosDBMongoDBKernelBuilderExtensions
{
    /// <summary>
    /// Register a Azure CosmosDB MongoDB <see cref="IVectorStore"/> with the specified service ID
    /// and where the Azure CosmosDB MongoDB <see cref="IMongoDatabase"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <param name="builder">The builder to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddAzureCosmosDBMongoDBVectorStore(
        this IKernelBuilder builder,
        AzureCosmosDBMongoDBVectorStoreOptions? options = default,
        string? serviceId = default)
    {
        builder.Services.AddKeyedAzureCosmosDBMongoDBVectorStore(serviceId, options);
        return builder;
    }

    /// <summary>
    /// Register a Azure CosmosDB MongoDB <see cref="IVectorStore"/> with the specified service ID
    /// and where the Azure CosmosDB MongoDB <see cref="IMongoDatabase"/> is constructed using the provided <paramref name="connectionString"/> and <paramref name="databaseName"/>.
    /// </summary>
    /// <param name="builder">The builder to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="connectionString">Connection string required to connect to Azure CosmosDB MongoDB.</param>
    /// <param name="databaseName">Database name for Azure CosmosDB MongoDB.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddAzureCosmosDBMongoDBVectorStore(
        this IKernelBuilder builder,
        string connectionString,
        string databaseName,
        AzureCosmosDBMongoDBVectorStoreOptions? options = default,
        string? serviceId = default)
    {
        builder.Services.AddKeyedAzureCosmosDBMongoDBVectorStore(serviceId, connectionString, databaseName, options);
        return builder;
    }

    /// <summary>
    /// Register an Azure CosmosDB MongoDB <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/> with the specified service ID
    /// and where the Azure CosmosDB MongoDB <see cref="IMongoDatabase"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="builder">The builder to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddAzureCosmosDBMongoDBVectorStoreRecordCollection<TRecord>(
        this IKernelBuilder builder,
        string collectionName,
        AzureCosmosDBMongoDBVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
    {
        builder.Services.AddKeyedAzureCosmosDBMongoDBVectorStoreRecordCollection<TRecord>(serviceId, collectionName, options);
        return builder;
    }

    /// <summary>
    /// Register an Azure CosmosDB MongoDB <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/> with the specified service ID
    /// and where the Azure CosmosDB MongoDB <see cref="IMongoDatabase"/> is constructed using the provided <paramref name="connectionString"/> and <paramref name="databaseName"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="builder">The builder to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="connectionString">Connection string required to connect to Azure CosmosDB MongoDB.</param>
    /// <param name="databaseName">Database name for Azure CosmosDB MongoDB.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddAzureCosmosDBMongoDBVectorStoreRecordCollection<TRecord>(
        this IKernelBuilder builder,
        string collectionName,
        string connectionString,
        string databaseName,
        AzureCosmosDBMongoDBVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
    {
        builder.Services.AddKeyedAzureCosmosDBMongoDBVectorStoreRecordCollection<TRecord>(serviceId, collectionName, connectionString, databaseName, options);
        return builder;
    }
}
