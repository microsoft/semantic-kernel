// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.CosmosNoSql;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.Extensions.DependencyInjection;

/// <summary>
/// Extension methods to register Azure CosmosDB NoSQL <see cref="CosmosNoSqlVectorStore"/> instances on an <see cref="IServiceCollection"/>.
/// </summary>
public static class CosmosNoSqlServiceCollectionExtensions
{
    private const string DynamicCodeMessage = "The Cosmos NoSQL provider is currently incompatible with trimming.";
    private const string UnreferencedCodeMessage = "The Cosmos NoSQL provider is currently incompatible with NativeAOT.";

    /// <summary>
    /// Registers a <see cref="CosmosNoSqlVectorStore"/> as <see cref="VectorStore"/>
    /// with <see cref="Database"/> retrieved from the dependency injection container.
    /// </summary>
    /// <inheritdoc cref="AddKeyedCosmosNoSqlVectorStore(IServiceCollection, object?, CosmosNoSqlVectorStoreOptions?, ServiceLifetime)"/>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddCosmosNoSqlVectorStore(
        this IServiceCollection services,
        CosmosNoSqlVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        => AddKeyedCosmosNoSqlVectorStore(services, serviceKey: null, options, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="CosmosNoSqlVectorStore"/> as <see cref="VectorStore"/>
    /// with <see cref="Database"/> retrieved from the dependency injection container.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="CosmosNoSqlVectorStore"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="options">Optional options to further configure the <see cref="CosmosNoSqlVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddKeyedCosmosNoSqlVectorStore(
        this IServiceCollection services,
        object? serviceKey,
        CosmosNoSqlVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNull(services);

        services.Add(new ServiceDescriptor(typeof(CosmosNoSqlVectorStore), serviceKey, (sp, _) =>
        {
            var database = sp.GetRequiredService<Database>();
            options = GetStoreOptions(sp, _ => options);

            return new CosmosNoSqlVectorStore(database, options);
        }, lifetime));

        services.Add(new ServiceDescriptor(typeof(VectorStore), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<CosmosNoSqlVectorStore>(key), lifetime));

        return services;
    }

    /// <summary>
    /// Registers a <see cref="CosmosNoSqlVectorStore"/> as <see cref="VectorStore"/>
    /// using the provided <paramref name="connectionString"/> and <paramref name="databaseName"/>.
    /// </summary>
    /// <inheritdoc cref="AddKeyedCosmosNoSqlVectorStore(IServiceCollection, object?, string, string, CosmosNoSqlVectorStoreOptions?, ServiceLifetime)"/>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddCosmosNoSqlVectorStore(
        this IServiceCollection services,
        string connectionString,
        string databaseName,
        CosmosNoSqlVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        => AddKeyedCosmosNoSqlVectorStore(services, serviceKey: null, connectionString, databaseName, options, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="CosmosNoSqlVectorStore"/> as <see cref="VectorStore"/>
    /// using the provided <paramref name="connectionString"/> and <paramref name="databaseName"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="CosmosNoSqlVectorStore"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="connectionString">Connection string required to connect to Azure CosmosDB NoSQL.</param>
    /// <param name="databaseName">Database name for Azure CosmosDB NoSQL.</param>
    /// <param name="options">Optional options to further configure the <see cref="CosmosNoSqlVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddKeyedCosmosNoSqlVectorStore(
        this IServiceCollection services,
        object? serviceKey,
        string connectionString,
        string databaseName,
        CosmosNoSqlVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(connectionString);
        Verify.NotNullOrWhiteSpace(databaseName);

        services.Add(new ServiceDescriptor(typeof(CosmosNoSqlVectorStore), serviceKey, (sp, _) =>
        {
            options = GetStoreOptions(sp, _ => options);
            var clientOptions = CreateClientOptions(options?.JsonSerializerOptions);

            return new CosmosNoSqlVectorStore(connectionString, databaseName, clientOptions, options);
        }, lifetime));

        services.Add(new ServiceDescriptor(typeof(VectorStore), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<CosmosNoSqlVectorStore>(key), lifetime));

        return services;
    }

