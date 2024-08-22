// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;
using Microsoft.SemanticKernel.Data;
using MongoDB.Driver;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register Azure CosmosDB MongoDB <see cref="IVectorStore"/> instances on the <see cref="IKernelBuilder"/>.
/// </summary>
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
        builder.Services.AddAzureCosmosDBMongoDBVectorStore(options, serviceId);
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
        builder.Services.AddAzureCosmosDBMongoDBVectorStore(connectionString, databaseName, options, serviceId);
        return builder;
    }
}
