// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Postgres;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register the Postgres <see cref="IVectorStore"/> instances on the <see cref="IKernelBuilder"/>.
/// </summary>
public static class PostgresKernelBuilderExtensions
{
    /// <summary>
    /// Register a Postgres <see cref="IVectorStore"/> with the specified service ID and where <see cref="IPostgresVectorStoreDbClient"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <param name="builder">The builder to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddPostgresVectorStore(this IKernelBuilder builder, PostgresVectorStoreOptions? options = default, string? serviceId = default)
    {
        builder.Services.AddPostgresVectorStore(options, serviceId);
        return builder;
    }
    /// <summary>
    /// Register a Postgres <see cref="IVectorStore"/> with the specified service ID and where <see cref="IPostgresVectorStoreDbClient"/> is constructed using the provided parameters.
    /// </summary>
    /// <param name="builder">The builder to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="connectionString">The Postgres connection string.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddPostgresVectorStore(this IKernelBuilder builder, string connectionString, PostgresVectorStoreOptions? options = default, string? serviceId = default)
    {
        builder.Services.AddPostgresVectorStore(connectionString, options, serviceId);
        return builder;
    }

    /// <summary>
    /// Register a Postgres <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/> with the specified service ID
    /// and where the Postgres <see cref="IPostgresVectorStoreDbClient"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="builder">The builder to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddPostgresVectorStoreRecordCollection<TKey, TRecord>(
        this IKernelBuilder builder,
        string collectionName,
        PostgresVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TKey : notnull
    {
        builder.Services.AddPostgresVectorStoreRecordCollection<TKey, TRecord>(collectionName, options, serviceId);
        return builder;
    }

    /// <summary>
    /// Register a Postgres <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/> with the specified service ID
    /// and where the Postgres <see cref="IPostgresVectorStoreDbClient"/> is constructed using the provided parameters.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="builder">The builder to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="connectionString">The Postgres connection string.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddPostgresVectorStoreRecordCollection<TKey, TRecord>(
        this IKernelBuilder builder,
        string collectionName,
        string connectionString,
        PostgresVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TKey : notnull
    {
        builder.Services.AddPostgresVectorStoreRecordCollection<TKey, TRecord>(collectionName, connectionString, options, serviceId);
        return builder;
    }
}
