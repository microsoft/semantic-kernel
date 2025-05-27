// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.CosmosMongoDB;
using Microsoft.SemanticKernel.Http;
using MongoDB.Driver;

namespace Microsoft.Extensions.DependencyInjection;

/// <summary>
/// Extension methods to register Azure CosmosDB MongoDB <see cref="VectorStore"/> instances on an <see cref="IServiceCollection"/>.
/// </summary>
public static class CosmosMongoServiceCollectionExtensions
{
    private const string DynamicCodeMessage = "This method is incompatible with NativeAOT, consult the documentation for adding collections in a way that's compatible with NativeAOT.";
    private const string UnreferencedCodeMessage = "This method is incompatible with trimming, consult the documentation for adding collections in a way that's compatible with NativeAOT.";

    /// <summary>
    /// Registers a <see cref="CosmosMongoVectorStore"/> as <see cref="VectorStore"/>
    /// with <see cref="IMongoDatabase"/> retrieved from the dependency injection container.
    /// </summary>
    /// <inheritdoc cref="AddKeyedCosmosMongoVectorStore(IServiceCollection, object?, CosmosMongoVectorStoreOptions?, ServiceLifetime)"/>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddCosmosMongoVectorStore(
        this IServiceCollection services,
        CosmosMongoVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        => AddKeyedCosmosMongoVectorStore(services, serviceKey: null, options, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="CosmosMongoVectorStore"/> as <see cref="VectorStore"/>
    /// with <see cref="IMongoDatabase"/> retrieved from the dependency injection container.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="CosmosMongoVectorStore"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="options">Optional options to further configure the <see cref="CosmosMongoVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddKeyedCosmosMongoVectorStore(
        this IServiceCollection services,
        object? serviceKey,
        CosmosMongoVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNull(services);

        services.Add(new ServiceDescriptor(typeof(CosmosMongoVectorStore), serviceKey, (sp, _) =>
        {
            var database = sp.GetRequiredService<IMongoDatabase>();
            options = GetStoreOptions(sp, _ => options);

            return new CosmosMongoVectorStore(database, options);
        }, lifetime));

        services.Add(new ServiceDescriptor(typeof(VectorStore), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<CosmosMongoVectorStore>(key), lifetime));

        return services;
    }

    /// <summary>
    /// Registers a <see cref="CosmosMongoVectorStore"/> as <see cref="VectorStore"/>
    /// using the provided <paramref name="connectionString"/> and <paramref name="databaseName"/>.
    /// </summary>
    /// <inheritdoc cref="AddKeyedCosmosMongoVectorStore(IServiceCollection, object?, string, string, CosmosMongoVectorStoreOptions?, ServiceLifetime)"/>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddCosmosMongoVectorStore(
        this IServiceCollection services,
        string connectionString,
        string databaseName,
        CosmosMongoVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        => AddKeyedCosmosMongoVectorStore(services, serviceKey: null, connectionString, databaseName, options, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="CosmosMongoVectorStore"/> as <see cref="VectorStore"/>
    /// using the provided <paramref name="connectionString"/> and <paramref name="databaseName"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="CosmosMongoVectorStore"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="connectionString">Connection string required to connect to Azure CosmosDB MongoDB.</param>
    /// <param name="databaseName">Database name for Azure CosmosDB MongoDB.</param>
    /// <param name="options">Optional options to further configure the <see cref="CosmosMongoVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddKeyedCosmosMongoVectorStore(
        this IServiceCollection services,
        object? serviceKey,
        string connectionString,
        string databaseName,
        CosmosMongoVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(connectionString);
        Verify.NotNullOrWhiteSpace(databaseName);

        services.Add(new ServiceDescriptor(typeof(CosmosMongoVectorStore), serviceKey, (sp, _) =>
        {
            options = GetStoreOptions(sp, _ => options);
            MongoClient mongoClient = new(CreateClientSettings(connectionString));
            var database = mongoClient.GetDatabase(databaseName);

            return new CosmosMongoVectorStore(database, options);
        }, lifetime));

        services.Add(new ServiceDescriptor(typeof(VectorStore), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<CosmosMongoVectorStore>(key), lifetime));

        return services;
    }

