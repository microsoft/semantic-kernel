// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

/// <summary>
/// Extension methods to register <see cref="SqlServerVectorStore"/> instances on an <see cref="IServiceCollection"/>.
/// </summary>
public static class SqlServerServiceCollectionExtensions
{
    /// <summary>
    /// Registers a <see cref="SqlServerVectorStore"/> as <see cref="IVectorStore"/>, with the specified connection string and service lifetime.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="connectionStringProvider">The connection string provider.</param>
    /// <param name="optionsProvider">Options provider to further configure the vector store.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddSqlServerVectorStore(this IServiceCollection services,
        Func<IServiceProvider, string> connectionStringProvider,
        Func<IServiceProvider, SqlServerVectorStoreOptions>? optionsProvider = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNull(services);
        Verify.NotNull(connectionStringProvider);

        services.Add(new ServiceDescriptor(typeof(SqlServerVectorStore), sp =>
        {
            var connectionString = connectionStringProvider(sp);
            var options = optionsProvider?.Invoke(sp);
            return new SqlServerVectorStore(connectionString, options);
        }, lifetime));

        // We try to add the SqlServerVectorStore as an IVectorStore,
        // but if it already exists, we don't override it.
        // Sample scenario: one app using two different vector stores.
        services.TryAdd(new ServiceDescriptor(typeof(IVectorStore),
            static sp => sp.GetRequiredService<SqlServerVectorStore>(), lifetime));

