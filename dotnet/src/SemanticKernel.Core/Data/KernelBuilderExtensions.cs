// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
using Microsoft.Extensions.VectorData;
>>>>>>> upstream/main
=======
<<<<<<< Updated upstream
>>>>>>> Stashed changes
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel;
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel;
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel;
=======

namespace Microsoft.SemanticKernel.Data;
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head

/// <summary>
/// Extension methods to register Data services on the <see cref="IKernelBuilder"/>.
/// </summary>
[Experimental("SKEXP0001")]
public static class KernelBuilderExtensions
{
    /// <summary>
    /// Register a Volatile <see cref="IVectorStore"/> with the specified service ID.
    /// </summary>
    /// <param name="builder">The builder to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The kernel builder.</returns>
    [Obsolete("This has been replaced by the Microsoft.SemanticKernel.Connectors.InMemory nuget package.")]
    public static IKernelBuilder AddVolatileVectorStore(this IKernelBuilder builder, string? serviceId = default)
    {
        builder.Services.AddVolatileVectorStore(serviceId);
        return builder;
    }
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div

    /// <summary>
    /// Register a <see cref="VectorStoreTextSearch{TRecord}"/> instance with the specified service ID.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> to register the <see cref="ITextSearch"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="stringMapper"><see cref="ITextSearchStringMapper" /> instance that can map a TRecord to a <see cref="string"/></param>
    /// <param name="resultMapper"><see cref="ITextSearchResultMapper" /> instance that can map a TRecord to a <see cref="TextSearchResult"/></param>
    /// <param name="options">Options used to construct an instance of <see cref="VectorStoreTextSearch{TRecord}"/></param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
<<<<<<< main
=======
    [Obsolete("This has been replaced by the Microsoft.SemanticKernel.Connectors.InMemory nuget package.")]
>>>>>>> upstream/main
    public static IKernelBuilder AddVolatileVectorStoreTextSearch<TKey, TRecord>(
        this IKernelBuilder builder,
        string collectionName,
        ITextSearchStringMapper? stringMapper = null,
        ITextSearchResultMapper? resultMapper = null,
        VectorStoreTextSearchOptions? options = null,
        string? serviceId = default)
        where TKey : notnull
    {
        builder.Services.AddVolatileVectorStoreTextSearch<TKey, TRecord>(collectionName, stringMapper, resultMapper, options, serviceId);
        return builder;
    }

    /// <summary>
    /// Register a <see cref="VectorStoreTextSearch{TRecord}"/> instance with the specified service ID.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> to register the <see cref="ITextSearch"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="stringMapper"><see cref="MapFromResultToString" /> delegate that can map a TRecord to a <see cref="string"/></param>
    /// <param name="resultMapper"><see cref="MapFromResultToTextSearchResult" /> delegate that can map a TRecord to a <see cref="TextSearchResult"/></param>
    /// <param name="options">Options used to construct an instance of <see cref="VectorStoreTextSearch{TRecord}"/></param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
<<<<<<< main
=======
    [Obsolete("This has been replaced by the Microsoft.SemanticKernel.Connectors.InMemory nuget package.")]
>>>>>>> upstream/main
    public static IKernelBuilder AddVolatileVectorStoreTextSearch<TKey, TRecord>(
        this IKernelBuilder builder,
        string collectionName,
        MapFromResultToString? stringMapper = null,
        MapFromResultToTextSearchResult? resultMapper = null,
        VectorStoreTextSearchOptions? options = null,
        string? serviceId = default)
        where TKey : notnull
    {
        builder.AddVolatileVectorStoreTextSearch<TKey, TRecord>(
            collectionName,
            stringMapper is not null ? new TextSearchStringMapper(stringMapper) : null,
            resultMapper is not null ? new TextSearchResultMapper(resultMapper) : null,
            options,
            serviceId);
        return builder;
    }
<<<<<<< main
<<<<<<< main
=======
<<<<<<< div
=======
>>>>>>> div
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
}
