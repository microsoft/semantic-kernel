// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using Azure;
using Azure.Core;
using Azure.Core.Serialization;
using Azure.Search.Documents;
using Azure.Search.Documents.Indexes;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register Azure AI Search <see cref="VectorStore"/> instances on an <see cref="IServiceCollection"/>.
/// </summary>
public static class AzureAISearchServiceCollectionExtensions
{
    /// <summary>
    /// Register an Azure AI Search <see cref="VectorStore"/> with the specified service ID and where <see cref="SearchIndexClient"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStore"/> on.</param>
    /// <param name="options">Optional options to further configure the <see cref="VectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddAzureAISearchVectorStore(this IServiceCollection services, AzureAISearchVectorStoreOptions? options = default, string? serviceId = default)
    {
        // If we are not constructing the SearchIndexClient, add the IVectorStore as transient, since we
        // cannot make assumptions about how SearchIndexClient is being managed.
        services.AddKeyedTransient<VectorStore>(
            serviceId,
            (sp, obj) =>
            {
                var searchIndexClient = sp.GetRequiredService<SearchIndexClient>();
                options ??= sp.GetService<AzureAISearchVectorStoreOptions>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return new AzureAISearchVectorStore(searchIndexClient, options);
            });

        return services;
    }

    /// <summary>
    /// Register an Azure AI Search <see cref="VectorStore"/> with the provided <see cref="Uri"/> and <see cref="TokenCredential"/> and the specified service ID.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStore"/> on.</param>
    /// <param name="endpoint">The service endpoint for Azure AI Search.</param>
    /// <param name="tokenCredential">The credential to authenticate to Azure AI Search with.</param>
    /// <param name="options">Optional options to further configure the <see cref="VectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddAzureAISearchVectorStore(this IServiceCollection services, Uri endpoint, TokenCredential tokenCredential, AzureAISearchVectorStoreOptions? options = default, string? serviceId = default)
    {
        Verify.NotNull(endpoint);
        Verify.NotNull(tokenCredential);

        services.AddKeyedSingleton<VectorStore>(
            serviceId,
            (sp, obj) =>
            {
                options ??= sp.GetService<AzureAISearchVectorStoreOptions>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };
                var searchClientOptions = BuildSearchClientOptions(options?.JsonSerializerOptions);
                var searchIndexClient = new SearchIndexClient(endpoint, tokenCredential, searchClientOptions);

                // Construct the vector store.
                return new AzureAISearchVectorStore(searchIndexClient, options);
            });

