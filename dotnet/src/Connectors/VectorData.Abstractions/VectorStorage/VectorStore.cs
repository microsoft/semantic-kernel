// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Represents a vector store that contains collections of records.
/// </summary>
/// <remarks>
/// <para>This type can be used with collections of any schema type, but requires you to provide schema information when getting a collection.</para>
/// <para>Unless otherwise documented, implementations of this abstract base class can be expected to be thread-safe, and can be used concurrently from multiple threads.</para>
/// </remarks>
public abstract class VectorStore : IDisposable
{
    /// <summary>
    /// Gets a collection from the vector store.
    /// </summary>
    /// <typeparam name="TKey">The data type of the record key.</typeparam>
    /// <typeparam name="TRecord">The record data model to use for adding, updating, and retrieving data from the collection.</typeparam>
    /// <param name="name">The name of the collection.</param>
    /// <param name="definition">The schema of the record type.</param>
    /// <returns>A new <see cref="VectorStoreCollection{TKey, TRecord}"/> instance for managing the records in the collection.</returns>
    /// <remarks>
    /// To successfully request a collection, either <typeparamref name="TRecord"/> must be annotated with attributes that define the schema of
    /// the record type, or <paramref name="definition"/> must be provided.
    /// </remarks>
    /// <seealso cref="VectorStoreKeyAttribute"/>
    /// <seealso cref="VectorStoreDataAttribute"/>
    /// <seealso cref="VectorStoreVectorAttribute"/>
    [RequiresDynamicCode("This API is not compatible with NativeAOT. For dynamic mapping via Dictionary<string, object?>, use GetCollectionDynamic() instead.")]
    [RequiresUnreferencedCode("This API is not compatible with trimming. For dynamic mapping via Dictionary<string, object?>, use GetCollectionDynamic() instead.")]
    public abstract VectorStoreCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreCollectionDefinition? definition = null)
        where TKey : notnull
        where TRecord : class;

    /// <summary>
    /// Gets a collection from the vector store, using dynamic mapping; the record type is represented as a <see cref="Dictionary{TKey, TValue}"/>.
    /// </summary>
    /// <param name="name">The name of the collection.</param>
    /// <param name="definition">The schema of the record type.</param>
    /// <returns>A new <see cref="VectorStoreCollection{TKey, TRecord}"/> instance for managing the records in the collection.</returns>
    public abstract VectorStoreCollection<object, Dictionary<string, object?>> GetDynamicCollection(string name, VectorStoreCollectionDefinition definition);

    /// <summary>
    /// Retrieves the names of all the collections in the vector store.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The list of names of all the collections in the vector store.</returns>
    public abstract IAsyncEnumerable<string> ListCollectionNamesAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Checks if the collection exists in the vector store.
    /// </summary>
    /// <param name="name">The name of the collection.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns><see langword="true"/> if the collection exists, <see langword="false"/> otherwise.</returns>
    public abstract Task<bool> CollectionExistsAsync(string name, CancellationToken cancellationToken = default);

    /// <summary>
    /// Deletes the collection from the vector store.
    /// </summary>
    /// <param name="name">The name of the collection to delete.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A <see cref="Task"/> that completes when the collection has been deleted.</returns>
    public abstract Task EnsureCollectionDeletedAsync(string name, CancellationToken cancellationToken = default);

    /// <summary>Asks the <see cref="VectorStore"/> for an object of the specified type <paramref name="serviceType"/>.</summary>
    /// <param name="serviceType">The type of object being requested.</param>
    /// <param name="serviceKey">An optional key that can be used to help identify the target service.</param>
    /// <returns>The found object, otherwise <see langword="null"/>.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="serviceType"/> is <see langword="null"/>.</exception>
    /// <remarks>
    /// The purpose of this method is to allow for the retrieval of strongly typed services that might be provided by the <see cref="VectorStore"/>,
    /// including itself or any services it might be wrapping. For example, to access the <see cref="VectorStoreMetadata"/> for the instance,
    /// <see cref="GetService"/> can be used to request it.
    /// </remarks>
    public abstract object? GetService(Type serviceType, object? serviceKey = null);

    /// <summary>
    /// Disposes the <see cref="VectorStore"/> and releases any resources it holds.
    /// </summary>
    /// <param name="disposing"><see langword="true"/> if called from <see cref="Dispose()"/>; <see langword="false"/> if called from a finalizer.</param>
    protected virtual void Dispose(bool disposing)
    {
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        this.Dispose(disposing: true);
        GC.SuppressFinalize(this);
    }
}