    /// <summary>
    /// Registers a <see cref="CosmosNoSqlCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>
    /// with <see cref="Database"/> retrieved from the dependency injection container.
    /// </summary>
    /// <inheritdoc cref="AddKeyedCosmosNoSqlVectorStore(IServiceCollection, object?, CosmosNoSqlVectorStoreOptions?, ServiceLifetime)"/>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddCosmosNoSqlCollection<TRecord>(
        this IServiceCollection services,
        string name,
        CosmosNoSqlCollectionOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
        => AddKeyedCosmosNoSqlCollection<TRecord>(services, serviceKey: null, name, options, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="CosmosNoSqlCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>
    /// with <see cref="Database"/> retrieved from the dependency injection container.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="CosmosNoSqlCollection{TKey, TRecord}"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the collection.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="options">Optional options to further configure the <see cref="CosmosNoSqlCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddKeyedCosmosNoSqlCollection<TRecord>(
        this IServiceCollection services,
        object? serviceKey,
        string name,
        CosmosNoSqlCollectionOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(name);

        services.Add(new ServiceDescriptor(typeof(CosmosNoSqlCollection<string, TRecord>), serviceKey, (sp, _) =>
        {
            var database = sp.GetRequiredService<Database>();
            options = GetCollectionOptions(sp, _ => options);

            return new CosmosNoSqlCollection<string, TRecord>(database, name, options);
        }, lifetime));

        AddAbstractions<string, TRecord>(services, serviceKey, lifetime);

        return services;
    }

