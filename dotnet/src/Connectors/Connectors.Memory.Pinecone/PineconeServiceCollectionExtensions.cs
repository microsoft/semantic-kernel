// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Pinecone;
using Sdk = Pinecone;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register Pinecone <see cref="IVectorStore"/> instances on an <see cref="IServiceCollection"/>.
/// </summary>
public static class PineconeServiceCollectionExtensions
{
    /// <summary>
    /// Register a Pinecone <see cref="IVectorStore"/> with the specified service ID and where <see cref="Sdk.PineconeClient"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddPineconeVectorStore(this IServiceCollection services, PineconeVectorStoreOptions? options = default, string? serviceId = default)
    {
        // If we are not constructing the PineconeClient, add the IVectorStore as transient, since we
        // cannot make assumptions about how PineconeClient is being managed.
        services.AddKeyedTransient<IVectorStore>(
            serviceId,
            (sp, obj) =>
            {
                var pineconeClient = sp.GetRequiredService<Sdk.PineconeClient>();
                options ??= sp.GetService<PineconeVectorStoreOptions>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return new PineconeVectorStore(pineconeClient, options);
            });

        return services;
    }

    /// <summary>
    /// Register a Pinecone <see cref="IVectorStore"/> with the specified service ID and where <see cref="Sdk.PineconeClient"/> is constructed using the provided apikey.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="apiKey">The api key for Pinecone.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddPineconeVectorStore(this IServiceCollection services, string apiKey, PineconeVectorStoreOptions? options = default, string? serviceId = default)
    {
        services.AddKeyedSingleton<IVectorStore>(
            serviceId,
            (sp, obj) =>
            {
                var pineconeClient = new Sdk.PineconeClient(apiKey);
                options ??= sp.GetService<PineconeVectorStoreOptions>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return new PineconeVectorStore(pineconeClient, options);
            });

        return services;
    }

    /// <summary>
    /// Register a Pinecone <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorSearch{TRecord}"/> with the
    /// specified service ID and where <see cref="Sdk.PineconeClient"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="PineconeVectorStoreRecordCollection{TKey, TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options to pass to the <see cref="PineconeVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddPineconeVectorStoreRecordCollection<TRecord>(
        this IServiceCollection services,
        string collectionName,
        PineconeVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TRecord : notnull
    {
        // If we are not constructing the PineconeClient, add the IVectorStore as transient, since we
        // cannot make assumptions about how PineconeClient is being managed.
        services.AddKeyedTransient<IVectorStoreRecordCollection<string, TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                var pineconeClient = sp.GetRequiredService<Sdk.PineconeClient>();
                options ??= sp.GetService<PineconeVectorStoreRecordCollectionOptions<TRecord>>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return new PineconeVectorStoreRecordCollection<string, TRecord>(pineconeClient, collectionName, options);
            });

        AddVectorizedSearch<TRecord>(services, serviceId);

        return services;
    }

    /// <summary>
    /// Register a Pinecone <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorSearch{TRecord}"/> with the
    /// provided <see cref="Sdk.PineconeClient"/> and the specified service ID.
    /// </summary>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="PineconeVectorStoreRecordCollection{TKey, TRecord}"/> will access.</param>
    /// <param name="apiKey">The api key for Pinecone.</param>
    /// <param name="options">Optional configuration options to pass to the <see cref="PineconeVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddPineconeVectorStoreRecordCollection<TRecord>(
        this IServiceCollection services,
        string collectionName,
        string apiKey,
        PineconeVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TRecord : notnull
    {
        services.AddKeyedSingleton<IVectorStoreRecordCollection<string, TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                var pineconeClient = new Sdk.PineconeClient(apiKey);
                options ??= sp.GetService<PineconeVectorStoreRecordCollectionOptions<TRecord>>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return new PineconeVectorStoreRecordCollection<string, TRecord>(pineconeClient, collectionName, options);
            });

        AddVectorizedSearch<TRecord>(services, serviceId);

        return services;
    }

    /// <summary>
    /// Also register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> with the given <paramref name="serviceId"/> as a <see cref="IVectorSearch{TRecord}"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="services">The service collection to register on.</param>
    /// <param name="serviceId">The service id that the registrations should use.</param>
    private static void AddVectorizedSearch<TRecord>(IServiceCollection services, string? serviceId) where TRecord : notnull
    {
        services.AddKeyedTransient<IVectorSearch<TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                return sp.GetRequiredKeyedService<IVectorStoreRecordCollection<string, TRecord>>(serviceId);
            });
    }
}