        return services;
    }

    /// <summary>
    /// Register an Azure AI Search <see cref="VectorStore"/> with the provided <see cref="Uri"/> and <see cref="AzureKeyCredential"/> and the specified service ID.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStore"/> on.</param>
    /// <param name="endpoint">The service endpoint for Azure AI Search.</param>
    /// <param name="credential">The credential to authenticate to Azure AI Search with.</param>
    /// <param name="options">Optional options to further configure the <see cref="VectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddAzureAISearchVectorStore(this IServiceCollection services, Uri endpoint, AzureKeyCredential credential, AzureAISearchVectorStoreOptions? options = default, string? serviceId = default)
    {
        Verify.NotNull(endpoint);
        Verify.NotNull(credential);

        services.AddKeyedSingleton<VectorStore>(
            serviceId,
            (sp, obj) =>
            {
                options ??= sp.GetService<AzureAISearchVectorStoreOptions>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };
                var searchClientOptions = BuildSearchClientOptions(options?.JsonSerializerOptions);
                var searchIndexClient = new SearchIndexClient(endpoint, credential, searchClientOptions);

                // Construct the vector store.
                return new AzureAISearchVectorStore(searchIndexClient, options);
            });

        return services;
    }

    /// <summary>
    /// Register an Azure AI Search <see cref="VectorStoreCollection{TKey, TRecord}"/> and an <see cref="IVectorSearchable{TRecord}"/> with the
    /// specified service ID and where <see cref="SearchIndexClient"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStoreCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="AzureAISearchCollection{TKey, TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options to pass to the <see cref="AzureAISearchCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddAzureAISearchVectorStoreRecordCollection<TRecord>(
        this IServiceCollection services,
        string collectionName,
        AzureAISearchCollectionOptions? options = default,
        string? serviceId = default)
        where TRecord : class
    {
        // If we are not constructing the SearchIndexClient, add the IVectorStore as transient, since we
        // cannot make assumptions about how SearchIndexClient is being managed.
        services.AddKeyedTransient<VectorStoreCollection<string, TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                var searchIndexClient = sp.GetRequiredService<SearchIndexClient>();
                options ??= sp.GetService<AzureAISearchCollectionOptions>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };

                return new AzureAISearchCollection<string, TRecord>(searchIndexClient, collectionName, options);
            });

        AddVectorizedSearch<TRecord>(services, serviceId);

        return services;
    }

    /// <summary>
    /// Register an Azure AI Search <see cref="VectorStoreCollection{TKey, TRecord}"/> and an <see cref="IVectorSearchable{TRecord}"/> with the
    /// provided <see cref="Uri"/> and <see cref="TokenCredential"/> and the specified service ID.
    /// </summary>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStoreCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="AzureAISearchCollection{TKey, TRecord}"/> will access.</param>
    /// <param name="endpoint">The service endpoint for Azure AI Search.</param>
    /// <param name="tokenCredential">The credential to authenticate to Azure AI Search with.</param>
    /// <param name="options">Optional configuration options to pass to the <see cref="AzureAISearchCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddAzureAISearchVectorStoreRecordCollection<TRecord>(
        this IServiceCollection services,
        string collectionName,
        Uri endpoint,
        TokenCredential tokenCredential,
        AzureAISearchCollectionOptions? options = default,
        string? serviceId = default)
        where TRecord : class
    {
        Verify.NotNull(endpoint);
        Verify.NotNull(tokenCredential);

        services.AddKeyedSingleton<VectorStoreCollection<string, TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                options ??= sp.GetService<AzureAISearchCollectionOptions>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };
                var searchClientOptions = BuildSearchClientOptions(options?.JsonSerializerOptions);
                var searchIndexClient = new SearchIndexClient(endpoint, tokenCredential, searchClientOptions);

                // Construct the vector store.
                return new AzureAISearchCollection<string, TRecord>(searchIndexClient, collectionName, options);
            });

        AddVectorizedSearch<TRecord>(services, serviceId);

        return services;
    }

    /// <summary>
    /// Register an Azure AI Search <see cref="VectorStoreCollection{TKey, TRecord}"/> and an <see cref="IVectorSearchable{TRecord}"/> with the
    /// provided <see cref="Uri"/> and <see cref="AzureKeyCredential"/> and the specified service ID.
    /// </summary>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="VectorStoreCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="AzureAISearchCollection{TKey, TRecord}"/> will access.</param>
    /// <param name="endpoint">The service endpoint for Azure AI Search.</param>
    /// <param name="credential">The credential to authenticate to Azure AI Search with.</param>
    /// <param name="options">Optional configuration options to pass to the <see cref="AzureAISearchCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddAzureAISearchVectorStoreRecordCollection<TRecord>(
        this IServiceCollection services,
        string collectionName,
        Uri endpoint,
        AzureKeyCredential credential,
        AzureAISearchCollectionOptions? options = default,
        string? serviceId = default)
        where TRecord : class
    {
        Verify.NotNull(endpoint);
        Verify.NotNull(credential);

        services.AddKeyedSingleton<VectorStoreCollection<string, TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                options ??= sp.GetService<AzureAISearchCollectionOptions>() ?? new()
                {
                    EmbeddingGenerator = sp.GetService<IEmbeddingGenerator>()
                };
                var searchClientOptions = BuildSearchClientOptions(options?.JsonSerializerOptions);
                var searchIndexClient = new SearchIndexClient(endpoint, credential, searchClientOptions);

                // Construct the vector store.
                return new AzureAISearchCollection<string, TRecord>(searchIndexClient, collectionName, options);
            });

        AddVectorizedSearch<TRecord>(services, serviceId);

        return services;
    }

    /// <summary>
    /// Also register the <see cref="VectorStoreCollection{TKey, TRecord}"/> with the given <paramref name="serviceId"/> as a <see cref="IVectorSearchable{TRecord}"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="services">The service collection to register on.</param>
    /// <param name="serviceId">The service id that the registrations should use.</param>
    private static void AddVectorizedSearch<TRecord>(IServiceCollection services, string? serviceId) where TRecord : class
    {
        services.AddKeyedTransient<IVectorSearchable<TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                return sp.GetRequiredKeyedService<VectorStoreCollection<string, TRecord>>(serviceId);
            });
    }

    /// <summary>
    /// Build a <see cref="SearchClientOptions"/> instance, using the provided <see cref="JsonSerializerOptions"/> if it's not null and add the SK user agent string.
    /// </summary>
    /// <param name="jsonSerializerOptions">Optional <see cref="JsonSerializerOptions"/> to add to the options if provided.</param>
    /// <returns>The <see cref="SearchClientOptions"/>.</returns>
    private static SearchClientOptions BuildSearchClientOptions(JsonSerializerOptions? jsonSerializerOptions)
    {
        var searchClientOptions = new SearchClientOptions();
        searchClientOptions.Diagnostics.ApplicationId = HttpHeaderConstant.Values.UserAgent;
        if (jsonSerializerOptions != null)
        {
            searchClientOptions.Serializer = new JsonObjectSerializer(jsonSerializerOptions);
        }

        return searchClientOptions;
    }
}
