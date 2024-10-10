// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// A schema aware interface for managing a named collection of records in a vector store and for creating or deleting the collection itself.
/// </summary>
/// <typeparam name="TKey">The data type of the record key.</typeparam>
/// <typeparam name="TRecord">The record data model to use for adding, updating and retrieving data from the store.</typeparam>
[Experimental("SKEXP0001")]
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public interface IVectorStoreRecordCollection<TKey, TRecord> : IVectorizedSearch<TRecord>
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
    where TKey : notnull
    where TRecord : class
{
    /// <summary>
    /// Gets the name of the collection.
    /// </summary>
    public string CollectionName { get; }

    /// <summary>
    /// Check if the collection exists in the vector store.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns><see langword="true"/> if the collection exists, <see langword="false"/> otherwise.</returns>
    Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Create this collection in the vector store.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A <see cref="Task"/> that completes when the collection has been created.</returns>
    Task CreateCollectionAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Create this collection in the vector store if it does not already exist.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A <see cref="Task"/> that completes when the collection has been created.</returns>
    Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Delete the collection from the vector store.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A <see cref="Task"/> that completes when the collection has been deleted.</returns>
    Task DeleteCollectionAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets a record from the vector store. Does not guarantee that the collection exists.
    /// Returns null if the record is not found.
    /// </summary>
    /// <param name="key">The unique id associated with the record to get.</param>
    /// <param name="options">Optional options for retrieving the record.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The record if found, otherwise null.</returns>
    /// <exception cref="VectorStoreOperationException">Throw when the command fails to execute for any reason.</exception>
    /// <exception cref="VectorStoreRecordMappingException">Throw when mapping between the storage model and record data model fails.</exception>
    Task<TRecord?> GetAsync(TKey key, GetRecordOptions? options = default, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets a batch of records from the vector store. Does not guarantee that the collection exists.
    /// Gets will be made in a single request or in a single parallel batch depending on the available store functionality.
    /// Only found records will be returned, so the resultset may be smaller than the requested keys.
    /// Throws for any issues other than records not being found.
    /// </summary>
    /// <param name="keys">The unique ids associated with the record to get.</param>
    /// <param name="options">Optional options for retrieving the records.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The records associated with the unique keys provided.</returns>
    /// <exception cref="VectorStoreOperationException">Throw when the command fails to execute for any reason.</exception>
    /// <exception cref="VectorStoreRecordMappingException">Throw when mapping between the storage model and record data model fails.</exception>
    IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<TKey> keys, GetRecordOptions? options = default, CancellationToken cancellationToken = default);

    /// <summary>
    /// Deletes a record from the vector store. Does not guarantee that the collection exists.
    /// </summary>
    /// <param name="key">The unique id associated with the record to remove.</param>
    /// <param name="options">Optional options for removing the record.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The unique identifier for the record.</returns>
    /// <exception cref="VectorStoreOperationException">Throw when the command fails to execute for any reason other than that the record does not exit.</exception>
    Task DeleteAsync(TKey key, DeleteRecordOptions? options = default, CancellationToken cancellationToken = default);

    /// <summary>
    /// Deletes a batch of records from the vector store. Does not guarantee that the collection exists.
    /// Deletes will be made in a single request or in a single parallel batch depending on the available store functionality.
    /// If a record is not found, it will be ignored and the batch will succeed.
    /// If any record cannot be deleted for any other reason, the operation will throw. Some records may have already been deleted, while others may not, so the entire operation should be retried.
    /// </summary>
    /// <param name="keys">The unique ids associated with the records to remove.</param>
    /// <param name="options">Optional options for removing the records.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A <see cref="Task"/> that completes when the records have been deleted.</returns>
    /// <exception cref="VectorStoreOperationException">Throw when the command fails to execute for any reason other than that a record does not exist.</exception>
    Task DeleteBatchAsync(IEnumerable<TKey> keys, DeleteRecordOptions? options = default, CancellationToken cancellationToken = default);

    /// <summary>
    /// Upserts a record into the vector store. Does not guarantee that the collection exists.
    ///     If the record already exists, it will be updated.
    ///     If the record does not exist, it will be created.
    /// </summary>
    /// <param name="record">The record to upsert.</param>
    /// <param name="options">Optional options for upserting the record.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The unique identifier for the record.</returns>
    /// <exception cref="VectorStoreOperationException">Throw when the command fails to execute for any reason.</exception>
    /// <exception cref="VectorStoreRecordMappingException">Throw when mapping between the storage model and record data model fails.</exception>
    Task<TKey> UpsertAsync(TRecord record, UpsertRecordOptions? options = default, CancellationToken cancellationToken = default);

    /// <summary>
    /// Upserts a group of records into the vector store. Does not guarantee that the collection exists.
    ///     If the record already exists, it will be updated.
    ///     If the record does not exist, it will be created.
    /// Upserts will be made in a single request or in a single parallel batch depending on the available store functionality.
    /// </summary>
    /// <param name="records">The records to upsert.</param>
    /// <param name="options">Optional options for upserting the records.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The unique identifiers for the records.</returns>
    /// <exception cref="VectorStoreOperationException">Throw when the command fails to execute for any reason.</exception>
    /// <exception cref="VectorStoreRecordMappingException">Throw when mapping between the storage model and record data model fails.</exception>
    IAsyncEnumerable<TKey> UpsertBatchAsync(IEnumerable<TRecord> records, UpsertRecordOptions? options = default, CancellationToken cancellationToken = default);
}
