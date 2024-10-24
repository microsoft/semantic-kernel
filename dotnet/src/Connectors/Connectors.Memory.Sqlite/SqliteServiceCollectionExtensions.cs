// Copyright (c) Microsoft. All rights reserved.

using System.Data;
using Microsoft.Data.Sqlite;
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
    public static IServiceCollection AddSqliteVectorStore(
        this IServiceCollection services,
        SqliteVectorStoreOptions? options = default,
        string? serviceId = default)
    {
        services.AddKeyedTransient<IVectorStore>(
            serviceId,
            (sp, obj) =>
            {
                var connection = sp.GetRequiredService<SqliteConnection>();

                if (connection.State != ConnectionState.Open)
                {
                    connection.Open();
                }

                var selectedOptions = options ?? sp.GetService<SqliteVectorStoreOptions>();

                return new SqliteVectorStore(connection, options);
            });

        return services;
    }

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
    {
        services.AddKeyedTransient<IVectorStore>(
            serviceId,
            (sp, obj) =>
            {
                var connection = new SqliteConnection(connectionString);
                var extensionName = GetExtensionName(options?.VectorSearchExtensionName);

                connection.Open();

                connection.LoadExtension(extensionName);

                var selectedOptions = options ?? sp.GetService<SqliteVectorStoreOptions>();
                return new SqliteVectorStore(connection, options);
            });

        return services;
    }

    /// <summary>
    /// Register a SQLite <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/> with the specified service ID
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
    public static IServiceCollection AddSqliteVectorStoreRecordCollection<TKey, TRecord>(
        this IServiceCollection services,
        string collectionName,
        SqliteVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TKey : notnull
    {
        services.AddKeyedTransient<IVectorStoreRecordCollection<TKey, TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                var connection = sp.GetRequiredService<SqliteConnection>();

                if (connection.State != ConnectionState.Open)
                {
                    connection.Open();
                }

                var selectedOptions = options ?? sp.GetService<SqliteVectorStoreRecordCollectionOptions<TRecord>>();

                return (new SqliteVectorStoreRecordCollection<TRecord>(connection, collectionName, selectedOptions) as IVectorStoreRecordCollection<TKey, TRecord>)!;
            });

        AddVectorizedSearch<TKey, TRecord>(services, serviceId);

        return services;
    }

    /// <summary>
    /// Register a SQLite <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/> with the specified service ID.
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
    {
        services.AddKeyedTransient<IVectorStoreRecordCollection<TKey, TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                var connection = new SqliteConnection(connectionString);
                var extensionName = GetExtensionName(options?.VectorSearchExtensionName);

                connection.Open();

                connection.LoadExtension(extensionName);

                var selectedOptions = options ?? sp.GetService<SqliteVectorStoreRecordCollectionOptions<TRecord>>();

                return (new SqliteVectorStoreRecordCollection<TRecord>(connection, collectionName, selectedOptions) as IVectorStoreRecordCollection<TKey, TRecord>)!;
            });

        AddVectorizedSearch<TKey, TRecord>(services, serviceId);

        return services;
    }

    /// <summary>
    /// Also register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> with the given <paramref name="serviceId"/> as a <see cref="IVectorizedSearch{TRecord}"/>.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="services">The service collection to register on.</param>
    /// <param name="serviceId">The service id that the registrations should use.</param>
    private static void AddVectorizedSearch<TKey, TRecord>(IServiceCollection services, string? serviceId)
        where TKey : notnull
    {
        services.AddKeyedTransient<IVectorizedSearch<TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                return sp.GetRequiredKeyedService<IVectorStoreRecordCollection<TKey, TRecord>>(serviceId);
            });
    }

    /// <summary>
    /// Returns extension name for vector search.
    /// </summary>
    private static string GetExtensionName(string? extensionName)
    {
        return !string.IsNullOrWhiteSpace(extensionName) ? extensionName! : SqliteConstants.VectorSearchExtensionName;
    }
}
