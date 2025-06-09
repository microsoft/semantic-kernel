// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.PgVector;
using Npgsql;

namespace Microsoft.Extensions.DependencyInjection;

/// <summary>
/// Extension methods to register Postgres <see cref="VectorStore"/> instances on an <see cref="IServiceCollection"/>.
/// </summary>
public static class PostgresServiceCollectionExtensions
{
    private const string DynamicCodeMessage = "This method is incompatible with NativeAOT, consult the documentation for adding collections in a way that's compatible with NativeAOT.";
    private const string UnreferencedCodeMessage = "This method is incompatible with trimming, consult the documentation for adding collections in a way that's compatible with NativeAOT.";

    /// <summary>
    /// Register a <see cref="PostgresVectorStore"/> as <see cref="VectorStore"/>, where the <see cref="NpgsqlDataSource"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="PostgresVectorStore"/> on.</param>
    /// <param name="options">Optional options to further configure the <see cref="VectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddPostgresVectorStore(
        this IServiceCollection services,
        PostgresVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNull(services);

        services.Add(new ServiceDescriptor(typeof(PostgresVectorStore), (sp) =>
        {
            var dataSource = sp.GetRequiredService<NpgsqlDataSource>();
            options = GetStoreOptions(sp, _ => options);

            // The data source has been solved from the DI container, so we do not own it.
            return new PostgresVectorStore(dataSource, ownsDataSource: false, options);
        }, lifetime));

        services.Add(new ServiceDescriptor(typeof(VectorStore),
            static (sp) => sp.GetRequiredService<PostgresVectorStore>(), lifetime));

