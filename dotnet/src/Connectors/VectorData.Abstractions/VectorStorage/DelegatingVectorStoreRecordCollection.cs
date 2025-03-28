// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Provides an optional base class for an <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> that passes through calls to another instance.
/// </summary>
/// <remarks>
/// This is recommended as a base type when building services that can be chained around an underlying <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.
/// The default implementation simply passes each call to the inner collection instance.
/// </remarks>
/// <typeparam name="TKey">The data type of the record key.</typeparam>
/// <typeparam name="TRecord">The record data model to use for adding, updating, and retrieving data from the store.</typeparam>
[Experimental("SKEXP0020")]
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public class DelegatingVectorStoreRecordCollection<TKey, TRecord> : IVectorStoreRecordCollection<TKey, TRecord>
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
    where TKey : notnull
{
    /// <summary>Gets the inner <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</summary>
    protected IVectorStoreRecordCollection<TKey, TRecord> InnerCollection { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="DelegatingVectorStoreRecordCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="innerCollection">The wrapped collection instance.</param>
    protected DelegatingVectorStoreRecordCollection(IVectorStoreRecordCollection<TKey, TRecord> innerCollection)
    {
        this.InnerCollection = innerCollection ?? throw new ArgumentNullException(nameof(innerCollection));
    }

    /// <inheritdoc />
    public virtual string CollectionName => this.InnerCollection.CollectionName;

    /// <inheritdoc />
    public virtual Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        return this.InnerCollection.CollectionExistsAsync(cancellationToken);
    }

    /// <inheritdoc />
    public virtual Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        return this.InnerCollection.CreateCollectionAsync(cancellationToken);
    }

    /// <inheritdoc />
    public virtual Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default)
    {
        return this.InnerCollection.CreateCollectionIfNotExistsAsync(cancellationToken);
    }

    /// <inheritdoc />
    public virtual Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
    {
        return this.InnerCollection.DeleteCollectionAsync(cancellationToken);
    }

    /// <inheritdoc />
    public virtual Task<TRecord?> GetAsync(TKey key, GetRecordOptions? options = default, CancellationToken cancellationToken = default)
    {
        return this.InnerCollection.GetAsync(key, options, cancellationToken);
    }

    /// <inheritdoc />
    public virtual IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<TKey> keys, GetRecordOptions? options = default, CancellationToken cancellationToken = default)
    {
        return this.InnerCollection.GetBatchAsync(keys, options, cancellationToken);
    }

    /// <inheritdoc />
    public virtual Task DeleteAsync(TKey key, CancellationToken cancellationToken = default)
    {
        return this.InnerCollection.DeleteAsync(key, cancellationToken);
    }

    /// <inheritdoc />
    public virtual Task DeleteBatchAsync(IEnumerable<TKey> keys, CancellationToken cancellationToken = default)
    {
        return this.InnerCollection.DeleteBatchAsync(keys, cancellationToken);
    }

    /// <inheritdoc />
    public virtual Task<TKey> UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        return this.InnerCollection.UpsertAsync(record, cancellationToken);
    }

    /// <inheritdoc />
    public virtual IAsyncEnumerable<TKey> UpsertBatchAsync(IEnumerable<TRecord> records, CancellationToken cancellationToken = default)
    {
        return this.InnerCollection.UpsertBatchAsync(records, cancellationToken);
    }

    /// <inheritdoc />
    public virtual Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, VectorSearchOptions<TRecord>? options = default, CancellationToken cancellationToken = default)
    {
        return this.InnerCollection.VectorizedSearchAsync(vector, options, cancellationToken);
    }
}
