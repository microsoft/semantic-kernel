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
    /// Registers a SQLite <see cref="IVectorStore"/>, retrieving the SQLite <see cref="SqliteConnection"/> from the dependency injection container.
    /// In this case vector search extension loading should be handled manually.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddSqliteVectorStore(
        this IServiceCollection serviceCollection,
        SqliteVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Transient)
    => AddKeyedSqliteVectorStore(serviceCollection, serviceKey: null, options, lifetime);

    /// <summary>
    /// Registers a keyed SQLite <see cref="IVectorStore"/>, retrieving the SQLite <see cref="SqliteConnection"/> from the dependency injection container.
    /// In this case vector search extension loading should be handled manually.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddKeyedSqliteVectorStore(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        SqliteVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Transient)
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStore),
                serviceKey,
                (serviceProvider, _) =>
                {
                    var connection = serviceProvider.GetRequiredService<SqliteConnection>();

                    if (connection.State != ConnectionState.Open)
                    {
                        connection.Open();
                    }

                    return new SqliteVectorStore(connection, options ?? serviceProvider.GetService<SqliteVectorStoreOptions>());
                },
                lifetime));

        return serviceCollection;
    }

    /// <summary>
    /// Registers a SQLite <see cref="IVectorStore"/>, using the specified connection string.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="connectionString">Connection string for <see cref="SqliteConnection"/>.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddSqliteVectorStore(
        this IServiceCollection serviceCollection,
        string connectionString,
        SqliteVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Transient)
        => AddKeyedSqliteVectorStore(serviceCollection, serviceKey: null, connectionString, options, lifetime);

    /// <summary>
    /// Registers a keyed SQLite <see cref="IVectorStore"/>, using the specified connection string.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="connectionString">Connection string for <see cref="SqliteConnection"/>.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddKeyedSqliteVectorStore(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        string connectionString,
        SqliteVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Transient)
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStore),
                serviceKey,
                (serviceProvider, _) =>
                {
                    var connection = new SqliteConnection(connectionString);
                    var extensionName = GetExtensionName(options?.VectorSearchExtensionName);

                    connection.Open();
                    connection.LoadExtension(extensionName);

                    return new SqliteVectorStore(connection, options ?? serviceProvider.GetService<SqliteVectorStoreOptions>());
                },
                lifetime));

        return serviceCollection;
    }

    /// <summary>
    /// Registers a SQLite <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/>,
    /// retrieving the <see cref="SqliteConnection"/> from the dependency injection container.
    /// In this case vector search extension loading should be handled manually.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddSqliteVectorStoreRecordCollection<TKey, TRecord>(
        this IServiceCollection serviceCollection,
        string collectionName,
        SqliteVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Transient)
        where TKey : notnull
        => AddKeyedSqliteVectorStoreRecordCollection<TKey, TRecord>(serviceCollection, serviceKey: null, collectionName, options, lifetime);

    /// <summary>
    /// Registers a keyed SQLite <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/>,
    /// retrieving the <see cref="SqliteConnection"/> from the dependency injection container.
    /// In this case vector search extension loading should be handled manually.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddKeyedSqliteVectorStoreRecordCollection<TKey, TRecord>(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        string collectionName,
        SqliteVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Transient)
        where TKey : notnull
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStoreRecordCollection<TKey, TRecord>),
                serviceKey,
                (serviceProvider, _) =>
                {
                    var connection = serviceProvider.GetRequiredService<SqliteConnection>();

                    if (connection.State != ConnectionState.Open)
                    {
                        connection.Open();
                    }

                    return new SqliteVectorStoreRecordCollection<TRecord>(
                        connection,
                        collectionName,
                        options ?? serviceProvider.GetService<SqliteVectorStoreRecordCollectionOptions<TRecord>>());
                },
                lifetime));

        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorizedSearch<TRecord>),
                serviceKey,
                static (serviceProvider, serviceKey) => serviceProvider.GetRequiredKeyedService<IVectorStoreRecordCollection<TKey, TRecord>>(serviceKey),
                lifetime));

        return serviceCollection;
    }

    /// <summary>
    /// Registers a SQLite <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/> usihng the provided connection string/
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="connectionString">Connection string for <see cref="SqliteConnection"/>.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddSqliteVectorStoreRecordCollection<TKey, TRecord>(
        this IServiceCollection serviceCollection,
        string collectionName,
        string connectionString,
        SqliteVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Transient)
        where TKey : notnull
        => AddKeyedSqliteVectorStoreRecordCollection<TKey, TRecord>(serviceCollection, serviceKey: null, collectionName, connectionString, options, lifetime);

    /// <summary>
    /// Registers a keyed SQLite <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/> usihng the provided connection string/
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="connectionString">Connection string for <see cref="SqliteConnection"/>.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddKeyedSqliteVectorStoreRecordCollection<TKey, TRecord>(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        string collectionName,
        string connectionString,
        SqliteVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Transient)
        where TKey : notnull
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStoreRecordCollection<TKey, TRecord>),
                serviceKey,
                (serviceProvider, _) =>
                {
                    var connection = new SqliteConnection(connectionString);
                    var extensionName = GetExtensionName(options?.VectorSearchExtensionName);

                    connection.Open();
                    connection.LoadExtension(extensionName);

                    return new SqliteVectorStoreRecordCollection<TRecord>(
                        connection,
                        collectionName,
                        options ?? serviceProvider.GetService<SqliteVectorStoreRecordCollectionOptions<TRecord>>());
                },
                lifetime));

        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorizedSearch<TRecord>),
                serviceKey,
                static (serviceProvider, serviceKey) => serviceProvider.GetRequiredKeyedService<IVectorStoreRecordCollection<TKey, TRecord>>(serviceKey),
                lifetime));

        return serviceCollection;
    }

    /// <summary>
    /// Returns extension name for vector search.
    /// </summary>
    private static string GetExtensionName(string? extensionName)
        => !string.IsNullOrWhiteSpace(extensionName) ? extensionName! : SqliteConstants.VectorSearchExtensionName;
}
