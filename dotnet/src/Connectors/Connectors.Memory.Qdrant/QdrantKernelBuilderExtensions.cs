// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Qdrant.Client;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register Qdrant <see cref="IVectorStore"/> instances on the <see cref="IKernelBuilder"/>.
/// </summary>
[Obsolete("The IKernelBuilder extensions are being obsoleted, call the appropriate function on the Services property of your IKernelBuilder")]
public static class QdrantKernelBuilderExtensions
{
    /// <summary>
    /// Register a Qdrant <see cref="IVectorStore"/> with the specified service ID and where <see cref="QdrantClient"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <param name="builder">The builder to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddQdrantVectorStore(this IKernelBuilder builder, QdrantVectorStoreOptions? options = default, string? serviceId = default)
    {
        builder.Services.AddQdrantVectorStore(options, serviceId);
        return builder;
    }
    /// <summary>
    /// Register a Qdrant <see cref="IVectorStore"/> with the specified service ID and where <see cref="QdrantClient"/> is constructed using the provided parameters.
    /// </summary>
    /// <param name="builder">The builder to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="host">The Qdrant service host name.</param>
    /// <param name="port">The Qdrant service port.</param>
    /// <param name="https">A value indicating whether to use HTTPS for communicating with Qdrant.</param>
    /// <param name="apiKey">The Qdrant service API key.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddQdrantVectorStore(this IKernelBuilder builder, string host, int port = 6334, bool https = false, string? apiKey = default, QdrantVectorStoreOptions? options = default, string? serviceId = default)
    {
        builder.Services.AddQdrantVectorStore(host, port, https, apiKey, options, serviceId);
        return builder;
    }

    /// <summary>
    /// Register a Qdrant <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorSearch{TRecord}"/> with the specified service ID
    /// and where the Qdrant <see cref="QdrantClient"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="builder">The builder to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddQdrantVectorStoreRecordCollection<TKey, TRecord>(
        this IKernelBuilder builder,
        string collectionName,
        QdrantVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TKey : notnull
        where TRecord : notnull
    {
        builder.Services.AddQdrantVectorStoreRecordCollection<TKey, TRecord>(collectionName, options, serviceId);
        return builder;
    }

    /// <summary>
    /// Register a Qdrant <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorSearch{TRecord}"/> with the specified service ID
    /// and where the Qdrant <see cref="QdrantClient"/> is constructed using the provided parameters.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="builder">The builder to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="host">The Qdrant service host name.</param>
    /// <param name="port">The Qdrant service port.</param>
    /// <param name="https">A value indicating whether to use HTTPS for communicating with Qdrant.</param>
    /// <param name="apiKey">The Qdrant service API key.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddQdrantVectorStoreRecordCollection<TKey, TRecord>(
        this IKernelBuilder builder,
        string collectionName,
        string host,
        int port = 6334,
        bool https = false,
        string? apiKey = default,
        QdrantVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TKey : notnull
        where TRecord : notnull
    {
        builder.Services.AddQdrantVectorStoreRecordCollection<TKey, TRecord>(collectionName, host, port, https, apiKey, options, serviceId);
        return builder;
    }
}
