﻿// Copyright (c) Microsoft. All rights reserved.

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
    /// Register a <see cref="IPostgresVectorStoreDbClient"/> with the specified service ID and where NpgsqlDataSource is constructed using the provided parameters.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IPostgresVectorStoreDbClient"/> on.</param>
    /// <param name="connectionString">Postgres database connection string.</param>
    /// <param name="schema">The schema to use.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddPostgresVectorStoreDbClient(this IServiceCollection services, string connectionString, string schema = PostgresConstants.DefaultSchema, string? serviceId = default)
    {
        string? npgsqlServiceId = serviceId == null ? default : $"{serviceId}_NpgsqlDataSource";
        // Register NpgsqlDataSource to ensure proper disposal.
        services.AddKeyedSingleton<NpgsqlDataSource>(
            npgsqlServiceId,
            (sp, obj) =>
            {
                NpgsqlDataSourceBuilder dataSourceBuilder = new(connectionString);
                dataSourceBuilder.UseVector();
                return dataSourceBuilder.Build();
            });

        services.AddKeyedSingleton<IPostgresVectorStoreDbClient>(
            serviceId,
            (sp, obj) =>
            {
                var dataSource = sp.GetRequiredKeyedService<NpgsqlDataSource>(npgsqlServiceId);
                return new PostgresVectorStoreDbClient(dataSource, schema);
            });

        return services;
    }

    /// <summary>
    /// Register a <see cref="IPostgresVectorStoreDbClient"/> with the specified service ID and where NpgsqlDataSource is passed in as parameter.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IPostgresVectorStoreDbClient"/> on.</param>
    /// <param name="dataSource">The data source to use.</param>
    /// <param name="schema">The schema to use.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddPostgresVectorStoreDbClient(this IServiceCollection services, NpgsqlDataSource dataSource, string schema = PostgresConstants.DefaultSchema, string? serviceId = default)
    {
        // Since we are not constructing the data source, add the IVectorStore as transient, since we
        // cannot make assumptions about how client is being managed.
        services.AddKeyedTransient<IPostgresVectorStoreDbClient>(
            serviceId,
            (sp, obj) =>
            {
                return new PostgresVectorStoreDbClient(dataSource, schema);
            });

        return services;
    }

    /// <summary>
    /// Register a <see cref="IPostgresVectorStoreDbClient"/> with the specified service ID and where the NpgsqlDataSource is retrieved from the dependency injection container.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IPostgresVectorStoreDbClient"/> on.</param>
    /// <param name="schema">The schema to use.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddPostgresVectorStoreDbClient(this IServiceCollection services, string schema = PostgresConstants.DefaultSchema, string? serviceId = default)
    {
        // Since we are not constructing the client, add the IVectorStore as transient, since we
        // cannot make assumptions about how client is being managed.
        services.AddKeyedTransient<IPostgresVectorStoreDbClient>(
            serviceId,
            (sp, obj) =>
            {
                var dataSource = sp.GetRequiredService<NpgsqlDataSource>();
                return new PostgresVectorStoreDbClient(dataSource, schema);
            });

        return services;
    }

    /// <summary>
    /// Register a Postgres <see cref="IVectorStore"/> with the specified service ID and where <see cref="IPostgresVectorStoreDbClient"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddPostgresVectorStore(this IServiceCollection services, PostgresVectorStoreOptions? options = default, string? serviceId = default)
    {
        // Since we are not constructing the client, add the IVectorStore as transient, since we
        // cannot make assumptions about how client is being managed.
        services.AddKeyedTransient<IVectorStore>(
            serviceId,
            (sp, obj) =>
            {
                var client = sp.GetRequiredService<IPostgresVectorStoreDbClient>();
                var selectedOptions = options ?? sp.GetService<PostgresVectorStoreOptions>();

                return new PostgresVectorStore(
                    client,
                    selectedOptions);
            });

        return services;
    }

    /// <summary>
    /// Register a Postgres <see cref="IVectorStore"/> with the specified service ID and where <see cref="IPostgresVectorStoreDbClient"/> is constructed using the provided parameters.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="connectionString">Postgres database connection string.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddPostgresVectorStore(this IServiceCollection services, string connectionString, PostgresVectorStoreOptions? options = default, string? serviceId = default)
    {
        string? npgsqlServiceId = serviceId == null ? default : $"{serviceId}_NpgsqlDataSource";
        // Register NpgsqlDataSource to ensure proper disposal.
        services.AddKeyedSingleton<NpgsqlDataSource>(
            npgsqlServiceId,
            (sp, obj) =>
            {
                NpgsqlDataSourceBuilder dataSourceBuilder = new(connectionString);
                dataSourceBuilder.UseVector();
                return dataSourceBuilder.Build();
            });

        services.AddKeyedSingleton<IVectorStore>(
            serviceId,
            (sp, obj) =>
            {
                var dataSource = sp.GetRequiredKeyedService<NpgsqlDataSource>(npgsqlServiceId);
                var client = new PostgresVectorStoreDbClient(dataSource);
                var selectedOptions = options ?? sp.GetService<PostgresVectorStoreOptions>();

                return new PostgresVectorStore(
                    client,
                    selectedOptions);
            });

        return services;
    }

    /// <summary>
    /// Register a Postgres <see cref="IVectorStore"/> with the specified service ID and where <see cref="IPostgresVectorStoreDbClient"/> is constructed using the NpgsqlDataSource.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="dataSource">The data source to use.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddPostgresVectorStore(this IServiceCollection services, NpgsqlDataSource dataSource, PostgresVectorStoreOptions? options = default, string? serviceId = default)
    {
        // Since we are not constructing the data source, add the IVectorStore as transient, since we
        // cannot make assumptions about how data source is being managed.
        services.AddKeyedTransient<IVectorStore>(
            serviceId,
            (sp, obj) =>
            {
                var client = new PostgresVectorStoreDbClient(dataSource);
                var selectedOptions = options ?? sp.GetService<PostgresVectorStoreOptions>();

                return new PostgresVectorStore(
                    client,
                    selectedOptions);
            });

        return services;
    }

    /// <summary>
    /// Register a Postgres <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/> with the specified service ID
    /// and where the Postgres <see cref="IPostgresVectorStoreDbClient"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddPostgresVectorStoreRecordCollection<TKey, TRecord>(
        this IServiceCollection services,
        string collectionName,
        PostgresVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TKey : notnull
    {
        services.AddKeyedTransient<IVectorStoreRecordCollection<TKey, TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                var PostgresClient = sp.GetRequiredService<IPostgresVectorStoreDbClient>();
                var selectedOptions = options ?? sp.GetService<PostgresVectorStoreRecordCollectionOptions<TRecord>>();

                return (new PostgresVectorStoreRecordCollection<TKey, TRecord>(PostgresClient, collectionName, selectedOptions) as IVectorStoreRecordCollection<TKey, TRecord>)!;
            });

        AddVectorizedSearch<TKey, TRecord>(services, serviceId);

        return services;
    }

    /// <summary>
    /// Register a Postgres <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/> with the specified service ID
    /// and where the Postgres <see cref="IPostgresVectorStoreDbClient"/> is constructed using the provided parameters.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="connectionString">Postgres database connection string.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddPostgresVectorStoreRecordCollection<TKey, TRecord>(
        this IServiceCollection services,
        string collectionName,
        string connectionString,
        PostgresVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TKey : notnull
    {
        string? npgsqlServiceId = serviceId == null ? default : $"{serviceId}_NpgsqlDataSource";
        // Register NpgsqlDataSource to ensure proper disposal.
        services.AddKeyedSingleton<NpgsqlDataSource>(
            npgsqlServiceId,
            (sp, obj) =>
            {
                NpgsqlDataSourceBuilder dataSourceBuilder = new(connectionString);
                dataSourceBuilder.UseVector();
                return dataSourceBuilder.Build();
            });

        services.AddKeyedSingleton<IVectorStoreRecordCollection<TKey, TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                var dataSource = sp.GetRequiredKeyedService<NpgsqlDataSource>(npgsqlServiceId);
                var client = new PostgresVectorStoreDbClient(dataSource);
                var selectedOptions = options ?? sp.GetService<PostgresVectorStoreRecordCollectionOptions<TRecord>>();

                return (new PostgresVectorStoreRecordCollection<TKey, TRecord>(client, collectionName, selectedOptions) as IVectorStoreRecordCollection<TKey, TRecord>)!;
            });

        AddVectorizedSearch<TKey, TRecord>(services, serviceId);

        return services;
    }

    /// <summary>
    /// Register a Postgres <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/> with the specified service ID
    /// and where the Postgres <see cref="IPostgresVectorStoreDbClient"/> is constructed using the data source.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="dataSource">The data source to use.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddPostgresVectorStoreRecordCollection<TKey, TRecord>(
        this IServiceCollection services,
        string collectionName,
        NpgsqlDataSource dataSource,
        PostgresVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TKey : notnull
    {
        // Since we are not constructing the data source, add the IVectorStore as transient, since we
        // cannot make assumptions about how data source is being managed.
        services.AddKeyedTransient<IVectorStoreRecordCollection<TKey, TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                var client = new PostgresVectorStoreDbClient(dataSource);
                var selectedOptions = options ?? sp.GetService<PostgresVectorStoreRecordCollectionOptions<TRecord>>();

                return (new PostgresVectorStoreRecordCollection<TKey, TRecord>(client, collectionName, selectedOptions) as IVectorStoreRecordCollection<TKey, TRecord>)!;
            });

        AddVectorizedSearch<TKey, TRecord>(services, serviceId);

        return services;
    }

    /// <summary>
    /// Also register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> with the given <paramref name="serviceId"/> as a <see cref="IVectorizedSearch{TRecord}"/>.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="services">The service collection to register on.</param>
    /// <param name="serviceId">The service id that the registrations should use.</param>
    private static void AddVectorizedSearch<TKey, TRecord>(IServiceCollection services, string? serviceId)
        where TKey : notnull
    {
        services.AddKeyedTransient<IVectorizedSearch<TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                return sp.GetRequiredKeyedService<IVectorStoreRecordCollection<TKey, TRecord>>(serviceId);
            });
    }
}