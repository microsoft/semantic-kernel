// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using Azure;
using Azure.Core;
using Azure.Core.Serialization;
using Azure.Search.Documents;
using Azure.Search.Documents.Indexes;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register Azure AI Search <see cref="IVectorStore"/> instances on an <see cref="IServiceCollection"/>.
/// </summary>
public static class AzureAISearchServiceCollectionExtensions
{
    /// <summary>
    /// Registers an Azure AI Search <see cref="IVectorStore"/> in the <see cref="IServiceCollection"/>, retrieving the <see cref="SearchIndexClient"/> from the dependency injection container.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddAzureAISearchVectorStore(
        this IServiceCollection serviceCollection,
        AzureAISearchVectorStoreOptions? options = default,
        // If we are not constructing the SearchIndexClient, add the IVectorStore as transient, since we
        // cannot make assumptions about how SearchIndexClient is being managed.
        ServiceLifetime lifetime = ServiceLifetime.Transient)
        => AddKeyedAzureAISearchVectorStore(serviceCollection, serviceKey: null, options, lifetime);

    /// <summary>
    /// Registers a keyed Azure AI Search <see cref="IVectorStore"/> in the <see cref="IServiceCollection"/>, retrieving the <see cref="SearchIndexClient"/> from the dependency injection container.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddKeyedAzureAISearchVectorStore(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        AzureAISearchVectorStoreOptions? options = default,
        // If we are not constructing the SearchIndexClient, add the IVectorStore as transient, since we
        // cannot make assumptions about how SearchIndexClient is being managed.
        ServiceLifetime lifetime = ServiceLifetime.Transient)
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStore),
                serviceKey,
                (serviceProvider, _) => new AzureAISearchVectorStore(
                    serviceProvider.GetRequiredService<SearchIndexClient>(),
                    options ?? serviceProvider.GetService<AzureAISearchVectorStoreOptions>()),
                lifetime));

        return serviceCollection;
    }

    /// <summary>
    /// Registers an Azure AI Search <see cref="IVectorStore"/> in the <see cref="IServiceCollection"/>, using the provided <see cref="Uri"/> and <see cref="TokenCredential"/>.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="endpoint">The service endpoint for Azure AI Search.</param>
    /// <param name="tokenCredential">The credential to authenticate to Azure AI Search with.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddAzureAISearchVectorStore(
        this IServiceCollection serviceCollection,
        Uri endpoint,
        TokenCredential tokenCredential,
        AzureAISearchVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        => AddKeyedAzureAISearchVectorStore(serviceCollection, serviceKey: null, endpoint, tokenCredential, options, lifetime);

    /// <summary>
    /// Registers a keyed Azure AI Search <see cref="IVectorStore"/> in the <see cref="IServiceCollection"/>, using the provided <see cref="Uri"/> and <see cref="TokenCredential"/>.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="endpoint">The service endpoint for Azure AI Search.</param>
    /// <param name="tokenCredential">The credential to authenticate to Azure AI Search with.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddKeyedAzureAISearchVectorStore(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        Uri endpoint,
        TokenCredential tokenCredential,
        AzureAISearchVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNull(endpoint);
        Verify.NotNull(tokenCredential);

        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStore),
                serviceKey,
                (serviceProvider, _) =>
                {
                    options ??= serviceProvider.GetService<AzureAISearchVectorStoreOptions>();
                    var searchClientOptions = BuildSearchClientOptions(options?.JsonSerializerOptions);
                    var searchIndexClient = new SearchIndexClient(endpoint, tokenCredential, searchClientOptions);

                    // Construct the vector store.
                    return new AzureAISearchVectorStore(searchIndexClient, options);
                },
                lifetime));

        return serviceCollection;
    }

    /// <summary>
    /// Registers an Azure AI Search <see cref="IVectorStore"/> in the <see cref="IServiceCollection"/>, using the provided <see cref="Uri"/> and <see cref="AzureKeyCredential"/>.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="endpoint">The service endpoint for Azure AI Search.</param>
    /// <param name="credential">The credential to authenticate to Azure AI Search with.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddAzureAISearchVectorStore(
        this IServiceCollection serviceCollection,
        Uri endpoint,
        AzureKeyCredential credential,
        AzureAISearchVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        => AddKeyedAzureAISearchVectorStore(serviceCollection, serviceKey: null, endpoint, credential, options, lifetime);

    /// <summary>
    /// Registers a keyed Azure AI Search <see cref="IVectorStore"/> in the <see cref="IServiceCollection"/>, using the provided <see cref="Uri"/> and <see cref="AzureKeyCredential"/>.
    /// </summary>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="endpoint">The service endpoint for Azure AI Search.</param>
    /// <param name="credential">The credential to authenticate to Azure AI Search with.</param>
    /// <param name="options">Options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="lifetime">The service lifetime for the store. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddKeyedAzureAISearchVectorStore(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        Uri endpoint,
        AzureKeyCredential credential,
        AzureAISearchVectorStoreOptions? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Transient)
    {
        Verify.NotNull(endpoint);
        Verify.NotNull(credential);

        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStore),
                serviceKey,
                (serviceProvider, _) =>
                {
                    options ??= serviceProvider.GetService<AzureAISearchVectorStoreOptions>();
                    var searchClientOptions = BuildSearchClientOptions(options?.JsonSerializerOptions);
                    var searchIndexClient = new SearchIndexClient(endpoint, credential, searchClientOptions);

                    // Construct the vector store.
                    return new AzureAISearchVectorStore(searchIndexClient, options);
                },
                lifetime));

        return serviceCollection;
    }

    /// <summary>
    /// Registers an Azure AI Search <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>, <see cref="IVectorizedSearch{TRecord}"/> and <see cref="IVectorizableTextSearch{TRecord}"/>,
    /// retrieving the <see cref="SearchIndexClient"/> from the dependency injection container.
    /// </summary>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="AzureAISearchVectorStoreRecordCollection{TRecord}"/> will access.</param>
    /// <param name="options">Configuration options to pass to the <see cref="AzureAISearchVectorStoreRecordCollection{TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the collection. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddAzureAISearchVectorStoreRecordCollection<TRecord>(
        this IServiceCollection serviceCollection,
        string collectionName,
        AzureAISearchVectorStoreRecordCollectionOptions<TRecord>? options = default,
        // If we are not constructing the SearchIndexClient, add the IVectorStore as transient, since we
        // cannot make assumptions about how SearchIndexClient is being managed.
        ServiceLifetime lifetime = ServiceLifetime.Transient)
        => AddKeyedAzureAISearchVectorStoreRecordCollection(serviceCollection, serviceKey: null, collectionName, options, lifetime);

    /// <summary>
    /// Registers a keyed Azure AI Search <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>, <see cref="IVectorizedSearch{TRecord}"/> and <see cref="IVectorizableTextSearch{TRecord}"/>,
    /// retrieving the <see cref="SearchIndexClient"/> from the dependency injection container.
    /// </summary>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="AzureAISearchVectorStoreRecordCollection{TRecord}"/> will access.</param>
    /// <param name="options">Configuration options to pass to the <see cref="AzureAISearchVectorStoreRecordCollection{TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the collection. Defaults to <see cref="ServiceLifetime.Transient"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddKeyedAzureAISearchVectorStoreRecordCollection<TRecord>(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        string collectionName,
        AzureAISearchVectorStoreRecordCollectionOptions<TRecord>? options = default,
        // If we are not constructing the SearchIndexClient, add the IVectorStore as transient, since we
        // cannot make assumptions about how SearchIndexClient is being managed.
        ServiceLifetime lifetime = ServiceLifetime.Transient)
    {
        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStoreRecordCollection<string, TRecord>),
                serviceKey,
                (serviceProvider, _) => new AzureAISearchVectorStoreRecordCollection<TRecord>(
                    serviceProvider.GetRequiredService<SearchIndexClient>(),
                    collectionName,
                    options ?? serviceProvider.GetService<AzureAISearchVectorStoreRecordCollectionOptions<TRecord>>()),
                lifetime));

        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorizedSearch<TRecord>),
                serviceKey,
                static (serviceProvider, serviceKey) => serviceProvider.GetRequiredKeyedService<IVectorStoreRecordCollection<string, TRecord>>(serviceKey),
                lifetime));

        return serviceCollection;
    }

    /// <summary>
    /// Registers an Azure AI Search <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>, <see cref="IVectorizedSearch{TRecord}"/> and <see cref="IVectorizableTextSearch{TRecord}"/> with the
    /// provided <see cref="Uri"/> and <see cref="TokenCredential"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="AzureAISearchVectorStoreRecordCollection{TRecord}"/> will access.</param>
    /// <param name="endpoint">The service endpoint for Azure AI Search.</param>
    /// <param name="tokenCredential">The credential to authenticate to Azure AI Search with.</param>
    /// <param name="options">Optional configuration options to pass to the <see cref="AzureAISearchVectorStoreRecordCollection{TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the collection. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddAzureAISearchVectorStoreRecordCollection<TRecord>(
        this IServiceCollection serviceCollection,
        string collectionName,
        Uri endpoint,
        TokenCredential tokenCredential,
        AzureAISearchVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        => AddKeyedAzureAISearchVectorStoreRecordCollection(serviceCollection, serviceKey: null, collectionName, endpoint, tokenCredential, options, lifetime);

    /// <summary>
    /// Registers a keyed Azure AI Search <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>, <see cref="IVectorizedSearch{TRecord}"/> and <see cref="IVectorizableTextSearch{TRecord}"/> with the
    /// provided <see cref="Uri"/> and <see cref="TokenCredential"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to which the vector store should be added.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="AzureAISearchVectorStoreRecordCollection{TRecord}"/> will access.</param>
    /// <param name="endpoint">The service endpoint for Azure AI Search.</param>
    /// <param name="tokenCredential">The credential to authenticate to Azure AI Search with.</param>
    /// <param name="options">Optional configuration options to pass to the <see cref="AzureAISearchVectorStoreRecordCollection{TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the collection. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddKeyedAzureAISearchVectorStoreRecordCollection<TRecord>(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        string collectionName,
        Uri endpoint,
        TokenCredential tokenCredential,
        AzureAISearchVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNull(endpoint);
        Verify.NotNull(tokenCredential);

        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStoreRecordCollection<string, TRecord>),
                serviceKey,
                (serviceProvider, _) =>
                {
                    options ??= serviceProvider.GetService<AzureAISearchVectorStoreRecordCollectionOptions<TRecord>>();
                    var searchClientOptions = BuildSearchClientOptions(options?.JsonSerializerOptions);
                    var searchIndexClient = new SearchIndexClient(endpoint, tokenCredential, searchClientOptions);

                    // Construct the vector store.
                    return new AzureAISearchVectorStoreRecordCollection<TRecord>(searchIndexClient, collectionName, options);
                },
                lifetime));

        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorizedSearch<TRecord>),
                serviceKey,
                static (serviceProvider, serviceKey) => serviceProvider.GetRequiredKeyedService<IVectorStoreRecordCollection<string, TRecord>>(serviceKey),
                lifetime));

        return serviceCollection;
    }

    /// <summary>
    /// Registers an Azure AI Search <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>, <see cref="IVectorizedSearch{TRecord}"/> and <see cref="IVectorizableTextSearch{TRecord}"/> with the
    /// provided <see cref="Uri"/> and <see cref="AzureKeyCredential"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="AzureAISearchVectorStoreRecordCollection{TRecord}"/> will access.</param>
    /// <param name="endpoint">The service endpoint for Azure AI Search.</param>
    /// <param name="credential">The credential to authenticate to Azure AI Search with.</param>
    /// <param name="options">Optional configuration options to pass to the <see cref="AzureAISearchVectorStoreRecordCollection{TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the collection. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddAzureAISearchVectorStoreRecordCollection<TRecord>(
        this IServiceCollection serviceCollection,
        string collectionName,
        Uri endpoint,
        AzureKeyCredential credential,
        AzureAISearchVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
        => AddKeyedAzureAISearchVectorStoreRecordCollection(serviceCollection, serviceKey: null, collectionName, endpoint, credential, options, lifetime);

    /// <summary>
    /// Registers a keyed Azure AI Search <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>, <see cref="IVectorizedSearch{TRecord}"/> and <see cref="IVectorizableTextSearch{TRecord}"/> with the
    /// provided <see cref="Uri"/> and <see cref="AzureKeyCredential"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="serviceCollection">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="serviceKey">The key with which to associate the vector store.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="AzureAISearchVectorStoreRecordCollection{TRecord}"/> will access.</param>
    /// <param name="endpoint">The service endpoint for Azure AI Search.</param>
    /// <param name="credential">The credential to authenticate to Azure AI Search with.</param>
    /// <param name="options">Optional configuration options to pass to the <see cref="AzureAISearchVectorStoreRecordCollection{TRecord}"/>.</param>
    /// <param name="lifetime">The service lifetime for the collection. Defaults to <see cref="ServiceLifetime.Singleton"/>.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddKeyedAzureAISearchVectorStoreRecordCollection<TRecord>(
        this IServiceCollection serviceCollection,
        object? serviceKey,
        string collectionName,
        Uri endpoint,
        AzureKeyCredential credential,
        AzureAISearchVectorStoreRecordCollectionOptions<TRecord>? options = default,
        ServiceLifetime lifetime = ServiceLifetime.Singleton)
    {
        Verify.NotNull(endpoint);
        Verify.NotNull(credential);

        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorStoreRecordCollection<string, TRecord>),
                serviceKey,
                (serviceProvider, _) =>
                {
                    var selectedOptions = options ?? serviceProvider.GetService<AzureAISearchVectorStoreRecordCollectionOptions<TRecord>>();
                    var searchClientOptions = BuildSearchClientOptions(selectedOptions?.JsonSerializerOptions);
                    var searchIndexClient = new SearchIndexClient(endpoint, credential, searchClientOptions);

                    // Construct the vector store.
                    return new AzureAISearchVectorStoreRecordCollection<TRecord>(searchIndexClient, collectionName, selectedOptions);
                },
                lifetime));

        serviceCollection.Add(
            new ServiceDescriptor(
                typeof(IVectorizedSearch<TRecord>),
                serviceKey, static (serviceProvider, serviceKey) => serviceProvider.GetRequiredKeyedService<IVectorStoreRecordCollection<string, TRecord>>(serviceKey),
                lifetime));

        return serviceCollection;
    }

    /// <summary>
    /// Build a <see cref="SearchClientOptions"/> instance, using the provided <see cref="JsonSerializerOptions"/> if it's not null and add the SK user agent string.
    /// </summary>
    /// <param name="jsonSerializerOptions">Optional <see cref="JsonSerializerOptions"/> to add to the options if provided.</param>
    /// <returns>The <see cref="SearchClientOptions"/>.</returns>
    private static SearchClientOptions BuildSearchClientOptions(JsonSerializerOptions? jsonSerializerOptions)
    {
        var searchClientOptions = new SearchClientOptions
        {
            Diagnostics = { ApplicationId = HttpHeaderConstant.Values.UserAgent }
        };

        if (jsonSerializerOptions != null)
        {
            searchClientOptions.Serializer = new JsonObjectSerializer(jsonSerializerOptions);
        }

        return searchClientOptions;
    }
}
