// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Threading;
using Microsoft.Extensions.AI;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Contains a method for performing a hybrid search using a vector and keywords.
/// </summary>
/// <typeparam name="TRecord">The record data model to use for retrieving data from the store.</typeparam>
public interface IKeywordHybridSearchable<TRecord>
{
    /// <summary>
    /// Performs a hybrid search for records that match the given embedding and keywords, after applying the provided filters.
    /// </summary>
    /// <typeparam name="TInput">The type of the input value on which to perform the vector similarity search.</typeparam>
    /// <param name="searchValue">The value on which to perform the similarity search. See the remarks section for more details.</param>
    /// <param name="keywords">A collection of keywords to search the store with.</param>
    /// <param name="top">The maximum number of results to return.</param>
    /// <param name="options">The options that control the behavior of the search.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The records found by the hybrid search, including their result scores.</returns>
    /// <remarks>
    /// The types supported for the <paramref name="searchValue"/> vary based on the provider being used and the embedding generation configured:
    ///
    /// <list type="bullet">
    ///   <item>
    ///     A <see cref="string"/> or <see cref="DataContent"/> (for images, sound...) if an appropriate <see cref="IEmbeddingGenerator"/> has been configured that accepts that type as input.
    ///     For example, register an <see cref="IEmbeddingGenerator"/> that accepts <see cref="string"/> as input in your dependency injection container, and then pass in a
    ///     <see cref="string"/> argument to this method; the argument will be automatically passed to the <see cref="IEmbeddingGenerator"/> to generate the embedding and perform the search.
    ///     Some databases support generating embeddings at the database side. In this case, you can pass in a <see cref="string"/> or <see cref="DataContent"/> without configuring an
    ///     <see cref="IEmbeddingGenerator"/> with Microsoft.Extensions.VectorData. The provider will simply send your argument to the database as-is for embedding generation.
    ///   </item>
    ///   <item>
    ///     Arbitrary .NET types can also be passed in as long as an appropriate <see cref="IEmbeddingGenerator"/> has been configured; for example, you can create your own <see cref="IEmbeddingGenerator"/>
    ///     that accepts your own custom types as input, and uses another <see cref="IEmbeddingGenerator"/> to generate embedding from multiple properties. For .NET types beyond <see cref="string"/> and
    ///     <see cref="DataContent"/>, you must use the generic <see cref="VectorStoreVectorProperty{TInput}"/> in your record definition.
    ///   </item>
    ///   <item>
    ///     To work with embeddings directly, pass in a <see cref="ReadOnlyMemory{T}"/> or a .NET array of the appropriate type. Most providers support at least <c>ReadOnlyMemory&lt;float&gt;</c> and <c>float[]</c>,
    ///     but some support other types (for example, <c>ReadOnlyMemory&lt;Half&gt;</c>, <see cref="BitArray"/>). Some providers might also support their own custom types as well, for example, to represent sparse embeddings.
    ///     Consult your provider's documentation for supported types.
    ///   </item>
    ///   <item>
    ///     If you're using <see cref="IEmbeddingGenerator"/> directly in your code, that type returns an <see cref="Embedding"/> (for example, <c>Embedding{float}</c>),
    ///     which can also be passed in directly, as long as the provider supports the specific embedding type. However, consider registering your <see cref="IEmbeddingGenerator"/> with the provider
    ///     instead and pass in the input type (for example, <see cref="string"/>).
    ///   </item>
    /// </list>
    /// </remarks>
    IAsyncEnumerable<VectorSearchResult<TRecord>> HybridSearchAsync<TInput>(
        TInput searchValue,
        ICollection<string> keywords,
        int top,
        HybridSearchOptions<TRecord>? options = default,
        CancellationToken cancellationToken = default)
        where TInput : notnull;

    /// <summary>Asks the <see cref="IKeywordHybridSearchable{TRecord}"/> for an object of the specified type <paramref name="serviceType"/>.</summary>
    /// <param name="serviceType">The type of object being requested.</param>
    /// <param name="serviceKey">An optional key that can be used to help identify the target service.</param>
    /// <returns>The found object, otherwise <see langword="null"/>.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="serviceType"/> is <see langword="null"/>.</exception>
    /// <remarks>
    /// The purpose of this method is to allow for the retrieval of strongly typed services that might be provided by the <see cref="IKeywordHybridSearchable{TRecord}"/>,
    /// including itself or any services it might be wrapping. For example, to access the <see cref="VectorStoreCollectionMetadata"/> for the instance,
    /// <see cref="GetService"/> can be used to request it.
    /// </remarks>
    object? GetService(Type serviceType, object? serviceKey = null);
}
