// Copyright (c) Microsoft. All rights reserved.

// TODO: Commented out as part of implementing LINQ-based filtering, since MappingVectorStoreRecordCollection is no longer easy/feasible.
// TODO: The user provides an expression tree accepting a TPublicRecord, but we require an expression tree accepting a TInternalRecord.
// TODO: This is something that the user must provide, and is quite advanced.

#if DISABLED

using System.Runtime.CompilerServices;
using Microsoft.Extensions.VectorData;

namespace Memory.VectorStoreLangchainInterop;

/// <summary>
/// Decorator class that allows conversion of keys and records between public and internal representations.
/// </summary>
/// <remarks>
/// This class is useful if a vector store implementation exposes keys or records in a way that is not
/// suitable for the user of the vector store. E.g. let's say that the vector store supports Guid keys
/// but you want to work with string keys that contain Guids. This class allows you to map between the
/// public string Guids and the internal Guids.
/// </remarks>
/// <typeparam name="TPublicKey">The type of the key that the user of this class will use.</typeparam>
/// <typeparam name="TInternalKey">The type of the key that the internal collection exposes.</typeparam>
/// <typeparam name="TPublicRecord">The type of the record that the user of this class will use.</typeparam>
/// <typeparam name="TInternalRecord">The type of the record that the internal collection exposes.</typeparam>
internal sealed class MappingVectorStoreRecordCollection<TPublicKey, TInternalKey, TPublicRecord, TInternalRecord> : IVectorStoreRecordCollection<TPublicKey, TPublicRecord>
    where TPublicKey : notnull
    where TInternalKey : notnull
{
    private readonly IVectorStoreRecordCollection<TInternalKey, TInternalRecord> _collection;
    private readonly Func<TPublicKey, TInternalKey> _publicToInternalKeyMapper;
    private readonly Func<TInternalKey, TPublicKey> _internalToPublicKeyMapper;
    private readonly Func<TPublicRecord, TInternalRecord> _publicToInternalRecordMapper;
    private readonly Func<TInternalRecord, TPublicRecord> _internalToPublicRecordMapper;

    public MappingVectorStoreRecordCollection(
        IVectorStoreRecordCollection<TInternalKey, TInternalRecord> collection,
        Func<TPublicKey, TInternalKey> publicToInternalKeyMapper,
        Func<TInternalKey, TPublicKey> internalToPublicKeyMapper,
        Func<TPublicRecord, TInternalRecord> publicToInternalRecordMapper,
        Func<TInternalRecord, TPublicRecord> internalToPublicRecordMapper)
    {
        this._collection = collection;
        this._publicToInternalKeyMapper = publicToInternalKeyMapper;
        this._internalToPublicKeyMapper = internalToPublicKeyMapper;
        this._publicToInternalRecordMapper = publicToInternalRecordMapper;
        this._internalToPublicRecordMapper = internalToPublicRecordMapper;
    }

    /// <inheritdoc />
    public string CollectionName => this._collection.CollectionName;

    /// <inheritdoc />
    public Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        return this._collection.CollectionExistsAsync(cancellationToken);
    }

    /// <inheritdoc />
    public Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        return this._collection.CreateCollectionAsync(cancellationToken);
    }

    /// <inheritdoc />
    public Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default)
    {
        return this._collection.CreateCollectionIfNotExistsAsync(cancellationToken);
    }

    /// <inheritdoc />
    public Task DeleteAsync(TPublicKey key, CancellationToken cancellationToken = default)
    {
        return this._collection.DeleteAsync(this._publicToInternalKeyMapper(key), cancellationToken);
    }

    /// <inheritdoc />
    public Task DeleteBatchAsync(IEnumerable<TPublicKey> keys, CancellationToken cancellationToken = default)
    {
        return this._collection.DeleteBatchAsync(keys.Select(this._publicToInternalKeyMapper), cancellationToken);
    }

    /// <inheritdoc />
    public Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
    {
        return this._collection.DeleteCollectionAsync(cancellationToken);
    }

    /// <inheritdoc />
    public async Task<TPublicRecord?> GetAsync(TPublicKey key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        var internalRecord = await this._collection.GetAsync(this._publicToInternalKeyMapper(key), options, cancellationToken).ConfigureAwait(false);
        if (internalRecord == null)
        {
            return default;
        }

        return this._internalToPublicRecordMapper(internalRecord);
    }

    /// <inheritdoc />
    public IAsyncEnumerable<TPublicRecord> GetBatchAsync(IEnumerable<TPublicKey> keys, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        var internalRecords = this._collection.GetBatchAsync(keys.Select(this._publicToInternalKeyMapper), options, cancellationToken);
        return internalRecords.Select(this._internalToPublicRecordMapper);
    }

    /// <inheritdoc />
    public async Task<TPublicKey> UpsertAsync(TPublicRecord record, CancellationToken cancellationToken = default)
    {
        var internalRecord = this._publicToInternalRecordMapper(record);
        var internalKey = await this._collection.UpsertAsync(internalRecord, cancellationToken).ConfigureAwait(false);
        return this._internalToPublicKeyMapper(internalKey);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TPublicKey> UpsertBatchAsync(IEnumerable<TPublicRecord> records, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var internalRecords = records.Select(this._publicToInternalRecordMapper);
        var internalKeys = this._collection.UpsertBatchAsync(internalRecords, cancellationToken);
        await foreach (var internalKey in internalKeys.ConfigureAwait(false))
        {
            yield return this._internalToPublicKeyMapper(internalKey);
        }
    }

    /// <inheritdoc />
    public async Task<VectorSearchResults<TPublicRecord>> VectorizedSearchAsync<TVector>(TVector vector, VectorSearchOptions? options = null, CancellationToken cancellationToken = default)
    {
        var searchResults = await this._collection.VectorizedSearchAsync(vector, options, cancellationToken).ConfigureAwait(false);
        var publicResultRecords = searchResults.Results.Select(result => new VectorSearchResult<TPublicRecord>(this._internalToPublicRecordMapper(result.Record), result.Score));

        return new VectorSearchResults<TPublicRecord>(publicResultRecords)
        {
            TotalCount = searchResults.TotalCount,
            Metadata = searchResults.Metadata,
        };
    }
}

#endif
