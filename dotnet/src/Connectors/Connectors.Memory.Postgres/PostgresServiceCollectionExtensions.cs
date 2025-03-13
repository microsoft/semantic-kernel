// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Postgres;
using Npgsql;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register Postgres <see cref="IVectorStore"/> instances on an <see cref="IServiceCollection"/>.
/// </summary>
public static class PostgresServiceCollectionExtensions
{
    /// <summary>
    /// Registers a Postgres <see cref="IVectorStore"/>, retrieving the <see cref="NpgsqlDataSource"/> from the dependency injection container.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddPostgresVectorStore(
        this IServiceCollection serviceCollection,
        PostgresVectorStoreOptions? options = default,
        // Since we are not constructing the data source, add the IVectorStore as transient, since we
        // cannot make assumptions about how data source is being managed.
        ServiceLifetime lifetime = ServiceLifetime.Transient)
        => AddKeyedPostgresVectorStore(serviceCollection, serviceKey: null, options, lifetime);

    /// <summary>
    /// Register a keyed Postgres <see cref="IVectorStore"/>, retrieving the <see cref="NpgsqlDataSource"/> from the dependency injection container.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddKeyedPostgresVectorStore(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        PostgresVectorStoreOptions? options = default,
        // Since we are not constructing the data source, add the IVectorStore as transient, since we
        // cannot make assumptions about how data source is being managed.
        ServiceLifetime lifetime = ServiceLifetime.Transient)
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStore),
                serviceKey,
                (serviceProvider, _) => new PostgresVectorStore(
                    serviceProvider.GetRequiredService<NpgsqlDataSource>(),
                    options ?? serviceProvider.GetService<PostgresVectorStoreOptions>()),
                lifetime));

        return serviceCollection;
    }

    /// <summary>
    /// Registers a Postgres <see cref="IVectorStore"/> using the provided parameters.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="connectionString">Postgres database connection string.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddPostgresVectorStore(
        this IServiceCollection serviceCollection,
        string connectionString,
        PostgresVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    => AddKeyedPostgresVectorStore(serviceCollection, serviceKey: null, connectionString, options, lifetime);

    /// <summary>
    /// Registers a keyed Postgres <see cref="IVectorStore"/> using the provided parameters.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="connectionString">Postgres database connection string.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddKeyedPostgresVectorStore(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        string connectionString,
        PostgresVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        // Register NpgsqlDataSource to ensure proper disposal.
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(NpgsqlDataSource),
                serviceKey,
                (_, _) =>
                {
                    NpgsqlDataSourceBuilder dataSourceBuilder = new(connectionString);
                    dataSourceBuilder.UseVector();
                    return dataSourceBuilder.Build();
                },
                lifetime));

        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStore),
                serviceKey,
                (serviceProvider, _) => new PostgresVectorStore(
                    serviceProvider.GetRequiredKeyedService<NpgsqlDataSource>(serviceKey),
                    options ?? serviceProvider.GetService<PostgresVectorStoreOptions>()),
                lifetime));

        return serviceCollection;
    }

    /// <summary>
    /// Register a Postgres <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/>,
    /// retrieving the <see cref="NpgsqlDataSource"/> from the dependency injection container.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddPostgresVectorStoreRecordCollection<TKey, TRecord>(
        this IServiceCollection serviceCollection,
        string collectionName,
        PostgresVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Transient)
        where TKey : notnull
        => AddKeyedPostgresVectorStoreRecordCollection<TKey, TRecord>(serviceCollection, serviceKey: null, collectionName, options, lifetime);

    /// <summary>
    /// Register a keyed Postgres <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/>,
    /// retrieving the <see cref="NpgsqlDataSource"/> from the dependency injection container.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddKeyedPostgresVectorStoreRecordCollection<TKey, TRecord>(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        string collectionName,
        PostgresVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Transient)
        where TKey : notnull
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStoreRecordCollection<TKey, TRecord>),
                serviceKey,
                (serviceProvider, _) => new PostgresVectorStoreRecordCollection<TKey, TRecord>(
                    serviceProvider.GetRequiredService<NpgsqlDataSource>(),
                    collectionName,
                    options ?? serviceProvider.GetService<PostgresVectorStoreRecordCollectionOptions<TRecord>>()),
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
    /// Registers a Postgres <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/>,
    /// using the provided parameters.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="connectionString">Postgres database connection string.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddPostgresVectorStoreRecordCollection<TKey, TRecord>(
        this IServiceCollection serviceCollection,
        string collectionName,
        string connectionString,
        PostgresVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton) where TKey : notnull
        => AddKeyedPostgresVectorStoreRecordCollection<TKey, TRecord>(serviceCollection, serviceKey: null, collectionName, connectionString, options, lifetime);

    /// <summary>
    /// Registers a keyed Postgres <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/>,
    /// using the provided parameters.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="connectionString">Postgres database connection string.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the client. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddKeyedPostgresVectorStoreRecordCollection<TKey, TRecord>(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        string collectionName,
        string connectionString,
        PostgresVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton) where TKey : notnull
    {
        // Register NpgsqlDataSource to ensure proper disposal.
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(NpgsqlDataSource),
                serviceKey,
                (_, _) =>
                {
                    NpgsqlDataSourceBuilder dataSourceBuilder = new(connectionString);
                    dataSourceBuilder.UseVector();
                    return dataSourceBuilder.Build();
                },
                lifetime));

        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStoreRecordCollection<TKey, TRecord>),
                serviceKey,
                (serviceProvider, _) => new PostgresVectorStoreRecordCollection<TKey, TRecord>(
                    serviceProvider.GetRequiredKeyedService<NpgsqlDataSource>(serviceKey),
                    collectionName,
                    options),
                lifetime));

        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorizedSearch<TRecord>),
                serviceKey,
                static (serviceProvider, serviceKey) => serviceProvider.GetRequiredKeyedService<IVectorStoreRecordCollection<TKey, TRecord>>(serviceKey),
                lifetime));

        return serviceCollection;
    }
}
