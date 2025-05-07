// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.SqlServer;

namespace Microsoft.Extensions.DependencyInjection;

/// <summary>
/// Extension methods to register <see cref="SqlServerVectorStore"/> instances on an <see cref="IServiceCollection"/>.
/// </summary>
public static class SqlServerServiceCollectionExtensions
{
    /// <summary>
    /// Registers a <see cref="SqlServerVectorStore"/> as <see cref="VectorStore"/>, with the specified connection string and service lifetime.
    /// </summary>
    /// <inheritdoc cref="AddVectorStore"/>
    public static IServiceCollection AddSqlServerVectorStore(
        this IServiceCollection services,
        Func<IServiceProvider, string> connectionStringProvider,
        Func<IServiceProvider, SqlServerVectorStoreOptions>? optionsProvider = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        => AddVectorStore(services, serviceKey: null, connectionStringProvider, optionsProvider, lifetime);

    /// <inheritdoc cref="AddVectorStore"/>
    public static IServiceCollection AddKeyedSqlServerVectorStore(
        this IServiceCollection services,
        object serviceKey,
        Func<IServiceProvider, string> connectionStringProvider,
        Func<IServiceProvider, SqlServerVectorStoreOptions>? optionsProvider = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNull(serviceKey);

        return AddVectorStore(services, serviceKey, connectionStringProvider, optionsProvider, lifetime);
    }

    /// <summary>
    /// Registers a keyed <see cref="SqlServerVectorStore"/> as <see cref="VectorStore"/>, with the specified connection string and service lifetime.
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
        Func<IServiceProvider, SqlServerVectorStoreOptions>? optionsProvider,
        ServiceLifetime lifetime)
    {
        Verify.NotNull(services);
        Verify.NotNull(connectionStringProvider);

        services.Add(new ServiceDescriptor(typeof(SqlServerVectorStore), serviceKey, (sp, _) =>
        {
            var connectionString = connectionStringProvider(sp);
            var options = GetStoreOptions(sp, optionsProvider);
            return new SqlServerVectorStore(connectionString, options);
        }, lifetime));

        services.Add(new ServiceDescriptor(typeof(VectorStore), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<SqlServerVectorStore>(key), lifetime));

        return services;
    }

    /// <summary>
    /// Registers a <see cref="SqlServerCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>, with the specified connection string and service lifetime.
    /// </summary>
    /// <inheritdoc cref="AddCollection{TKey, TRecord}(IServiceCollection, object?, string, Func{IServiceProvider, string}, Func{IServiceProvider, SqlServerCollectionOptions}?, ServiceLifetime)"/>
    public static IServiceCollection AddSqlServerCollection<TKey, TRecord>(
        this IServiceCollection services,
        string collectionName,
        Func<IServiceProvider, string> connectionStringProvider,
        Func<IServiceProvider, SqlServerCollectionOptions>? optionsProvider = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : class
        => AddCollection<TKey, TRecord>(services, serviceKey: null, collectionName, connectionStringProvider, optionsProvider, lifetime);

    /// <inheritdoc cref="AddCollection{TKey, TRecord}(IServiceCollection, object?, string, Func{IServiceProvider, string}, Func{IServiceProvider, SqlServerCollectionOptions}?, ServiceLifetime)"/>
    public static IServiceCollection AddKeyedSqlServerCollection<TKey, TRecord>(
        this IServiceCollection services,
        object serviceKey,
        string collectionName,
        Func<IServiceProvider, string> connectionStringProvider,
        Func<IServiceProvider, SqlServerCollectionOptions>? optionsProvider = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : class
    {
        Verify.NotNull(serviceKey);

        return AddCollection<TKey, TRecord>(services, serviceKey, collectionName, connectionStringProvider, optionsProvider, lifetime);
    }

    /// <summary>
    /// Registers a keyed <see cref="SqlServerCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>, with the specified connection string and service lifetime.
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
        Func<IServiceProvider, SqlServerCollectionOptions?>? optionsProvider = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : class
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(collectionName);
        Verify.NotNull(connectionStringProvider);

        services.Add(new ServiceDescriptor(typeof(SqlServerCollection<TKey, TRecord>), serviceKey, (sp, _) =>
        {
            var connectionString = connectionStringProvider(sp);
            var options = GetCollectionOptions(sp, optionsProvider);
            return new SqlServerCollection<TKey, TRecord>(connectionString, collectionName, options);
        }, lifetime));

        services.Add(new ServiceDescriptor(typeof(VectorStoreCollection<TKey, TRecord>), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<SqlServerCollection<TKey, TRecord>>(key), lifetime));

        services.Add(new ServiceDescriptor(typeof(IVectorSearchable<TRecord>), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<SqlServerCollection<TKey, TRecord>>(key), lifetime));

        // Once HybridSearch supports get implemented (https://github.com/microsoft/semantic-kernel/issues/11080)
        // we need to add IKeywordHybridSearchable abstraction here as well.

        return services;
    }

    /// <summary>
    /// Registers a <see cref="SqlServerCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>, with the specified connection string and service lifetime.
    /// </summary>
    /// <inheritdoc cref="AddCollection{TKey, TRecord}(IServiceCollection, object?, string, string, SqlServerCollectionOptions?, ServiceLifetime)"/>/>
    public static IServiceCollection AddSqlServerCollection<TKey, TRecord>(
        this IServiceCollection services,
        string collectionName,
        string connectionString,
        SqlServerCollectionOptions? options = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : class
        => AddCollection<TKey, TRecord>(services, serviceKey: null, collectionName, connectionString, options, lifetime);

    /// <inheritdoc cref="AddCollection{TKey, TRecord}(IServiceCollection, object?, string, string, SqlServerCollectionOptions?, ServiceLifetime)"/>/>
    public static IServiceCollection AddKeyedSqlServerCollection<TKey, TRecord>(
        this IServiceCollection services,
        object serviceKey,
        string collectionName,
        string connectionString,
        SqlServerCollectionOptions? options = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : class
    {
        Verify.NotNull(serviceKey);

        return AddCollection<TKey, TRecord>(services, serviceKey, collectionName, connectionString, options, lifetime);
    }

    /// <summary>
    /// Registers a keyed <see cref="SqlServerCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>, with the specified connection string and service lifetime.
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
        SqlServerCollectionOptions? options = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : class
    {
        Verify.NotNullOrWhiteSpace(connectionString);

        return AddCollection<TKey, TRecord>(services, serviceKey, collectionName, _ => connectionString, _ => options, lifetime);
    }

    private static SqlServerVectorStoreOptions? GetStoreOptions(IServiceProvider sp, Func<IServiceProvider, SqlServerVectorStoreOptions?>? optionsProvider)
    {
        var options = optionsProvider?.Invoke(sp);
        return new() // Create a new instance to avoid modifying the original options.
        {
            // Don't override the embedding generator if the user has provided one.
            EmbeddingGenerator = options?.EmbeddingGenerator ?? sp.GetService<IEmbeddingGenerator>(),
            Schema = options?.Schema,
        };
    }

    private static SqlServerCollectionOptions? GetCollectionOptions(IServiceProvider sp, Func<IServiceProvider, SqlServerCollectionOptions?>? optionsProvider)
    {
        var options = optionsProvider?.Invoke(sp);
        return new() // Create a new instance to avoid modifying the original options.
        {
            // Don't override the embedding generator if the user has provided one.
            EmbeddingGenerator = options?.EmbeddingGenerator ?? sp.GetService<IEmbeddingGenerator>(),
            Schema = options?.Schema,
        };
    }
}
