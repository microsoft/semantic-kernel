// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register <see cref="ITextSearch"/> for use with <see cref="KernelBuilder"/>.
/// </summary>
public static class TextSearchKernelBuilderExtensions
{
    /// <summary>
    /// Register an <see cref="ITextSearch"/> instance with the specified service ID.
    /// </summary>
    /// <param name="builder">The builder to register the <see cref="ITextSearch"/> on.</param>
    /// <param name="textSearch">Instance of <see cref="ITextSearch"/> to register.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    public static IKernelBuilder AddTextSearch(
        this IKernelBuilder builder,
        ITextSearch textSearch,
        string? serviceId = default)
    {
        builder.Services.AddTextSearch(textSearch, serviceId);
        return builder;
    }

    /// <summary>
    /// Register an <see cref="IVectorizableTextSearch{TRecord}"/> instance with the specified service ID.
    /// </summary>
    /// <param name="builder">The builder to register the <see cref="IVectorizableTextSearch{TRecord}"/> on.</param>
    /// <param name="vectorTextSearch">Instance of <see cref="IVectorizableTextSearch{TRecord}"/> to register.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    public static IKernelBuilder AddVectorStoreTextSearch<TRecord>(
        this IKernelBuilder builder,
        VectorStoreTextSearch<TRecord> vectorTextSearch,
        string? serviceId = default)
        where TRecord : class
    {
        builder.Services.AddVectorStoreTextSearch(vectorTextSearch, serviceId);
        return builder;
    }

    /// <summary>
    /// Register a <see cref="VectorStoreTextSearch{TRecord}"/> instance with the specified service ID.
    /// </summary>
    /// <param name="builder">The builder to register the <see cref="VectorStoreTextSearch{TRecord}"/> on.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    public static IKernelBuilder AddVectorStoreTextSearch<TRecord>(
        this IKernelBuilder builder,
        string? serviceId = default)
        where TRecord : class
    {
        builder.Services.AddVectorStoreTextSearch<TRecord>(serviceId);
        return builder;
    }
}
