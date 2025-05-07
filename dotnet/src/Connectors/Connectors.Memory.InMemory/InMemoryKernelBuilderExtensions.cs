// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.InMemory;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register Data services on the <see cref="IKernelBuilder"/>.
/// </summary>
[Obsolete("The IKernelBuilder extensions are being obsoleted, call the appropriate function on the Services property of your IKernelBuilder")]
public static class InMemoryKernelBuilderExtensions
{
    /// <summary>
    /// Register an InMemory <see cref="IVectorStore"/> with the specified service ID.
    /// </summary>
    /// <param name="builder">The builder to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddInMemoryVectorStore(this IKernelBuilder builder, string? serviceId = default)
    {
        builder.Services.AddInMemoryVectorStore(serviceId: serviceId);
        return builder;
    }

    /// <summary>
    /// Register an InMemory <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorSearch{TRecord}"/> with the specified service ID.
    /// </summary>
    /// <typeparam name="TKey">The type of the key.</typeparam>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="builder">The builder to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddInMemoryVectorStoreRecordCollection<TKey, TRecord>(
        this IKernelBuilder builder,
        string collectionName,
        InMemoryVectorStoreRecordCollectionOptions<TKey, TRecord>? options = default,
        string? serviceId = default)
        where TKey : notnull
        where TRecord : notnull
    {
        builder.Services.AddInMemoryVectorStoreRecordCollection<TKey, TRecord>(collectionName, options, serviceId);
        return builder;
    }
}
