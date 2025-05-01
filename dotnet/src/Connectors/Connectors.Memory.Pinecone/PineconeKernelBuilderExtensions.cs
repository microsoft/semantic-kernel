// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Pinecone;
using Sdk = Pinecone;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register Pinecone <see cref="IVectorStore"/> instances on the <see cref="IKernelBuilder"/>.
/// </summary>
[Obsolete("The IKernelBuilder extensions are being obsoleted, call the appropriate function on the Services property of your IKernelBuilder")]
public static class PineconeKernelBuilderExtensions
{
    /// <summary>
    /// Register a Pinecone <see cref="IVectorStore"/> with the specified service ID and where <see cref="Sdk.PineconeClient"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <param name="builder">The builder to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddPineconeVectorStore(this IKernelBuilder builder, PineconeVectorStoreOptions? options = default, string? serviceId = default)
    {
        builder.Services.AddPineconeVectorStore(options, serviceId);
        return builder;
    }

    /// <summary>
    /// Register a Pinecone <see cref="IVectorStore"/> with the specified service ID and where <see cref="Sdk.PineconeClient"/> is constructed using the provided apikey.
    /// </summary>
    /// <param name="builder">The builder to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="apiKey">The api key for Pinecone.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddPineconeVectorStore(this IKernelBuilder builder, string apiKey, PineconeVectorStoreOptions? options = default, string? serviceId = default)
    {
        builder.Services.AddPineconeVectorStore(apiKey, options, serviceId);
        return builder;
    }

    /// <summary>
    /// Register a Pinecone <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorSearch{TRecord}"/> with the
    /// specified service ID and where <see cref="Sdk.PineconeClient"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="builder">The builder to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="PineconeVectorStoreRecordCollection{TKey, TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options to pass to the <see cref="PineconeVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddPineconeVectorStoreRecordCollection<TRecord>(
        this IKernelBuilder builder,
        string collectionName,
        PineconeVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TRecord : notnull
    {
        builder.Services.AddPineconeVectorStoreRecordCollection<TRecord>(collectionName, options, serviceId);
        return builder;
    }

    /// <summary>
    /// Register a Pinecone <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorSearch{TRecord}"/> with the
    /// provided <see cref="Sdk.PineconeClient"/> and the specified service ID.
    /// </summary>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="builder">The builder to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="PineconeVectorStoreRecordCollection{TKey, TRecord}"/> will access.</param>
    /// <param name="apiKey">The api key for Pinecone.</param>
    /// <param name="options">Optional configuration options to pass to the <see cref="PineconeVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddPineconeVectorStoreRecordCollection<TRecord>(
        this IKernelBuilder builder,
        string collectionName,
        string apiKey,
        PineconeVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TRecord : notnull
    {
        builder.Services.AddPineconeVectorStoreRecordCollection<TRecord>(collectionName, apiKey, options, serviceId);
        return builder;
    }
}