        return services;
    }

    /// <summary>
    /// Registers a <see cref="PostgresVectorStore"/> as <see cref="VectorStore"/>, with the specified connection string and service lifetime.
    /// </summary>
    /// <inheritdoc cref="AddKeyedPostgresVectorStore(IServiceCollection, object, string, PostgresVectorStoreOptions?, ServiceLifetime)"/>
    public static IServiceCollection AddPostgresVectorStore(
        this IServiceCollection services,
        string connectionString,
        PostgresVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNullOrWhiteSpace(connectionString);

        return AddVectorStore(services, serviceKey: null, sp => connectionString, sp => options, lifetime);
    }

    /// <summary>
    /// Registers a keyed <see cref="PostgresVectorStore"/> as <see cref="VectorStore"/>, with the specified connection string and service lifetime.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="PostgresVectorStore"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="connectionString">Postgres database connection string.</param>
    /// <param name="options">Optional options to further configure the <see cref="PostgresVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddKeyedPostgresVectorStore(
        this IServiceCollection services,
        object? serviceKey,
        string connectionString,
        PostgresVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNullOrWhiteSpace(connectionString);

        return AddVectorStore(services, serviceKey, sp => connectionString, sp => options, lifetime);
    }

    /// <summary>
    /// Registers a <see cref="PostgresVectorStore"/> as <see cref="VectorStore"/>, with the specified connection string and service lifetime.
    /// </summary>
    /// <inheritdoc cref="AddVectorStore(IServiceCollection, object?, Func{IServiceProvider, string}, Func{IServiceProvider, PostgresVectorStoreOptions?}?, ServiceLifetime)"/>
    public static IServiceCollection AddPostgresVectorStore(
        this IServiceCollection services,
        Func<IServiceProvider, string> connectionStringProvider,
        Func<IServiceProvider, PostgresVectorStoreOptions?>? optionsProvider = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        => AddVectorStore(services, serviceKey: null, connectionStringProvider, optionsProvider, lifetime);

    /// <inheritdoc cref="AddVectorStore(IServiceCollection, object?, Func{IServiceProvider, string}, Func{IServiceProvider, PostgresVectorStoreOptions?}?, ServiceLifetime)"/>
    public static IServiceCollection AddKeyedPostgresVectorStore(
        this IServiceCollection services,
        object? serviceKey,
        Func<IServiceProvider, string> connectionStringProvider,
        Func<IServiceProvider, PostgresVectorStoreOptions?>? optionsProvider = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        => AddVectorStore(services, serviceKey, connectionStringProvider, optionsProvider, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="PostgresVectorStore"/> as <see cref="VectorStore"/>, with the specified connection string and service lifetime.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="PostgresVectorStore"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the store.</param>
    /// <param name="connectionStringProvider">The connection string provider.</param>
    /// <param name="optionsProvider">Options provider to further configure the <see cref="PostgresVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    private static IServiceCollection AddVectorStore(
        IServiceCollection services,
        object? serviceKey,
        Func<IServiceProvider, string> connectionStringProvider,
        Func<IServiceProvider, PostgresVectorStoreOptions?>? optionsProvider,
        ServiceLifetime lifetime)
    {
        Verify.NotNull(services);
        Verify.NotNull(connectionStringProvider);

        services.Add(new ServiceDescriptor(typeof(PostgresVectorStore), serviceKey, (sp, _) =>
        {
            var connectionString = connectionStringProvider(sp);
            var options = GetStoreOptions(sp, optionsProvider);

            return new PostgresVectorStore(connectionString, options);
        }, lifetime));

        services.Add(new ServiceDescriptor(typeof(VectorStore), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<PostgresVectorStore>(key), lifetime));

        return services;
    }

    /// <summary>
    /// Register a <see cref="PostgresCollection{TKey, TRecord}"/> where the <see cref="NpgsqlDataSource"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStoreCollection{TKey, TRecord}"/> on.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="options">Optional options to further configure the <see cref="VectorStoreCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. It needs to match <see cref="NpgsqlDataSource"/> lifetime. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresDynamicCode(DynamicCodeMessage)]
    [RequiresUnreferencedCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddPostgresCollection<TKey, TRecord>(
        this IServiceCollection services,
        string name,
        PostgresCollectionOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : class
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(name);

        services.Add(new ServiceDescriptor(typeof(PostgresCollection<TKey, TRecord>), (sp) =>
        {
            var dataSource = sp.GetRequiredService<NpgsqlDataSource>();
            var copy = GetCollectionOptions(sp, _ => options);

            // The data source has been solved from the DI container, so we do not own it.
            return new PostgresCollection<TKey, TRecord>(dataSource, name, ownsDataSource: false, copy);
        }, lifetime));

        AddAbstractions<TKey, TRecord>(services, serviceKey: null, lifetime);

        return services;
    }

    /// <summary>
    /// Registers a <see cref="PostgresCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>, with the specified connection string and service lifetime.
    /// </summary>
    /// <inheritdoc cref="AddKeyedPostgresCollection{TKey, TRecord}(IServiceCollection, object, string, string, PostgresCollectionOptions?, ServiceLifetime)"/>
    [RequiresDynamicCode(DynamicCodeMessage)]
    [RequiresUnreferencedCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddPostgresCollection<TKey, TRecord>(
        this IServiceCollection services,
        string name,
        string connectionString,
        PostgresCollectionOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : class
    {
        Verify.NotNullOrWhiteSpace(connectionString);

        return AddKeyedPostgresCollection<TKey, TRecord>(services, serviceKey: null, name, sp => connectionString, sp => options, lifetime);
    }

    /// <summary>
    /// Registers a keyed <see cref="PostgresCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>, with the specified connection string and service lifetime.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStoreCollection{TKey, TRecord}"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the collection.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="connectionString">Postgres database connection string.</param>
    /// <param name="options">Optional options to further configure the <see cref="VectorStoreCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresDynamicCode(DynamicCodeMessage)]
    [RequiresUnreferencedCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddKeyedPostgresCollection<TKey, TRecord>(
        this IServiceCollection services,
        object? serviceKey,
        string name,
        string connectionString,
        PostgresCollectionOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : class
    {
        Verify.NotNullOrWhiteSpace(connectionString);

        return AddKeyedPostgresCollection<TKey, TRecord>(services, serviceKey, name, sp => connectionString, sp => options, lifetime);
    }

    /// <summary>
    /// Registers a <see cref="PostgresCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>, with the specified connection string and service lifetime.
    /// </summary>
    /// <inheritdoc cref="AddKeyedPostgresCollection{TKey, TRecord}(IServiceCollection, object?, string, Func{IServiceProvider, string}, Func{IServiceProvider, PostgresCollectionOptions?}?, ServiceLifetime)"/>
    [RequiresDynamicCode(DynamicCodeMessage)]
    [RequiresUnreferencedCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddPostgresCollection<TKey, TRecord>(
        this IServiceCollection services,
        string name,
        Func<IServiceProvider, string> connectionStringProvider,
        Func<IServiceProvider, PostgresCollectionOptions?>? optionsProvider = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : class
        => AddKeyedPostgresCollection<TKey, TRecord>(services, serviceKey: null, name, connectionStringProvider, optionsProvider, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="PostgresCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>, with the specified connection string and service lifetime.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStoreCollection{TKey, TRecord}"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the collection.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="connectionStringProvider">The connection string provider.</param>
    /// <param name="optionsProvider">Options provider to further configure the collection.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    [RequiresDynamicCode(DynamicCodeMessage)]
    [RequiresUnreferencedCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddKeyedPostgresCollection<TKey, TRecord>(
        this IServiceCollection services,
        object? serviceKey,
        string name,
        Func<IServiceProvider, string> connectionStringProvider,
        Func<IServiceProvider, PostgresCollectionOptions?>? optionsProvider = null,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TKey : notnull
        where TRecord : class
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(name);
        Verify.NotNull(connectionStringProvider);

        services.Add(new ServiceDescriptor(typeof(PostgresCollection<TKey, TRecord>), serviceKey, (sp, _) =>
        {
            var connectionString = connectionStringProvider(sp);
            var options = GetCollectionOptions(sp, optionsProvider);
            return new PostgresCollection<TKey, TRecord>(connectionString, name, options);
        }, lifetime));

        AddAbstractions<TKey, TRecord>(services, serviceKey, lifetime);

        return services;
    }

    private static void AddAbstractions<TKey, TRecord>(IServiceCollection services, object? serviceKey, ServiceLifetime lifetime)
        where TKey : notnull
        where TRecord : class
    {
        services.Add(new ServiceDescriptor(typeof(VectorStoreCollection<TKey, TRecord>), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<PostgresCollection<TKey, TRecord>>(key), lifetime));

        services.Add(new ServiceDescriptor(typeof(IVectorSearchable<TRecord>), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<PostgresCollection<TKey, TRecord>>(key), lifetime));

        // Once HybridSearch supports get implemented by PostgresCollection,
        // we need to add IKeywordHybridSearchable abstraction here as well.
    }

    private static PostgresVectorStoreOptions? GetStoreOptions(IServiceProvider sp, Func<IServiceProvider, PostgresVectorStoreOptions?>? optionsProvider)
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

    private static PostgresCollectionOptions? GetCollectionOptions(IServiceProvider sp, Func<IServiceProvider, PostgresCollectionOptions?>? optionsProvider)
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
