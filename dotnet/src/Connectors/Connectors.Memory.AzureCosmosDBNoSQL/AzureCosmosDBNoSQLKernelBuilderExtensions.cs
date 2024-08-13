// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Azure.Cosmos;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register Azure CosmosDB NoSQL <see cref="IVectorStore"/> instances on the <see cref="IKernelBuilder"/>.
/// </summary>
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
}