    /// <summary>
    /// Registers a <see cref="CosmosNoSqlCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey,TRecord}"/>
    /// using the provided <paramref name="connectionString"/> and <paramref name="databaseName"/>.
    /// </summary>
    /// <inheritdoc cref="AddKeyedCosmosNoSqlCollection{TRecord}(IServiceCollection, object?, string, string, string, CosmosNoSqlCollectionOptions?, ServiceLifetime)"/>
    [RequiresUnreferencedCode(UnreferencedCodeMessage)]
    [RequiresDynamicCode(DynamicCodeMessage)]
    public static IServiceCollection AddCosmosNoSqlCollection<TRecord>(
        this IServiceCollection services,
        string name,
        string connectionString,
        string databaseName,
        CosmosNoSqlCollectionOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
        => AddKeyedCosmosNoSqlCollection<TRecord>(services, serviceKey: null, name, connectionString, databaseName, options, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="CosmosNoSqlCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey,TRecord}"/>
    /// using the provided <paramref name="connectionString"/> and <paramref name="databaseName"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="CosmosNoSqlCollection{TKey, TRecord}"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the collection.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="connectionString">Connection string required to connect to Azure CosmosDB NoSQL.</param>
    /// <param name="databaseName">Database name for Azure CosmosDB NoSQL.</param>
    /// <param name="options">Optional options to further configure the <see cref="CosmosNoSqlCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(UnreferencedCodeMessage)]
    [RequiresDynamicCode(DynamicCodeMessage)]
    public static IServiceCollection AddKeyedCosmosNoSqlCollection<TRecord>(
        this IServiceCollection services,
        object? serviceKey,
        string name,
        string connectionString,
        string databaseName,
        CosmosNoSqlCollectionOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
    {
        Verify.NotNullOrWhiteSpace(connectionString);
        Verify.NotNullOrWhiteSpace(databaseName);

        return AddKeyedCosmosNoSqlCollection<TRecord>(services, serviceKey, name, _ => connectionString, _ => databaseName, _ => options!, lifetime);
    }

    /// <summary>
    /// Registers a <see cref="CosmosNoSqlCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey,TRecord}"/>
    /// using the provided <paramref name="connectionStringProvider"/> and <paramref name="databaseNameProvider"/>.
    /// </summary>
    /// <inheritdoc cref="AddKeyedCosmosNoSqlCollection{TRecord}(IServiceCollection, object?, string, Func{IServiceProvider, string}, Func{IServiceProvider, string}, Func{IServiceProvider, CosmosNoSqlCollectionOptions}?, ServiceLifetime)"/>
    [RequiresUnreferencedCode(UnreferencedCodeMessage)]
    [RequiresDynamicCode(DynamicCodeMessage)]
    public static IServiceCollection AddCosmosNoSqlCollection<TRecord>(
        this IServiceCollection services,
        string name,
        Func<IServiceProvider, string> connectionStringProvider,
        Func<IServiceProvider, string> databaseNameProvider,
        Func<IServiceProvider, CosmosNoSqlCollectionOptions>? optionsProvider = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
        => AddKeyedCosmosNoSqlCollection<TRecord>(services, serviceKey: null, name, connectionStringProvider, databaseNameProvider, optionsProvider, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="CosmosNoSqlCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey,TRecord}"/>
    /// using the provided <paramref name="connectionStringProvider"/> and <paramref name="databaseNameProvider"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStoreCollection{TKey, TRecord}"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the collection.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="connectionStringProvider">The connection string provider.</param>
    /// <param name="databaseNameProvider">The database name provider.</param>
    /// <param name="optionsProvider">Options provider to further configure the collection.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(UnreferencedCodeMessage)]
    [RequiresDynamicCode(DynamicCodeMessage)]
    public static IServiceCollection AddKeyedCosmosNoSqlCollection<TRecord>(
        this IServiceCollection services,
        object? serviceKey,
        string name,
        Func<IServiceProvider, string> connectionStringProvider,
        Func<IServiceProvider, string> databaseNameProvider,
        Func<IServiceProvider, CosmosNoSqlCollectionOptions>? optionsProvider = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(name);
        Verify.NotNull(connectionStringProvider);
        Verify.NotNull(databaseNameProvider);

        services.Add(new ServiceDescriptor(typeof(CosmosNoSqlCollection<string, TRecord>), serviceKey, (sp, _) =>
        {
            var options = GetCollectionOptions(sp, optionsProvider);
            var clientOptions = CreateClientOptions(options?.JsonSerializerOptions);

            return new CosmosNoSqlCollection<string, TRecord>(
                connectionString: connectionStringProvider(sp),
                databaseName: databaseNameProvider(sp),
                name: name,
                clientOptions,
                options);
        }, lifetime));

        AddAbstractions<string, TRecord>(services, serviceKey, lifetime);

        return services;
    }

    private static void AddAbstractions<TKey, TRecord>(IServiceCollection services, object? serviceKey, ServiceLifetime lifetime)
        where TKey : notnull
        where TRecord : class
    {
        services.Add(new ServiceDescriptor(typeof(VectorStoreCollection<TKey, TRecord>), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<CosmosNoSqlCollection<TKey, TRecord>>(key), lifetime));

        services.Add(new ServiceDescriptor(typeof(IVectorSearchable<TRecord>), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<CosmosNoSqlCollection<TKey, TRecord>>(key), lifetime));

        services.Add(new ServiceDescriptor(typeof(IKeywordHybridSearchable<TRecord>), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<CosmosNoSqlCollection<TKey, TRecord>>(key), lifetime));
    }

    private static CosmosNoSqlVectorStoreOptions? GetStoreOptions(IServiceProvider sp, Func<IServiceProvider, CosmosNoSqlVectorStoreOptions?>? optionsProvider)
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

    private static CosmosNoSqlCollectionOptions? GetCollectionOptions(IServiceProvider sp, Func<IServiceProvider, CosmosNoSqlCollectionOptions?>? optionsProvider)
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

    private static CosmosClientOptions CreateClientOptions(JsonSerializerOptions? jsonSerializerOptions) => new()
    {
        ApplicationName = HttpHeaderConstant.Values.UserAgent,
        UseSystemTextJsonSerializerWithOptions = jsonSerializerOptions ?? JsonSerializerOptions.Default,
    };
}
