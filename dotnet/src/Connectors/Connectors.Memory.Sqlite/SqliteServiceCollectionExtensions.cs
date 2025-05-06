// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Data.Sqlite;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Sqlite;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register SQLite <see cref="VectorStore"/> instances on an <see cref="IServiceCollection"/>.
/// </summary>
public static class SqliteServiceCollectionExtensions
{
    /// <summary>
    /// Register a SQLite <see cref="VectorStore"/> with the specified service ID.
    /// <see cref="SqliteConnection"/> instance will be initialized, connection will be opened and vector search extension with be loaded.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStore"/> on.</param>
    /// <param name="connectionString">Connection string for <see cref="SqliteConnection"/>.</param>
    /// <param name="options">Optional options to further configure the <see cref="VectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddSqliteVectorStore(
        this IServiceCollection services,
        string connectionString,
        SqliteVectorStoreOptions? options = default,
        string? serviceId = default)
        => services.AddKeyedSingleton<VectorStore>(
            serviceId,
            (sp, _) => new SqliteVectorStore(connectionString, options ?? sp.GetService<SqliteVectorStoreOptions>() ?? new() { EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>() }));

    /// <summary>
    /// Register a SQLite <see cref="VectorStoreCollection{TKey, TRecord}"/> and <see cref="IVectorSearchable{TRecord}"/> with the specified service ID.
    /// <see cref="SqliteConnection"/> instance will be initialized, connection will be opened and vector search extension with be loaded.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStoreCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="connectionString">Connection string for <see cref="SqliteConnection"/>.</param>
    /// <param name="options">Optional options to further configure the <see cref="VectorStoreCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddSqliteVectorStoreRecordCollection<TKey, TRecord>(
        this IServiceCollection services,
        string collectionName,
        string connectionString,
        SqliteCollectionOptions? options = default,
        string? serviceId = default)
        where TKey : notnull
        where TRecord : class
    {
        services.AddKeyedSingleton<VectorStoreCollection<TKey, TRecord>>(
            serviceId,
            (sp, _) => (
                new SqliteCollection<TKey, TRecord>(
                    connectionString,
                    collectionName,
                    options ?? sp.GetService<SqliteCollectionOptions>() ?? new()
                    {
                        EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                    })
                    as VectorStoreCollection<TKey, TRecord>)!);

        AddVectorizedSearch<TKey, TRecord>(services, serviceId);

        return services;
    }

    /// <summary>
    /// Also register the <see cref="VectorStoreCollection{TKey, TRecord}"/> with the given <paramref name="serviceId"/> as a <see cref="IVectorSearchable{TRecord}"/>.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="services">The service collection to register on.</param>
    /// <param name="serviceId">The service id that the registrations should use.</param>
    private static void AddVectorizedSearch<TKey, TRecord>(IServiceCollection services, string? serviceId) where TRecord : class
        where TKey : notnull
        => services.AddKeyedSingleton<IVectorSearchable<TRecord>>(
            serviceId,
            (sp, _) => sp.GetRequiredKeyedService<VectorStoreCollection<TKey, TRecord>>(serviceId));
}
