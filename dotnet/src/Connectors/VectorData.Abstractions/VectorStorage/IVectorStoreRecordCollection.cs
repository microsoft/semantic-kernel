// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines a schema-aware interface for managing a named collection of records in a vector store and for creating or deleting the collection itself.
/// </summary>
/// <typeparam name="TKey">The data type of the record key.</typeparam>
/// <typeparam name="TRecord">The record data model to use for adding, updating, and retrieving data from the store.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public interface IVectorStoreRecordCollection<TKey, TRecord> : IVectorizedSearch<TRecord>
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
    where TKey : notnull
{
    /// <summary>
    /// Gets the name of the collection.
    /// </summary>
    string CollectionName { get; }

    /// <summary>
    /// Checks if the collection exists in the vector store.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns><see langword="true"/> if the collection exists, <see langword="false"/> otherwise.</returns>
    Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Creates this collection in the vector store.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A <see cref="Task"/> that completes when the collection has been created.</returns>
    Task CreateCollectionAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Creates this collection in the vector store if it doesn't already exist.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A <see cref="Task"/> that completes when the collection has been created.</returns>
    Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Deletes the collection from the vector store.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A <see cref="Task"/> that completes when the collection has been deleted.</returns>
    Task DeleteCollectionAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets a record from the vector store. Does not guarantee that the collection exists.
    /// Returns null if the record is not found.
    /// </summary>
    /// <param name="key">The unique ID associated with the record to get.</param>
    /// <param name="options">Optional options for retrieving the record.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The record if found, otherwise null.</returns>
    /// <exception cref="VectorStoreOperationException">The command fails to execute for any reason.</exception>
    /// <exception cref="VectorStoreRecordMappingException">The mapping between the storage model and record data model fails.</exception>
    Task<TRecord?> GetAsync(TKey key, GetRecordOptions? options = default, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets a batch of records from the vector store. Does not guarantee that the collection exists.
    /// </summary>
    /// <param name="keys">The unique IDs associated with the record to get.</param>
    /// <param name="options">Optional options for retrieving the records.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The records associated with the specified unique keys.</returns>
    /// <remarks>
    /// Gets are made in a single request or in a single parallel batch depending on the available store functionality.
    /// Only found records are returned, so the result set might be smaller than the requested keys.
    /// This method throws for any issues other than records not being found.
    /// </remarks>
    /// <exception cref="VectorStoreOperationException">The command fails to execute for any reason.</exception>
    /// <exception cref="VectorStoreRecordMappingException">The mapping between the storage model and record data model fails.</exception>
    IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<TKey> keys, GetRecordOptions? options = default, CancellationToken cancellationToken = default);

    /// <summary>
    /// Deletes a record from the vector store. Does not guarantee that the collection exists.
    /// </summary>
    /// <param name="key">The unique ID associated with the record to remove.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The unique identifier for the record.</returns>
    /// <exception cref="VectorStoreOperationException">The command fails to execute for any reason other than that the record does not exist.</exception>
    Task DeleteAsync(TKey key, CancellationToken cancellationToken = default);

    /// <summary>
    /// Deletes a batch of records from the vector store. Does not guarantee that the collection exists.
    /// </summary>
    /// <param name="keys">The unique IDs associated with the records to remove.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A <see cref="Task"/> that completes when the records have been deleted.</returns>
    /// <remarks>
    /// Deletes are made in a single request or in a single parallel batch, depending on the available store functionality.
    /// If a record isn't found, it is ignored and the batch succeeds.
    /// If any record can't be deleted for any other reason, the operation throws. Some records might have already been deleted while others might not have, so the entire operation should be retried.
    /// </remarks>
    /// <exception cref="VectorStoreOperationException">The command fails to execute for any reason other than that a record does not exist.</exception>
    Task DeleteBatchAsync(IEnumerable<TKey> keys, CancellationToken cancellationToken = default);

    /// <summary>
    /// Upserts a record into the vector store. Does not guarantee that the collection exists.
    ///     If the record already exists, it is updated.
    ///     If the record does not exist, it is created.
    /// </summary>
    /// <param name="record">The record to upsert.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The unique identifier for the record.</returns>
    /// <exception cref="VectorStoreOperationException">The command fails to execute for any reason.</exception>
    /// <exception cref="VectorStoreRecordMappingException">The mapping between the storage model and record data model fails.</exception>
    Task<TKey> UpsertAsync(TRecord record, CancellationToken cancellationToken = default);

    /// <summary>
    /// Upserts a group of records into the vector store. Does not guarantee that the collection exists.
    ///     If the record already exists, it is updated.
    ///     If the record does not exist, it is created.
    /// </summary>
    /// <param name="records">The records to upsert.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The unique identifiers for the records.</returns>
    /// <remarks>
    /// Upserts are made in a single request or in a single parallel batch depending on the available store functionality.
    /// </remarks>
    /// <exception cref="VectorStoreOperationException">The command fails to execute for any reason.</exception>
    /// <exception cref="VectorStoreRecordMappingException">The mapping between the storage model and record data model fails.</exception>
    IAsyncEnumerable<TKey> UpsertBatchAsync(IEnumerable<TRecord> records, CancellationToken cancellationToken = default);
}