    /// <summary>
    /// Registers a <see cref="CosmosMongoCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>
    /// with <see cref="IMongoDatabase"/> retrieved from the dependency injection container.
    /// </summary>
    /// <inheritdoc cref="AddKeyedCosmosMongoVectorStore(IServiceCollection, object?, CosmosMongoVectorStoreOptions?, ServiceLifetime)"/>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddCosmosMongoCollection<TRecord>(
        this IServiceCollection services,
        string name,
        CosmosMongoCollectionOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
        => AddKeyedCosmosMongoCollection<TRecord>(services, serviceKey: null, name, options, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="CosmosMongoCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey, TRecord}"/>
    /// with <see cref="IMongoDatabase"/> retrieved from the dependency injection container.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="CosmosMongoCollection{TKey, TRecord}"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the collection.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="options">Optional options to further configure the <see cref="CosmosMongoCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(DynamicCodeMessage)]
    [RequiresDynamicCode(UnreferencedCodeMessage)]
    public static IServiceCollection AddKeyedCosmosMongoCollection<TRecord>(
        this IServiceCollection services,
        object? serviceKey,
        string name,
        CosmosMongoCollectionOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(name);

        services.Add(new ServiceDescriptor(typeof(CosmosMongoCollection<string, TRecord>), serviceKey, (sp, _) =>
        {
            var database = sp.GetRequiredService<IMongoDatabase>();
            options = GetCollectionOptions(sp, _ => options);

            return new CosmosMongoCollection<string, TRecord>(database, name, options);
        }, lifetime));

        AddAbstractions<string, TRecord>(services, serviceKey, lifetime);

        return services;
    }

    /// <summary>
    /// Registers a <see cref="CosmosMongoCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey,TRecord}"/>
    /// using the provided <paramref name="connectionString"/> and <paramref name="databaseName"/>.
    /// </summary>
    /// <inheritdoc cref="AddKeyedCosmosMongoCollection{TRecord}(IServiceCollection, object?, string, string, string, CosmosMongoCollectionOptions?, ServiceLifetime)"/>
    [RequiresUnreferencedCode(UnreferencedCodeMessage)]
    [RequiresDynamicCode(DynamicCodeMessage)]
    public static IServiceCollection AddCosmosMongoCollection<TRecord>(
        this IServiceCollection services,
        string name,
        string connectionString,
        string databaseName,
        CosmosMongoCollectionOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
        => AddKeyedCosmosMongoCollection<TRecord>(services, serviceKey: null, name, connectionString, databaseName, options, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="CosmosMongoCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey,TRecord}"/>
    /// using the provided <paramref name="connectionString"/> and <paramref name="databaseName"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="CosmosMongoCollection{TKey, TRecord}"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the collection.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="connectionString">Connection string required to connect to Azure CosmosDB MongoDB.</param>
    /// <param name="databaseName">Database name for Azure CosmosDB MongoDB.</param>
    /// <param name="options">Optional options to further configure the <see cref="CosmosMongoCollection{TKey, TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>Service collection.</returns>
    [RequiresUnreferencedCode(UnreferencedCodeMessage)]
    [RequiresDynamicCode(DynamicCodeMessage)]
    public static IServiceCollection AddKeyedCosmosMongoCollection<TRecord>(
        this IServiceCollection services,
        object? serviceKey,
        string name,
        string connectionString,
        string databaseName,
        CosmosMongoCollectionOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
    {
        Verify.NotNullOrWhiteSpace(connectionString);
        Verify.NotNullOrWhiteSpace(databaseName);

        return AddKeyedCosmosMongoCollection<TRecord>(services, serviceKey, name, _ => connectionString, _ => databaseName, _ => options!, lifetime);
    }

    /// <summary>
    /// Registers a <see cref="CosmosMongoCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey,TRecord}"/>
    /// using the provided <paramref name="connectionStringProvider"/> and <paramref name="databaseNameProvider"/>.
    /// </summary>
    /// <inheritdoc cref="AddKeyedCosmosMongoCollection{TRecord}(IServiceCollection, object?, string, Func{IServiceProvider, string}, Func{IServiceProvider, string}, Func{IServiceProvider, CosmosMongoCollectionOptions}?, ServiceLifetime)"/>
    [RequiresUnreferencedCode(UnreferencedCodeMessage)]
    [RequiresDynamicCode(DynamicCodeMessage)]
    public static IServiceCollection AddCosmosMongoCollection<TRecord>(
        this IServiceCollection services,
        string name,
        Func<IServiceProvider, string> connectionStringProvider,
        Func<IServiceProvider, string> databaseNameProvider,
        Func<IServiceProvider, CosmosMongoCollectionOptions>? optionsProvider = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
        => AddKeyedCosmosMongoCollection<TRecord>(services, serviceKey: null, name, connectionStringProvider, databaseNameProvider, optionsProvider, lifetime);

    /// <summary>
    /// Registers a keyed <see cref="CosmosMongoCollection{TKey, TRecord}"/> as <see cref="VectorStoreCollection{TKey,TRecord}"/>
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
    public static IServiceCollection AddKeyedCosmosMongoCollection<TRecord>(
        this IServiceCollection services,
        object? serviceKey,
        string name,
        Func<IServiceProvider, string> connectionStringProvider,
        Func<IServiceProvider, string> databaseNameProvider,
        Func<IServiceProvider, CosmosMongoCollectionOptions>? optionsProvider = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        where TRecord : class
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(name);
        Verify.NotNull(connectionStringProvider);
        Verify.NotNull(databaseNameProvider);

        services.Add(new ServiceDescriptor(typeof(CosmosMongoCollection<string, TRecord>), serviceKey, (sp, _) =>
        {
            var options = GetCollectionOptions(sp, optionsProvider);
            MongoClient mongoClient = new(CreateClientSettings(connectionStringProvider(sp)));
            var database = mongoClient.GetDatabase(databaseNameProvider(sp));

            return new CosmosMongoCollection<string, TRecord>(database, name, options);
        }, lifetime));

        AddAbstractions<string, TRecord>(services, serviceKey, lifetime);

        return services;
    }

    private static void AddAbstractions<TKey, TRecord>(IServiceCollection services, object? serviceKey, ServiceLifetime lifetime)
        where TKey : notnull
        where TRecord : class
    {
        services.Add(new ServiceDescriptor(typeof(VectorStoreCollection<TKey, TRecord>), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<CosmosMongoCollection<TKey, TRecord>>(key), lifetime));

        services.Add(new ServiceDescriptor(typeof(IVectorSearchable<TRecord>), serviceKey,
            static (sp, key) => sp.GetRequiredKeyedService<CosmosMongoCollection<TKey, TRecord>>(key), lifetime));

        // Once HybridSearch supports get implemented by CosmosMongoCollection,
        // we need to add IKeywordHybridSearchable abstraction here as well.
    }

    private static CosmosMongoVectorStoreOptions? GetStoreOptions(IServiceProvider sp, Func<IServiceProvider, CosmosMongoVectorStoreOptions?>? optionsProvider)
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

    private static CosmosMongoCollectionOptions? GetCollectionOptions(IServiceProvider sp, Func<IServiceProvider, CosmosMongoCollectionOptions?>? optionsProvider)
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

    private static MongoClientSettings CreateClientSettings(string connectionString)
    {
        var settings = MongoClientSettings.FromConnectionString(connectionString);
        settings.ApplicationName = HttpHeaderConstant.Values.UserAgent;
        return settings;
    }
}