        return services;
    }

    /// <summary>
    /// Registers a keyed <see cref="SqlServerVectorStore"/> as <see cref="IVectorStore"/>, with the specified connection string and service lifetime.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="connectionStringProvider">The connection string provider.</param>
    /// <param name="optionsProvider">Options provider to further configure the vector store.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddKeyedSqlServerVectorStore(this IServiceCollection services,
        object serviceKey,
        Func<IServiceProvider, string> connectionStringProvider,
        Func<IServiceProvider, SqlServerVectorStoreOptions>? optionsProvider = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNull(services);
        Verify.NotNull(serviceKey);
        Verify.NotNull(connectionStringProvider);

        services.Add(new ServiceDescriptor(typeof(SqlServerVectorStore), serviceKey, (sp, _) =>
        {
            var connectionString = connectionStringProvider(sp);
            var options = optionsProvider?.Invoke(sp);
            return new SqlServerVectorStore(connectionString, options);
        }, lifetime));

        services.TryAdd(new ServiceDescriptor(typeof(IVectorStore), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<SqlServerVectorStore>(key), lifetime));

        return services;
    }

    /// <summary>
    /// Registers a <see cref="SqlServerVectorStoreRecordCollection{TKey, TRecord}"/> as <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>, with the specified connection string and service lifetime.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="connectionStringProvider">The connection string provider.</param>
    /// <param name="optionsProvider">Options provider to further configure the collection.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddSqlServerVectorStoreCollection<TKey, TRecord>(this IServiceCollection services,
        string collectionName,
        Func<IServiceProvider, string> connectionStringProvider,
        Func<IServiceProvider, SqlServerVectorStoreRecordCollectionOptions<TRecord>>? optionsProvider = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : notnull
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(collectionName);
        Verify.NotNull(connectionStringProvider);

        services.Add(new ServiceDescriptor(typeof(SqlServerVectorStoreRecordCollection<TKey, TRecord>), sp =>
        {
            var connectionString = connectionStringProvider(sp);
            var options = optionsProvider?.Invoke(sp);
            return new SqlServerVectorStoreRecordCollection<TKey, TRecord>(connectionString, collectionName, options);
        }, lifetime));

        services.TryAdd(new ServiceDescriptor(typeof(IVectorStoreRecordCollection<TKey, TRecord>),
            static sp => sp.GetRequiredService<SqlServerVectorStoreRecordCollection<TKey, TRecord>>(), lifetime));

        return services;
    }

    /// <summary>
    /// Registers a keyed <see cref="SqlServerVectorStoreRecordCollection{TKey, TRecord}"/> as <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>, with the specified connection string and service lifetime.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the collection.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="connectionStringProvider">The connection string provider.</param>
    /// <param name="optionsProvider">Options provider to further configure the collection.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddKeyedSqlServerVectorStoreCollection<TKey, TRecord>(this IServiceCollection services,
        object serviceKey,
        string collectionName,
        Func<IServiceProvider, string> connectionStringProvider,
        Func<IServiceProvider, SqlServerVectorStoreRecordCollectionOptions<TRecord>>? optionsProvider = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : notnull
    {
        Verify.NotNull(services);
        Verify.NotNull(serviceKey);
        Verify.NotNullOrWhiteSpace(collectionName);
        Verify.NotNull(connectionStringProvider);

        services.Add(new ServiceDescriptor(typeof(SqlServerVectorStoreRecordCollection<TKey, TRecord>), serviceKey, (sp, _) =>
        {
            var connectionString = connectionStringProvider(sp);
            var options = optionsProvider?.Invoke(sp);
            return new SqlServerVectorStoreRecordCollection<TKey, TRecord>(connectionString, collectionName, options);
        }, lifetime));

        services.TryAdd(new ServiceDescriptor(typeof(IVectorStoreRecordCollection<TKey, TRecord>), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<SqlServerVectorStoreRecordCollection<TKey, TRecord>>(key), lifetime));

        return services;
    }

    /// <summary>
    /// Registers a <see cref="SqlServerVectorStoreRecordCollection{TKey, TRecord}"/> as <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>, with the specified connection string and service lifetime.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="connectionString">The connection string.</param>
    /// <param name="options">Options to further configure the collection.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddSqlServerVectorStoreCollection<TKey, TRecord>(this IServiceCollection services,
        string collectionName,
        string connectionString,
        SqlServerVectorStoreRecordCollectionOptions<TRecord>? options = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : notnull
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(collectionName);
        Verify.NotNullOrWhiteSpace(connectionString);

        services.Add(new ServiceDescriptor(typeof(SqlServerVectorStoreRecordCollection<TKey, TRecord>),
            sp => new SqlServerVectorStoreRecordCollection<TKey, TRecord>(connectionString, collectionName, options), lifetime));

        services.TryAdd(new ServiceDescriptor(typeof(IVectorStoreRecordCollection<TKey, TRecord>),
            static sp => sp.GetRequiredService<SqlServerVectorStoreRecordCollection<TKey, TRecord>>(), lifetime));

        return services;
    }

    /// <summary>
    /// Registers a keyed <see cref="SqlServerVectorStoreRecordCollection{TKey, TRecord}"/> as <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>, with the specified connection string and service lifetime.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the collection.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="connectionString">The connection string.</param>
    /// <param name="options">Options to further configure the collection.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddKeyedSqlServerVectorStoreCollection<TKey, TRecord>(this IServiceCollection services,
        object serviceKey,
        string collectionName,
        string connectionString,
        SqlServerVectorStoreRecordCollectionOptions<TRecord>? options = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : notnull
    {
        Verify.NotNull(services);
        Verify.NotNull(serviceKey);
        Verify.NotNullOrWhiteSpace(collectionName);
        Verify.NotNullOrWhiteSpace(connectionString);

        services.Add(new ServiceDescriptor(typeof(SqlServerVectorStoreRecordCollection<TKey, TRecord>), serviceKey,
            (sp, _) => new SqlServerVectorStoreRecordCollection<TKey, TRecord>(connectionString, collectionName, options), lifetime));

        services.TryAdd(new ServiceDescriptor(typeof(IVectorStoreRecordCollection<TKey, TRecord>), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<SqlServerVectorStoreRecordCollection<TKey, TRecord>>(key), lifetime));

        return services;
    }
}
