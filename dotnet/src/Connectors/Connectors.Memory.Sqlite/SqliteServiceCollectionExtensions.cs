// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Data.Sqlite;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Sqlite;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register SQLite <see cref="IVectorStore"/> instances on an <see cref="IServiceCollection"/>.
/// </summary>
public static class SqliteServiceCollectionExtensions
{
    /// <summary>
    /// Register a SQLite <see cref="IVectorStore"/> with the specified service ID
    /// and where the SQLite <see cref="SqliteConnection"/> is retrieved from the dependency injection container.
    /// In this case vector search extension loading should be handled manually.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    [Obsolete("Use AddSqliteVectorStore with connectionString instead.", error: true)]
    public static IServiceCollection AddSqliteVectorStore(
        this IServiceCollection services,
        SqliteVectorStoreOptions? options = default,
        string? serviceId = default)
        => throw new InvalidOperationException("Use AddSqliteVectorStore with connectionString instead.");

    /// <summary>
    /// Register a SQLite <see cref="IVectorStore"/> with the specified service ID.
    /// <see cref="SqliteConnection"/> instance will be initialized, connection will be opened and vector search extension with be loaded.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="connectionString">Connection string for <see cref="SqliteConnection"/>.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddSqliteVectorStore(
        this IServiceCollection services,
        string connectionString,
        SqliteVectorStoreOptions? options = default,
        string? serviceId = default)
        => services.AddKeyedSingleton<IVectorStore>(
            serviceId,
            (sp, _) => new SqliteVectorStore(connectionString, options ?? sp.GetService<SqliteVectorStoreOptions>() ?? new() { EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>() }));

    /// <summary>
    /// Register a SQLite <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorSearch{TRecord}"/> with the specified service ID
    /// and where the SQLite <see cref="SqliteConnection"/> is retrieved from the dependency injection container.
    /// In this case vector search extension loading should be handled manually.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    [Obsolete("Use AddSqliteVectorStoreRecordCollection with connectionString instead.", error: true)]
    public static IServiceCollection AddSqliteVectorStoreRecordCollection<TKey, TRecord>(
        this IServiceCollection services,
        string collectionName,
        SqliteVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TKey : notnull
        => throw new InvalidOperationException("Use AddSqliteVectorStore with connectionString instead.");

    /// <summary>
    /// Register a SQLite <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorSearch{TRecord}"/> with the specified service ID.
    /// <see cref="SqliteConnection"/> instance will be initialized, connection will be opened and vector search extension with be loaded.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="connectionString">Connection string for <see cref="SqliteConnection"/>.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddSqliteVectorStoreRecordCollection<TKey, TRecord>(
        this IServiceCollection services,
        string collectionName,
        string connectionString,
        SqliteVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TKey : notnull
        where TRecord : notnull
    {
        services.AddKeyedSingleton<IVectorStoreRecordCollection<TKey, TRecord>>(
            serviceId,
            (sp, _) => (
                new SqliteVectorStoreRecordCollection<TKey, TRecord>(
                    connectionString,
                    collectionName,
                    options ?? sp.GetService<SqliteVectorStoreRecordCollectionOptions<TRecord>>() ?? new()
                    {
                        EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                    })
                    as IVectorStoreRecordCollection<TKey, TRecord>)!);

        AddVectorizedSearch<TKey, TRecord>(services, serviceId);

        return services;
    }

    /// <summary>
    /// Also register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> with the given <paramref name="serviceId"/> as a <see cref="IVectorSearch{TRecord}"/>.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="services">The service collection to register on.</param>
    /// <param name="serviceId">The service id that the registrations should use.</param>
    private static void AddVectorizedSearch<TKey, TRecord>(IServiceCollection services, string? serviceId) where TRecord : notnull
        where TKey : notnull
        => services.AddKeyedSingleton<IVectorSearch<TRecord>>(
            serviceId,
            (sp, _) => sp.GetRequiredKeyedService<IVectorStoreRecordCollection<TKey, TRecord>>(serviceId));
}
