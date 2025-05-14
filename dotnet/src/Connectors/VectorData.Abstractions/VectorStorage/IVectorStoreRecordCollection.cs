// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq.Expressions;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines a schema-aware interface for managing a named collection of records in a vector store and for creating or deleting the collection itself.
/// </summary>
/// <typeparam name="TKey">The data type of the record key.</typeparam>
/// <typeparam name="TRecord">The record data model to use for adding, updating, and retrieving data from the store.</typeparam>
/// <remarks>
/// <para>Unless otherwise documented, implementations of this interface can be expected to be thread-safe, and can be used concurrently from multiple threads.</para>
/// </remarks>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix (Collection)
#pragma warning disable CS0618 // IVectorizedSearch is obsolete
public interface IVectorStoreRecordCollection<TKey, TRecord> : IVectorSearch<TRecord>, IVectorizedSearch<TRecord>
#pragma warning restore CS0618 // IVectorizedSearch is obsolete
#pragma warning restore CA1711
    where TKey : notnull
    where TRecord : notnull
{
    /// <summary>
    /// Gets the name of the collection.
    /// </summary>
    string Name { get; }

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
    IAsyncEnumerable<TRecord> GetAsync(IEnumerable<TKey> keys, GetRecordOptions? options = default, CancellationToken cancellationToken = default);

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
    Task DeleteAsync(IEnumerable<TKey> keys, CancellationToken cancellationToken = default);

    /// <summary>
    /// Upserts a record into the vector store. Does not guarantee that the collection exists.
    ///     If the record already exists, it is updated.
    ///     If the record does not exist, it is created.
    /// </summary>
    /// <param name="record">The record to upsert.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The key for the records, to be used when keys are generated in the database.</returns>
    /// <exception cref="VectorStoreOperationException">The command fails to execute for any reason.</exception>
    /// <exception cref="VectorStoreRecordMappingException">The mapping between the storage model and record data model fails.</exception>
    Task<TKey> UpsertAsync(TRecord record, CancellationToken cancellationToken = default);

    /// <summary>
    /// Upserts a batch of records into the vector store. Does not guarantee that the collection exists.
    ///     If the record already exists, it is updated.
    ///     If the record does not exist, it is created.
    /// </summary>
    /// <param name="records">The records to upsert.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The keys for the records, to be used when keys are generated in the database.</returns>
    /// <remarks>
    /// <para>
    /// The exact method of upserting the batch is implementation-specific and can vary based on database support; some databases support batch upserts via a single, efficient
    /// request, while in other cases the implementation might send multiple upserts in parallel.
    /// </para>
    /// <para>
    /// Similarly, the error behavior can vary across databases: where possible, the batch will be upserted atomically, so that any errors cause the entire batch to be rolled
    /// back. Where not supported, some records may be upserted while others are not. If key properties are set by the user, then the entire upsert operation is idempotent,
    /// and can simply be retried again if an error occurs. However, if store-generated keys are in use, the upsert operation is no longer idempotent; in that case, if the
    /// database doesn't guarantee atomicity, retrying could cause duplicate records to be created.
    /// </para>
    /// </remarks>
    /// <exception cref="VectorStoreOperationException">The command fails to execute for any reason.</exception>
    /// <exception cref="VectorStoreRecordMappingException">The mapping between the storage model and record data model fails.</exception>
    Task<IReadOnlyList<TKey>> UpsertAsync(IEnumerable<TRecord> records, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets matching records from the vector store. Does not guarantee that the collection exists.
    /// </summary>
    /// <param name="filter">The predicate to filter the records.</param>
    /// <param name="top">The maximum number of results to return.</param>
    /// <param name="options">Options for retrieving the records.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The records matching given predicate.</returns>
    /// <exception cref="VectorStoreOperationException">The command fails to execute for any reason.</exception>
    /// <exception cref="VectorStoreRecordMappingException">The mapping between the storage model and record data model fails.</exception>
    IAsyncEnumerable<TRecord> GetAsync(Expression<Func<TRecord, bool>> filter, int top, GetFilteredRecordOptions<TRecord>? options = null, CancellationToken cancellationToken = default);
}
