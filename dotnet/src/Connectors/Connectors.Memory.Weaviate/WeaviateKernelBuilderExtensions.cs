// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Weaviate;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register Weaviate <see cref="IVectorStore"/> instances on the <see cref="IKernelBuilder"/>.
/// </summary>
[Obsolete("The IKernelBuilder extensions are being obsoleted, call the appropriate function on the Services property of your IKernelBuilder")]
public static class WeaviateKernelBuilderExtensions
{
    /// <summary>
    /// Register a Weaviate <see cref="IVectorStore"/> with the specified service ID.
    /// </summary>
    /// <param name="builder">The builder to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="httpClient">
    /// <see cref="HttpClient"/> that is used to interact with Weaviate API.
    /// <see cref="HttpClient.BaseAddress"/> should point to remote or local cluster and API key can be configured via <see cref="HttpClient.DefaultRequestHeaders"/>.
    /// It's also possible to provide these parameters via <see cref="WeaviateVectorStoreOptions"/>.
    /// </param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddWeaviateVectorStore(
        this IKernelBuilder builder,
        HttpClient? httpClient = default,
        WeaviateVectorStoreOptions? options = default,
        string? serviceId = default)
    {
        builder.Services.AddWeaviateVectorStore(httpClient, options, serviceId);
        return builder;
    }

    /// <summary>
    /// Register a Weaviate <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorSearch{TRecord}"/> with the specified service ID.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="builder">The builder to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="httpClient">
    /// <see cref="HttpClient"/> that is used to interact with Weaviate API.
    /// <see cref="HttpClient.BaseAddress"/> should point to remote or local cluster and API key can be configured via <see cref="HttpClient.DefaultRequestHeaders"/>.
    /// It's also possible to provide these parameters via <see cref="WeaviateVectorStoreOptions"/>.
    /// </param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddWeaviateVectorStoreRecordCollection<TRecord>(
        this IKernelBuilder builder,
        string collectionName,
        HttpClient? httpClient = default,
        WeaviateVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TRecord : notnull
    {
        builder.Services.AddWeaviateVectorStoreRecordCollection(collectionName, httpClient, options, serviceId);
        return builder;
    }
}
