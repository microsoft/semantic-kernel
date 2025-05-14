// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.CosmosNoSql;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register Azure CosmosDB NoSQL <see cref="VectorStore"/> instances on an <see cref="IServiceCollection"/>.
/// </summary>
public static class CosmosNoSqlServiceCollectionExtensions
{
    /// <summary>
    /// Register an Azure CosmosDB NoSQL <see cref="VectorStore"/> with the specified service ID
    /// and where the Azure CosmosDB NoSQL <see cref="Database"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStore"/> on.</param>
    /// <param name="options">Optional options to further configure the <see cref="VectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode("The Cosmos NoSQL provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The Cosmos NoSQL provider is currently incompatible with NativeAOT.")]
    public static IServiceCollection AddCosmosNoSqlVectorStore(
        this IServiceCollection services,
        CosmosNoSqlVectorStoreOptions? options = default,
        string? serviceId = default)
    {
        // If we are not constructing Database, add the IVectorStore as transient, since we
        // cannot make assumptions about how Database is being managed.
        services.AddKeyedTransient<VectorStore>(
            serviceId,
            (sp, obj) =>
            {
                var database = sp.GetRequiredService<Database>();
                options ??= sp.GetService<CosmosNoSqlVectorStoreOptions>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return new CosmosNoSqlVectorStore(database, options);
            });

        return services;
    }

    /// <summary>
    /// Register an Azure CosmosDB NoSQL <see cref="VectorStore"/> with the specified service ID
    /// and where the Azure CosmosDB NoSQL <see cref="Database"/> is constructed using the provided <paramref name="connectionString"/> and <paramref name="databaseName"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStore"/> on.</param>
    /// <param name="connectionString">Connection string required to connect to Azure CosmosDB NoSQL.</param>
    /// <param name="databaseName">Database name for Azure CosmosDB NoSQL.</param>
    /// <param name="options">Optional options to further configure the <see cref="VectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode("The Cosmos NoSQL provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The Cosmos NoSQL provider is currently incompatible with NativeAOT.")]
    public static IServiceCollection AddCosmosNoSqlVectorStore(
        this IServiceCollection services,
        string connectionString,
        string databaseName,
        CosmosNoSqlVectorStoreOptions? options = default,
        string? serviceId = default)
    {
        Verify.NotNullOrWhiteSpace(connectionString);
        Verify.NotNullOrWhiteSpace(databaseName);

        // If we are constructing Database, add the IVectorStore as singleton.
        services.AddKeyedSingleton<VectorStore>(
            serviceId,
            (sp, obj) =>
            {
                CosmosClientOptions clientOptions = new()
                {
                    ApplicationName = HttpHeaderConstant.Values.UserAgent,
                    UseSystemTextJsonSerializerWithOptions = options?.JsonSerializerOptions ?? JsonSerializerOptions.Default,
                };

                options ??= sp.GetService<CosmosNoSqlVectorStoreOptions>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return new CosmosNoSqlVectorStore(connectionString, databaseName, clientOptions, options);
            });

        return services;
    }

    /// <summary>
    /// Register an Azure CosmosDB NoSQL <see cref="VectorStoreCollection{TKey, TRecord}"/> and <see cref="IVectorSearchable{TRecord}"/> with the specified service ID
    /// and where the Azure CosmosDB NoSQL <see cref="Database"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStoreCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Optional options to further configure the <see cref="VectorStoreCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode("The Cosmos NoSQL provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The Cosmos NoSQL provider is currently incompatible with NativeAOT.")]
    public static IServiceCollection AddCosmosNoSqlVectorStoreRecordCollection<TRecord>(
        this IServiceCollection services,
        string collectionName,
        CosmosNoSqlCollectionOptions? options = default,
        string? serviceId = default)
        where TRecord : class
    {
        services.AddKeyedTransient<VectorStoreCollection<string, TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                var database = sp.GetRequiredService<Database>();
                options ??= sp.GetService<CosmosNoSqlCollectionOptions>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return new CosmosNoSqlCollection<string, TRecord>(database, collectionName, options);
            });

        AddVectorizedSearch<TRecord>(services, serviceId);

        return services;
    }

    /// <summary>
    /// Register an Azure CosmosDB NoSQL <see cref="VectorStoreCollection{TKey, TRecord}"/> and <see cref="IVectorSearchable{TRecord}"/> with the specified service ID
    /// and where the Azure CosmosDB NoSQL <see cref="Database"/> is constructed using the provided <paramref name="connectionString"/> and <paramref name="databaseName"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStoreCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="connectionString">Connection string required to connect to Azure CosmosDB NoSQL.</param>
    /// <param name="databaseName">Database name for Azure CosmosDB NoSQL.</param>
    /// <param name="options">Optional options to further configure the <see cref="VectorStoreCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode("The Cosmos NoSQL provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The Cosmos NoSQL provider is currently incompatible with NativeAOT.")]
    public static IServiceCollection AddCosmosNoSqlVectorStoreRecordCollection<TRecord>(
        this IServiceCollection services,
        string collectionName,
        string connectionString,
        string databaseName,
        CosmosNoSqlCollectionOptions? options = default,
        string? serviceId = default)
        where TRecord : class
    {
        Verify.NotNullOrWhiteSpace(collectionName);
        Verify.NotNullOrWhiteSpace(connectionString);
        Verify.NotNullOrWhiteSpace(databaseName);

        services.AddKeyedSingleton<VectorStoreCollection<string, TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                CosmosClientOptions clientOptions = new()
                {
                    ApplicationName = HttpHeaderConstant.Values.UserAgent,
                    UseSystemTextJsonSerializerWithOptions = options?.JsonSerializerOptions ?? JsonSerializerOptions.Default,
                };

                options ??= sp.GetService<CosmosNoSqlCollectionOptions>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return new CosmosNoSqlCollection<string, TRecord>(connectionString, databaseName, collectionName, clientOptions, options);
            });

        AddVectorizedSearch<TRecord>(services, serviceId);

        return services;
    }

    /// <summary>
    /// Also register the <see cref="VectorStoreCollection{TKey, TRecord}"/> with the given <paramref name="serviceId"/> as a <see cref="IVectorSearchable{TRecord}"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="services">The service collection to register on.</param>
    /// <param name="serviceId">The service id that the registrations should use.</param>
    private static void AddVectorizedSearch<TRecord>(IServiceCollection services, string? serviceId) where TRecord : class
    {
        services.AddKeyedTransient<IVectorSearchable<TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                return sp.GetRequiredKeyedService<VectorStoreCollection<string, TRecord>>(serviceId);
            });
    }
}
