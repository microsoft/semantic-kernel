// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.SqliteVec;

namespace Microsoft.Extensions.DependencyInjection;

/// <summary>
/// Extension methods to register SQLite <see cref="VectorStore"/> instances on an <see cref="IServiceCollection"/>.
/// </summary>
public static class SqliteServiceCollectionExtensions
{
    /// <summary>
    /// Registers a <see cref="SqliteVectorStore"/> as <see cref="VectorStore"/>, with the specified connection string and service lifetime.
    /// </summary>
    /// <inheritdoc cref="AddVectorStore"/>
    public static IServiceCollection AddSqliteVectorStore(
        this IServiceCollection services,
        Func<IServiceProvider, string> connectionStringProvider,
        Func<IServiceProvider, SqliteVectorStoreOptions>? optionsProvider = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        => AddVectorStore(services, serviceKey: null, connectionStringProvider, optionsProvider, lifetime);

    /// <inheritdoc cref="AddVectorStore"/>
    public static IServiceCollection AddKeyedSqliteVectorStore(
        this IServiceCollection services,
        object serviceKey,
        Func<IServiceProvider, string> connectionStringProvider,
        Func<IServiceProvider, SqliteVectorStoreOptions>? optionsProvider = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNull(serviceKey);

        return AddVectorStore(services, serviceKey, connectionStringProvider, optionsProvider, lifetime);
    }

    /// <summary>
    /// Registers a keyed <see cref="SqliteVectorStore"/> as <see cref="VectorStore"/>, with the specified connection string and service lifetime.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStore"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="connectionStringProvider">The connection string provider.</param>
    /// <param name="optionsProvider">Options provider to further configure the vector store.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    private static IServiceCollection AddVectorStore(
        IServiceCollection services,
        object? serviceKey,
        Func<IServiceProvider, string> connectionStringProvider,
        Func<IServiceProvider, SqliteVectorStoreOptions>? optionsProvider,
        ServiceLifetime lifetime)
    {
        Verify.NotNull(services);
        Verify.NotNull(connectionStringProvider);

        services.Add(new ServiceDescriptor(typeof(SqliteVectorStore), serviceKey, (sp, _) =>
        {
            var connectionString = connectionStringProvider(sp);
            var options = GetStoreOptions(sp, optionsProvider);
            return new SqliteVectorStore(connectionString, options);
        }, lifetime));

        services.Add(new ServiceDescriptor(typeof(VectorStore), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<SqliteVectorStore>(key), lifetime));

        return services;
    }

