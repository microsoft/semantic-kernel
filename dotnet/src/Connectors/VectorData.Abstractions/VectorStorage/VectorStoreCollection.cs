// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq.Expressions;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Represents a named collection of records in a vector store, and can be used to search and manage records, and to create or delete the collection itself.
/// </summary>
/// <typeparam name="TKey">The data type of the record key.</typeparam>
/// <typeparam name="TRecord">The record data model to use for adding, updating, and retrieving data from the store.</typeparam>
/// <remarks>
/// <para>Unless otherwise documented, implementations of this abstract base class can be expected to be thread-safe, and can be used concurrently from multiple threads.</para>
/// </remarks>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix (Collection)
public abstract class VectorStoreCollection<TKey, TRecord> : IVectorSearchable<TRecord>, IDisposable
#pragma warning restore CA1711
    where TKey : notnull
    where TRecord : class
{
    /// <summary>
    /// Gets the name of the collection.
    /// </summary>
    public abstract string Name { get; }

    /// <summary>
    /// Checks if the collection exists in the vector store.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns><see langword="true"/> if the collection exists, <see langword="false"/> otherwise.</returns>
    public abstract Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Creates this collection in the vector store if it doesn't already exist.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A <see cref="Task"/> that completes when the collection has been created.</returns>
    public abstract Task EnsureCollectionExistsAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Deletes the collection from the vector store if it exists.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A <see cref="Task"/> that completes when the collection has been deleted.</returns>
    public abstract Task EnsureCollectionDeletedAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets a record from the vector store. Does not guarantee that the collection exists.
    /// Returns null if the record is not found.
    /// </summary>
    /// <param name="key">The unique ID associated with the record to get.</param>
    /// <param name="options">Optional options for retrieving the record.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The record if found, otherwise null.</returns>
    /// <exception cref="VectorStoreException">The command fails to execute for any reason.</exception>
    public abstract Task<TRecord?> GetAsync(TKey key, RecordRetrievalOptions? options = default, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets a batch of records from the vector store. Does not guarantee that the collection exists.
    /// </summary>
    /// <param name="keys">The unique IDs associated with the record to get.</param>
    /// <param name="options">Optional options for retrieving the records.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The records associated with the specified unique keys.</returns>
    /// <remarks>
    /// <para>
    /// The exact method of retrieval is implementation-specific and can vary based on database support.
    /// The default implementation of this method retrieves the records one after the other, but implementations which supporting batching can override to provide a more efficient implementation.
    /// </para>
    /// <para>
    /// Only found records are returned, so the result set might be smaller than the requested keys.
    /// </para>
    /// <para>
    /// This method throws for any issues other than records not being found.
    /// </para>
    /// </remarks>
    /// <exception cref="VectorStoreException">The command fails to execute for any reason.</exception>
    public virtual async IAsyncEnumerable<TRecord> GetAsync(IEnumerable<TKey> keys, RecordRetrievalOptions? options = default, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        foreach (var key in keys)
        {
            var record = await this.GetAsync(key, options, cancellationToken).ConfigureAwait(false);

            if (record is not null)
            {
                yield return record;
            }
        }
    }

    /// <summary>
    /// Deletes a record from the vector store. Does not guarantee that the collection exists.
    /// </summary>
    /// <param name="key">The unique ID associated with the record to remove.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The unique identifier for the record.</returns>
    /// <exception cref="VectorStoreException">The command fails to execute for any reason other than that the record does not exist.</exception>
    public abstract Task DeleteAsync(TKey key, CancellationToken cancellationToken = default);

    /// <summary>
    /// Deletes a batch of records from the vector store. Does not guarantee that the collection exists.
    /// </summary>
    /// <param name="keys">The unique IDs associated with the records to remove.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A <see cref="Task"/> that completes when the records have been deleted.</returns>
    /// <remarks>
    /// <para>
    /// The exact method of deleting is implementation-specific and can vary based on database support.
    /// The default implementation of this method deletes the records one after the other, but implementations which supporting batching can override to provide a more efficient implementation.
    /// </para>
    /// <para>
    /// If a record isn't found, it is ignored and the batch succeeds.
    /// If any record can't be deleted for any other reason, the operation throws. Some records might have already been deleted while others might not have, so the entire operation should be retried.
    /// </para>
    /// </remarks>
    /// <exception cref="VectorStoreException">The command fails to execute for any reason other than that a record does not exist.</exception>
    public virtual async Task DeleteAsync(IEnumerable<TKey> keys, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        foreach (var key in keys)
        {
            await this.DeleteAsync(key, cancellationToken).ConfigureAwait(false);
        }
    }

    /// <summary>
    /// Upserts a record into the vector store. Does not guarantee that the collection exists.
    ///     If the record already exists, it is updated.
    ///     If the record does not exist, it is created.
    /// </summary>
    /// <param name="record">The record to upsert.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <exception cref="VectorStoreException">The command fails to execute for any reason.</exception>
    public abstract Task UpsertAsync(TRecord record, CancellationToken cancellationToken = default);

    /// <summary>
    /// Upserts a batch of records into the vector store. Does not guarantee that the collection exists.
    ///     If the record already exists, it is updated.
    ///     If the record does not exist, it is created.
    /// </summary>
    /// <param name="records">The records to upsert.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <remarks>
    /// <para>
    /// The exact method of upserting the batch is implementation-specific and can vary based on database support.
    /// </para>
    /// <para>
    /// Similarly, the error behavior can vary across databases: where possible, the batch should be upserted atomically, so that any errors cause the entire batch to be rolled
    /// back. Where not supported, some records might be upserted while others are not. If key properties are set by the user, then the entire upsert operation is idempotent,
    /// and can simply be retried again if an error occurs. However, if store-generated keys are in use, the upsert operation is no longer idempotent; in that case, if the
    /// database doesn't guarantee atomicity, retrying could cause duplicate records to be created.
    /// </para>
    /// <para>
    /// Implementations of <see cref="VectorStoreCollection{TKey,TRecord}"/> should implement this method in a way which performs embedding generation once for the batch, rather than
    /// generating an embedding for each record separately. This is why a default implementation that calls <see cref="UpsertAsync(TRecord, CancellationToken)"/> is not provided.
    /// </para>
    /// </remarks>
    /// <exception cref="VectorStoreException">The command fails to execute for any reason.</exception>
    public abstract Task UpsertAsync(IEnumerable<TRecord> records, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets matching records from the vector store. Does not guarantee that the collection exists.
    /// </summary>
    /// <param name="filter">The predicate to filter the records.</param>
    /// <param name="top">The maximum number of results to return.</param>
    /// <param name="options">Options for retrieving the records.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The records that match the given predicate.</returns>
    /// <exception cref="VectorStoreException">The command fails to execute for any reason.</exception>
    public abstract IAsyncEnumerable<TRecord> GetAsync(Expression<Func<TRecord, bool>> filter, int top, FilteredRecordRetrievalOptions<TRecord>? options = null, CancellationToken cancellationToken = default);

    /// <inheritdoc />
    public abstract IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TInput>(TInput searchValue, int top, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
        where TInput : notnull;

    /// <inheritdoc />
    public abstract object? GetService(Type serviceType, object? serviceKey = null);

    /// <summary>
    /// Disposes the <see cref="VectorStoreCollection{TKey, TRecord}"/> and releases any resources it holds.
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
