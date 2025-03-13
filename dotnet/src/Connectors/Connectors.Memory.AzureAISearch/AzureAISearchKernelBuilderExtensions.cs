// Copyright (c) Microsoft. All rights reserved.

using System;
using Azure;
using Azure.Core;
using Azure.Search.Documents.Indexes;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register Azure AI Search <see cref="IVectorStore"/> instances on the <see cref="IKernelBuilder"/>.
/// </summary>
[Obsolete("Call the corresponding method on the Services property of your IKernelBuilder instance.")]
public static class AzureAISearchKernelBuilderExtensions
{
    /// <summary>
    /// Register an Azure AI Search <see cref="IVectorStore"/> with the specified service ID and where <see cref="SearchIndexClient"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <param name="builder">The builder to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddAzureAISearchVectorStore(this IKernelBuilder builder, AzureAISearchVectorStoreOptions? options = default, string? serviceId = default)
    {
        builder.Services.AddKeyedAzureAISearchVectorStore(serviceId, options);
        return builder;
    }

    /// <summary>
    /// Register an Azure AI Search <see cref="IVectorStore"/> with the provided <see cref="Uri"/> and <see cref="TokenCredential"/> and the specified service ID.
    /// </summary>
    /// <param name="builder">The builder to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="endpoint">The service endpoint for Azure AI Search.</param>
    /// <param name="tokenCredential">The credential to authenticate to Azure AI Search with.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddAzureAISearchVectorStore(this IKernelBuilder builder, Uri endpoint, TokenCredential tokenCredential, AzureAISearchVectorStoreOptions? options = default, string? serviceId = default)
    {
        builder.Services.AddKeyedAzureAISearchVectorStore(serviceId, endpoint, tokenCredential, options);
        return builder;
    }

    /// <summary>
    /// Register an Azure AI Search <see cref="IVectorStore"/> with the provided <see cref="Uri"/> and <see cref="AzureKeyCredential"/> and the specified service ID.
    /// </summary>
    /// <param name="builder">The builder to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="endpoint">The service endpoint for Azure AI Search.</param>
    /// <param name="credential">The credential to authenticate to Azure AI Search with.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddAzureAISearchVectorStore(this IKernelBuilder builder, Uri endpoint, AzureKeyCredential credential, AzureAISearchVectorStoreOptions? options = default, string? serviceId = default)
    {
        builder.Services.AddKeyedAzureAISearchVectorStore(serviceId, endpoint, credential, options);
        return builder;
    }

    /// <summary>
    /// Register an Azure AI Search <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>, <see cref="IVectorizedSearch{TRecord}"/> and <see cref="IVectorizableTextSearch{TRecord}"/> with the
    /// specified service ID and where <see cref="SearchIndexClient"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="builder">The builder to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="AzureAISearchVectorStoreRecordCollection{TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options to pass to the <see cref="AzureAISearchVectorStoreRecordCollection{TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddAzureAISearchVectorStoreRecordCollection<TRecord>(
        this IKernelBuilder builder,
        string collectionName,
        AzureAISearchVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
    {
        builder.Services.AddKeyedAzureAISearchVectorStoreRecordCollection<TRecord>(serviceId, collectionName, options);
        return builder;
    }

    /// <summary>
    /// Register an Azure AI Search <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>, <see cref="IVectorizedSearch{TRecord}"/> and <see cref="IVectorizableTextSearch{TRecord}"/> with the
    /// provided <see cref="Uri"/> and <see cref="TokenCredential"/> and the specified service ID.
    /// </summary>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="builder">The builder to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="AzureAISearchVectorStoreRecordCollection{TRecord}"/> will access.</param>
    /// <param name="endpoint">The service endpoint for Azure AI Search.</param>
    /// <param name="tokenCredential">The credential to authenticate to Azure AI Search with.</param>
    /// <param name="options">Optional configuration options to pass to the <see cref="AzureAISearchVectorStoreRecordCollection{TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddAzureAISearchVectorStoreRecordCollection<TRecord>(
        this IKernelBuilder builder,
        string collectionName,
        Uri endpoint,
        TokenCredential tokenCredential,
        AzureAISearchVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
    {
        builder.Services.AddKeyedAzureAISearchVectorStoreRecordCollection<TRecord>(serviceId, collectionName, endpoint, tokenCredential, options);
        return builder;
    }

    /// <summary>
    /// Register an Azure AI Search <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>, <see cref="IVectorizedSearch{TRecord}"/> and <see cref="IVectorizableTextSearch{TRecord}"/> with the
    /// provided <see cref="Uri"/> and <see cref="AzureKeyCredential"/> and the specified service ID.
    /// </summary>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="builder">The builder to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="AzureAISearchVectorStoreRecordCollection{TRecord}"/> will access.</param>
    /// <param name="endpoint">The service endpoint for Azure AI Search.</param>
    /// <param name="credential">The credential to authenticate to Azure AI Search with.</param>
    /// <param name="options">Optional configuration options to pass to the <see cref="AzureAISearchVectorStoreRecordCollection{TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddAzureAISearchVectorStoreRecordCollection<TRecord>(
        this IKernelBuilder builder,
        string collectionName,
        Uri endpoint,
        AzureKeyCredential credential,
        AzureAISearchVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
    {
        builder.Services.AddKeyedAzureAISearchVectorStoreRecordCollection<TRecord>(serviceId, collectionName, endpoint, credential, options);
        return builder;
    }
}