    /// <summary>
    /// Registers a <see cref="SqliteCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>, with the specified connection string and service lifetime.
    /// </summary>
    /// <inheritdoc cref="AddCollection{TKey, TRecord}(IServiceCollection, object?, string, Func{IServiceProvider, string}, Func{IServiceProvider, SqliteCollectionOptions}?, ServiceLifetime)"/>
    public static IServiceCollection AddSqliteCollection<TKey, TRecord>(
        this IServiceCollection services,
        string collectionName,
        Func<IServiceProvider, string> connectionStringProvider,
        Func<IServiceProvider, SqliteCollectionOptions>? optionsProvider = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : class
        => AddCollection<TKey, TRecord>(services, serviceKey: null, collectionName, connectionStringProvider, optionsProvider, lifetime);

    /// <inheritdoc cref="AddCollection{TKey, TRecord}(IServiceCollection, object?, string, Func{IServiceProvider, string}, Func{IServiceProvider, SqliteCollectionOptions}?, ServiceLifetime)"/>
    public static IServiceCollection AddKeyedSqliteCollection<TKey, TRecord>(
        this IServiceCollection services,
        object serviceKey,
        string collectionName,
        Func<IServiceProvider, string> connectionStringProvider,
        Func<IServiceProvider, SqliteCollectionOptions>? optionsProvider = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : class
    {
        Verify.NotNull(serviceKey);

        return AddCollection<TKey, TRecord>(services, serviceKey, collectionName, connectionStringProvider, optionsProvider, lifetime);
    }

    /// <summary>
    /// Registers a keyed <see cref="SqliteCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>, with the specified connection string and service lifetime.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStoreCollection{TKey, TRecord}"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the collection.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="connectionStringProvider">The connection string provider.</param>
    /// <param name="optionsProvider">Options provider to further configure the collection.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    private static IServiceCollection AddCollection<TKey, TRecord>(
        this IServiceCollection services,
        object? serviceKey,
        string collectionName,
        Func<IServiceProvider, string> connectionStringProvider,
        Func<IServiceProvider, SqliteCollectionOptions?>? optionsProvider = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : class
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(collectionName);
        Verify.NotNull(connectionStringProvider);

        services.Add(new ServiceDescriptor(typeof(SqliteCollection<TKey, TRecord>), serviceKey, (sp, _) =>
        {
            var connectionString = connectionStringProvider(sp);
            var options = GetCollectionOptions(sp, optionsProvider);
            return new SqliteCollection<TKey, TRecord>(connectionString, collectionName, options);
        }, lifetime));

        services.Add(new ServiceDescriptor(typeof(VectorStoreCollection<TKey, TRecord>), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<SqliteCollection<TKey, TRecord>>(key), lifetime));

        services.Add(new ServiceDescriptor(typeof(IVectorSearchable<TRecord>), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<SqliteCollection<TKey, TRecord>>(key), lifetime));

        // Once HybridSearch supports get implemented by SqliteCollection
        // we need to add IKeywordHybridSearchable abstraction here as well.

        return services;
    }

    /// <summary>
    /// Registers a <see cref="SqliteCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>, with the specified connection string and service lifetime.
    /// </summary>
    /// <inheritdoc cref="AddCollection{TKey, TRecord}(IServiceCollection, object?, string, string, SqliteCollectionOptions?, ServiceLifetime)"/>/>
    public static IServiceCollection AddSqliteCollection<TKey, TRecord>(
        this IServiceCollection services,
        string collectionName,
        string connectionString,
        SqliteCollectionOptions? options = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : class
        => AddCollection<TKey, TRecord>(services, serviceKey: null, collectionName, connectionString, options, lifetime);

    /// <inheritdoc cref="AddCollection{TKey, TRecord}(IServiceCollection, object?, string, string, SqliteCollectionOptions?, ServiceLifetime)"/>/>
    public static IServiceCollection AddKeyedSqliteCollection<TKey, TRecord>(
        this IServiceCollection services,
        object serviceKey,
        string collectionName,
        string connectionString,
        SqliteCollectionOptions? options = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : class
    {
        Verify.NotNull(serviceKey);

        return AddCollection<TKey, TRecord>(services, serviceKey, collectionName, connectionString, options, lifetime);
    }

    /// <summary>
    /// Registers a keyed <see cref="SqliteCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>, with the specified connection string and service lifetime.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStoreCollection{TKey, TRecord}"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the collection.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="connectionString">The connection string.</param>
    /// <param name="options">Options to further configure the collection.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    private static IServiceCollection AddCollection<TKey, TRecord>(
        this IServiceCollection services,
        object? serviceKey,
        string collectionName,
        string connectionString,
        SqliteCollectionOptions? options = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : class
    {
        Verify.NotNullOrWhiteSpace(connectionString);

        return AddCollection<TKey, TRecord>(services, serviceKey, collectionName, _ => connectionString, _ => options, lifetime);
    }

    private static SqliteVectorStoreOptions? GetStoreOptions(IServiceProvider sp, Func<IServiceProvider, SqliteVectorStoreOptions?>? optionsProvider)
    {
        var options = optionsProvider?.Invoke(sp);
        if (options?.EmbeddingGenerator is not null)
        {
            return options; // The user has provided everything, there is nothing to change.
        }

        var embeddingGenerator = sp.GetService<IEmbeddingGenerator>();
        return embeddingGenerator is null
            ? options // There is nothing to change.
            : new(options, embeddingGenerator); // Create a brand new copy in order to avoid modifying the original options.
    }

    private static SqliteCollectionOptions? GetCollectionOptions(IServiceProvider sp, Func<IServiceProvider, SqliteCollectionOptions?>? optionsProvider)
    {
        var options = optionsProvider?.Invoke(sp);
        if (options?.EmbeddingGenerator is not null)
        {
            return options; // The user has provided everything, there is nothing to change.
        }

        var embeddingGenerator = sp.GetService<IEmbeddingGenerator>();
        return embeddingGenerator is null
            ? options // There is nothing to change.
            : new(options, embeddingGenerator); // Create a brand new copy in order to avoid modifying the original options.
    }
}
