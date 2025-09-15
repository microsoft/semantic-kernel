// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
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
    /// <inheritdoc cref="AddKeyedSqlServerVectorStore"/>
    [RequiresUnreferencedCode("The SQL Server provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The SQL Server provider is currently incompatible with NativeAOT.")]
    public static IServiceCollection AddSqlServerVectorStore(
        this IServiceCollection services,
        Func<IServiceProvider, string> connectionStringProvider,
        Func<IServiceProvider, SqlServerVectorStoreOptions>? optionsProvider = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        => AddKeyedSqlServerVectorStore(services, serviceKey: null, connectionStringProvider, optionsProvider, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="SqlServerVectorStore"/> as <see cref="VectorStore"/>, with the specified connection string and service lifetime.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStore"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="connectionStringProvider">The connection string provider.</param>
    /// <param name="optionsProvider">Options provider to further configure the vector store.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    [RequiresUnreferencedCode("The SQL Server provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The SQL Server provider is currently incompatible with NativeAOT.")]
    public static IServiceCollection AddKeyedSqlServerVectorStore(
        this IServiceCollection services,
        object? serviceKey,
        Func<IServiceProvider, string> connectionStringProvider,
        Func<IServiceProvider, SqlServerVectorStoreOptions>? optionsProvider = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
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
    /// <inheritdoc cref="AddKeyedSqlServerCollection{TKey, TRecord}(IServiceCollection, object?, string, Func{IServiceProvider, string}, Func{IServiceProvider, SqlServerCollectionOptions}?, ServiceLifetime)"/>
    [RequiresUnreferencedCode("The SQL Server provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The SQL Server provider is currently incompatible with NativeAOT.")]
    public static IServiceCollection AddSqlServerCollection<TKey, TRecord>(
        this IServiceCollection services,
        string name,
        Func<IServiceProvider, string> connectionStringProvider,
        Func<IServiceProvider, SqlServerCollectionOptions>? optionsProvider = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : class
        => AddKeyedSqlServerCollection<TKey, TRecord>(services, serviceKey: null, name, connectionStringProvider, optionsProvider, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="SqlServerCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>, with the specified connection string and service lifetime.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStoreCollection{TKey, TRecord}"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the collection.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="connectionStringProvider">The connection string provider.</param>
    /// <param name="optionsProvider">Options provider to further configure the collection.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    [RequiresUnreferencedCode("The SQL Server provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The SQL Server provider is currently incompatible with NativeAOT.")]
    public static IServiceCollection AddKeyedSqlServerCollection<TKey, TRecord>(
        this IServiceCollection services,
        object? serviceKey,
        string name,
        Func<IServiceProvider, string> connectionStringProvider,
        Func<IServiceProvider, SqlServerCollectionOptions>? optionsProvider = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : class
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(name);
        Verify.NotNull(connectionStringProvider);

        services.Add(new ServiceDescriptor(typeof(SqlServerCollection<TKey, TRecord>), serviceKey, (sp, _) =>
        {
            var connectionString = connectionStringProvider(sp);
            var options = GetCollectionOptions(sp, optionsProvider);
            return new SqlServerCollection<TKey, TRecord>(connectionString, name, options);
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
    /// <inheritdoc cref="AddKeyedSqlServerCollection{TKey, TRecord}(IServiceCollection, object?, string, string, SqlServerCollectionOptions?, ServiceLifetime)"/>/>
    [RequiresUnreferencedCode("The SQL Server provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The SQL Server provider is currently incompatible with NativeAOT.")]
    public static IServiceCollection AddSqlServerCollection<TKey, TRecord>(
        this IServiceCollection services,
        string name,
        string connectionString,
        SqlServerCollectionOptions? options = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : class
        => AddKeyedSqlServerCollection<TKey, TRecord>(services, serviceKey: null, name, connectionString, options, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="SqlServerCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>, with the specified connection string and service lifetime.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStoreCollection{TKey, TRecord}"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the collection.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="connectionString">The connection string.</param>
    /// <param name="options">Options to further configure the collection.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    [RequiresUnreferencedCode("The SQL Server provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The SQL Server provider is currently incompatible with NativeAOT.")]
    public static IServiceCollection AddKeyedSqlServerCollection<TKey, TRecord>(
        this IServiceCollection services,
        object? serviceKey,
        string name,
        string connectionString,
        SqlServerCollectionOptions? options = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : class
    {
        Verify.NotNullOrWhiteSpace(connectionString);

        return AddKeyedSqlServerCollection<TKey, TRecord>(services, serviceKey, name, _ => connectionString, _ => options!, lifetime);
    }

    private static SqlServerVectorStoreOptions? GetStoreOptions(IServiceProvider sp, Func<IServiceProvider, SqlServerVectorStoreOptions?>? optionsProvider)
    {
        var options = optionsProvider?.Invoke(sp);
        if (options?.EmbeddingGenerator is not null)
        {
            return options; // The user has provided everything, there is nothing to change.
        }

        var embeddingGenerator = sp.GetService<IEmbeddingGenerator>();
        return embeddingGenerator is null
            ? options // There is nothing to change.
            : new(options) { EmbeddingGenerator = embeddingGenerator }; // Create a brand new copy in order to avoid modifying the original options.
    }

    private static SqlServerCollectionOptions? GetCollectionOptions(IServiceProvider sp, Func<IServiceProvider, SqlServerCollectionOptions?>? optionsProvider)
    {
        var options = optionsProvider?.Invoke(sp);
        if (options?.EmbeddingGenerator is not null)
        {
            return options; // The user has provided everything, there is nothing to change.
        }

        var embeddingGenerator = sp.GetService<IEmbeddingGenerator>();
        return embeddingGenerator is null
            ? options // There is nothing to change.
            : new(options) { EmbeddingGenerator = embeddingGenerator }; // Create a brand new copy in order to avoid modifying the original options.
    }
}
