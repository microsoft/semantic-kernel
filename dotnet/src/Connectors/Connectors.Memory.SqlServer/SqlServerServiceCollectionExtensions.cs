// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.SqlServer;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register <see cref="SqlServerVectorStore"/> instances on an <see cref="IServiceCollection"/>.
/// </summary>
public static class SqlServerServiceCollectionExtensions
{
    /// <summary>
    /// Registers a <see cref="SqlServerVectorStore"/> as <see cref="VectorStore"/>, with the specified connection string and service lifetime.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStore"/> on.</param>
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
        services.TryAdd(new ServiceDescriptor(typeof(VectorStore),
            static sp => sp.GetRequiredService<SqlServerVectorStore>(), lifetime));

        return services;
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

        services.TryAdd(new ServiceDescriptor(typeof(VectorStore), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<SqlServerVectorStore>(key), lifetime));

        return services;
    }

    /// <summary>
    /// Registers a <see cref="SqlServerCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>, with the specified connection string and service lifetime.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStoreCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="connectionStringProvider">The connection string provider.</param>
    /// <param name="optionsProvider">Options provider to further configure the collection.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddSqlServerCollection<TKey, TRecord>(this IServiceCollection services,
        string collectionName,
        Func<IServiceProvider, string> connectionStringProvider,
        Func<IServiceProvider, SqlServerCollectionOptions>? optionsProvider = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : class
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(collectionName);
        Verify.NotNull(connectionStringProvider);

        services.Add(new ServiceDescriptor(typeof(SqlServerCollection<TKey, TRecord>), sp =>
        {
            var connectionString = connectionStringProvider(sp);
            var options = optionsProvider?.Invoke(sp);
            return new SqlServerCollection<TKey, TRecord>(connectionString, collectionName, options);
        }, lifetime));

        RegisterAbstractions<TKey, TRecord>(services, lifetime, serviceKey: null);

        return services;
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
    public static IServiceCollection AddKeyedSqlServerCollection<TKey, TRecord>(this IServiceCollection services,
        object serviceKey,
        string collectionName,
        Func<IServiceProvider, string> connectionStringProvider,
        Func<IServiceProvider, SqlServerCollectionOptions>? optionsProvider = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : class
    {
        Verify.NotNull(services);
        Verify.NotNull(serviceKey);
        Verify.NotNullOrWhiteSpace(collectionName);
        Verify.NotNull(connectionStringProvider);

        services.Add(new ServiceDescriptor(typeof(SqlServerCollection<TKey, TRecord>), serviceKey, (sp, _) =>
        {
            var connectionString = connectionStringProvider(sp);
            var options = optionsProvider?.Invoke(sp);
            return new SqlServerCollection<TKey, TRecord>(connectionString, collectionName, options);
        }, lifetime));

        RegisterAbstractions<TKey, TRecord>(services, lifetime, serviceKey);

        return services;
    }

    /// <summary>
    /// Registers a <see cref="SqlServerCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>, with the specified connection string and service lifetime.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStoreCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="connectionString">The connection string.</param>
    /// <param name="options">Options to further configure the collection.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddSqlServerCollection<TKey, TRecord>(this IServiceCollection services,
        string collectionName,
        string connectionString,
        SqlServerCollectionOptions? options = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : class
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(collectionName);
        Verify.NotNullOrWhiteSpace(connectionString);

        services.Add(new ServiceDescriptor(typeof(SqlServerCollection<TKey, TRecord>),
            sp => new SqlServerCollection<TKey, TRecord>(connectionString, collectionName, options), lifetime));

        RegisterAbstractions<TKey, TRecord>(services, lifetime, serviceKey: null);

        return services;
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
    public static IServiceCollection AddKeyedSqlServerCollection<TKey, TRecord>(this IServiceCollection services,
        object serviceKey,
        string collectionName,
        string connectionString,
        SqlServerCollectionOptions? options = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : class
    {
        Verify.NotNull(services);
        Verify.NotNull(serviceKey);
        Verify.NotNullOrWhiteSpace(collectionName);
        Verify.NotNullOrWhiteSpace(connectionString);

        services.Add(new ServiceDescriptor(typeof(SqlServerCollection<TKey, TRecord>), serviceKey,
            (sp, _) => new SqlServerCollection<TKey, TRecord>(connectionString, collectionName, options), lifetime));

        RegisterAbstractions<TKey, TRecord>(services, lifetime, serviceKey);

        return services;
    }

    private static void RegisterAbstractions<TKey, TRecord>(IServiceCollection services, ServiceLifetime lifetime, object? serviceKey)
        where TKey : notnull
        where TRecord : class
    {
        if (serviceKey is null)
        {
            services.TryAdd(new ServiceDescriptor(typeof(VectorStoreCollection<TKey, TRecord>),
                static sp => sp.GetRequiredService<SqlServerCollection<TKey, TRecord>>(), lifetime));

            services.TryAdd(new ServiceDescriptor(typeof(IVectorSearchable<TRecord>),
                static sp => sp.GetRequiredService<SqlServerCollection<TKey, TRecord>>(), lifetime));
        }
        else
        {
            services.TryAdd(new ServiceDescriptor(typeof(VectorStoreCollection<TKey, TRecord>), serviceKey,
                static (sp, key) => sp.GetRequiredKeyedService<SqlServerCollection<TKey, TRecord>>(key), lifetime));

            services.TryAdd(new ServiceDescriptor(typeof(IVectorSearchable<TRecord>), serviceKey,
                static (sp, key) => sp.GetRequiredKeyedService<SqlServerCollection<TKey, TRecord>>(key), lifetime));
        }
    }
}
