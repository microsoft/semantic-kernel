// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register Azure CosmosDB NoSQL <see cref="IVectorStore"/> instances on the <see cref="IKernelBuilder"/>.
/// </summary>
[Obsolete("The IKernelBuilder extensions are being obsoleted, call the appropriate function on the Services property of your IKernelBuilder")]
public static class AzureCosmosDBNoSQLKernelBuilderExtensions
{
    /// <summary>
    /// Register an Azure CosmosDB NoSQL <see cref="IVectorStore"/> with the specified service ID
    /// and where the Azure CosmosDB NoSQL <see cref="Database"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <param name="builder">The builder to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddAzureCosmosDBNoSQLVectorStore(
        this IKernelBuilder builder,
        AzureCosmosDBNoSQLVectorStoreOptions? options = default,
        string? serviceId = default)
    {
        builder.Services.AddAzureCosmosDBNoSQLVectorStore(options, serviceId);
        return builder;
    }

    /// <summary>
    /// Register an Azure CosmosDB NoSQL <see cref="IVectorStore"/> with the specified service ID
    /// and where the Azure CosmosDB NoSQL <see cref="Database"/> is constructed using the provided <paramref name="connectionString"/> and <paramref name="databaseName"/>.
    /// </summary>
    /// <param name="builder">The builder to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="connectionString">Connection string required to connect to Azure CosmosDB NoSQL.</param>
    /// <param name="databaseName">Database name for Azure CosmosDB NoSQL.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddAzureCosmosDBNoSQLVectorStore(
        this IKernelBuilder builder,
        string connectionString,
        string databaseName,
        AzureCosmosDBNoSQLVectorStoreOptions? options = default,
        string? serviceId = default)
    {
        builder.Services.AddAzureCosmosDBNoSQLVectorStore(
            connectionString,
            databaseName,
            options,
            serviceId);

        return builder;
    }

    /// <summary>
    /// Register an Azure CosmosDB NoSQL <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorSearch{TRecord}"/> with the specified service ID
    /// and where the Azure CosmosDB NoSQL <see cref="Database"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="builder">The builder to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddAzureCosmosDBNoSQLVectorStoreRecordCollection<TRecord>(
        this IKernelBuilder builder,
        string collectionName,
        AzureCosmosDBNoSQLVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TRecord : notnull
    {
        builder.Services.AddAzureCosmosDBNoSQLVectorStoreRecordCollection<TRecord>(collectionName, options, serviceId);
        return builder;
    }

    /// <summary>
    /// Register an Azure CosmosDB NoSQL <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorSearch{TRecord}"/> with the specified service ID
    /// and where the Azure CosmosDB NoSQL <see cref="Database"/> is constructed using the provided <paramref name="connectionString"/> and <paramref name="databaseName"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="builder">The builder to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="connectionString">Connection string required to connect to Azure CosmosDB NoSQL.</param>
    /// <param name="databaseName">Database name for Azure CosmosDB NoSQL.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddAzureCosmosDBNoSQLVectorStoreRecordCollection<TRecord>(
        this IKernelBuilder builder,
        string collectionName,
        string connectionString,
        string databaseName,
        AzureCosmosDBNoSQLVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TRecord : notnull
    {
        builder.Services.AddAzureCosmosDBNoSQLVectorStoreRecordCollection<TRecord>(collectionName, connectionString, databaseName, options, serviceId);
        return builder;
    }
}
