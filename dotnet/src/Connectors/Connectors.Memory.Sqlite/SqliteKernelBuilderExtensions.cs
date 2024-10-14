// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Data.Sqlite;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Sqlite;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register SQLite <see cref="IVectorStore"/> instances on the <see cref="IKernelBuilder"/>.
/// </summary>
public static class SqliteKernelBuilderExtensions
{
    /// <summary>
    /// Register a SQLite <see cref="IVectorStore"/> with the specified service ID
    /// and where the SQLite <see cref="SqliteConnection"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <param name="builder">The builder to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Kernel builder.</returns>
    public static IKernelBuilder AddSqliteVectorStore(
        this IKernelBuilder builder,
        SqliteVectorStoreOptions? options = default,
        string? serviceId = default)
    {
        builder.Services.AddSqliteVectorStore(options, serviceId);
        return builder;
    }

    /// <summary>
    /// Register a SQLite <see cref="IVectorStore"/> with the specified service ID.
    /// </summary>
    /// <param name="builder">The builder to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="connectionString">Connection string for <see cref="SqliteConnection"/>.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Kernel builder.</returns>
    public static IKernelBuilder AddSqliteVectorStore(
        this IKernelBuilder builder,
        string connectionString,
        SqliteVectorStoreOptions? options = default,
        string? serviceId = default)
    {
        builder.Services.AddSqliteVectorStore(connectionString, options, serviceId);
        return builder;
    }

    /// <summary>
    /// Register a SQLite <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/> with the specified service ID
    /// and where the SQLite <see cref="SqliteConnection"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="builder">The builder to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Kernel builder.</returns>
    public static IKernelBuilder AddSqliteVectorStoreRecordCollection<TKey, TRecord>(
        this IKernelBuilder builder,
        string collectionName,
        SqliteVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TKey : notnull
        where TRecord : class
    {
        builder.Services.AddSqliteVectorStoreRecordCollection<TKey, TRecord>(collectionName, options, serviceId);
        return builder;
    }

    /// <summary>
    /// Register a SQLite <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/> with the specified service ID.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="builder">The builder to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="connectionString">Connection string for <see cref="SqliteConnection"/>.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Kernel builder.</returns>
    public static IKernelBuilder AddSqliteVectorStoreRecordCollection<TKey, TRecord>(
        this IKernelBuilder builder,
        string collectionName,
        string connectionString,
        SqliteVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TKey : notnull
        where TRecord : class
    {
        builder.Services.AddSqliteVectorStoreRecordCollection<TKey, TRecord>(collectionName, connectionString, options, serviceId);
        return builder;
    }
}
