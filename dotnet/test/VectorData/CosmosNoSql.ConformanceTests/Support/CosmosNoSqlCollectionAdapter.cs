// Copyright (c) Microsoft. All rights reserved.

using System.Linq.Expressions;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.CosmosNoSql;

namespace CosmosNoSql.ConformanceTests.Support;

#pragma warning disable CA1812 // Internal class that is apparently never instantiated

/// <summary>
/// Adapts a <see cref="VectorStoreCollection{TKey, TRecord}"/> with <see cref="CosmosNoSqlKey"/> keys
/// to a <see cref="VectorStoreCollection{TKey, TRecord}"/> with simple string keys.
/// This allows Cosmos conformance tests to use simple key types (string, etc.) while still
/// using the underlying Cosmos collection with composite keys.
/// </summary>
internal sealed class CosmosNoSqlCollectionAdapter<TDocumentId, TRecord>(
    VectorStoreCollection<CosmosNoSqlKey, TRecord> inner)
    : VectorStoreCollection<TDocumentId, TRecord>,
      IKeywordHybridSearchable<TRecord>
    where TDocumentId : notnull
    where TRecord : class
{
    public override string Name => inner.Name;

    public override Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
        => inner.CollectionExistsAsync(cancellationToken);

    public override Task EnsureCollectionExistsAsync(CancellationToken cancellationToken = default)
        => inner.EnsureCollectionExistsAsync(cancellationToken);

    public override Task EnsureCollectionDeletedAsync(CancellationToken cancellationToken = default)
        => inner.EnsureCollectionDeletedAsync(cancellationToken);

    public override Task<TRecord?> GetAsync(TDocumentId key, RecordRetrievalOptions? options = null, CancellationToken cancellationToken = default)
        => key is null
            ? throw new ArgumentNullException(nameof(key))
            : inner.GetAsync(ConvertKey(key), options, cancellationToken);

    public override IAsyncEnumerable<TRecord> GetAsync(IEnumerable<TDocumentId> keys, RecordRetrievalOptions? options = null, CancellationToken cancellationToken = default)
        => keys is null
            ? throw new ArgumentNullException(nameof(keys))
            : inner.GetAsync(ConvertKeys(keys), options, cancellationToken);

    public override IAsyncEnumerable<TRecord> GetAsync(
        Expression<Func<TRecord, bool>> filter,
        int top,
        FilteredRecordRetrievalOptions<TRecord>? options = null,
        CancellationToken cancellationToken = default)
        => inner.GetAsync(filter, top, options, cancellationToken);

    public override Task UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
        => inner.UpsertAsync(record, cancellationToken);

    public override Task UpsertAsync(IEnumerable<TRecord> records, CancellationToken cancellationToken = default)
        => inner.UpsertAsync(records, cancellationToken);

    public override Task DeleteAsync(TDocumentId key, CancellationToken cancellationToken = default)
        => key is null
            ? throw new ArgumentNullException(nameof(key))
            : inner.DeleteAsync(ConvertKey(key), cancellationToken);

    public override Task DeleteAsync(IEnumerable<TDocumentId> keys, CancellationToken cancellationToken = default)
        => keys is null
            ? throw new ArgumentNullException(nameof(keys))
            : inner.DeleteAsync(ConvertKeys(keys), cancellationToken);

    public override IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TInput>(
        TInput searchValue,
        int top,
        VectorSearchOptions<TRecord>? options = null,
        CancellationToken cancellationToken = default)
        => inner.SearchAsync(searchValue, top, options, cancellationToken);

    public IAsyncEnumerable<VectorSearchResult<TRecord>> HybridSearchAsync<TInput>(
        TInput searchValue,
        ICollection<string> keywords,
        int top,
        HybridSearchOptions<TRecord>? options = default,
        CancellationToken cancellationToken = default)
        where TInput : notnull
        => ((IKeywordHybridSearchable<TRecord>)inner).HybridSearchAsync(searchValue, keywords, top, options, cancellationToken);

    public override object? GetService(Type serviceType, object? serviceKey = null)
        => inner.GetService(serviceType, serviceKey);

    // For tests, use the document ID as the partition key
    private static CosmosNoSqlKey ConvertKey(TDocumentId documentId)
        => documentId switch
        {
            string s => new(s, s),
            Guid g => new(g, g),
            _ => throw new InvalidOperationException()
        };

    private static IEnumerable<CosmosNoSqlKey> ConvertKeys(IEnumerable<TDocumentId> keys)
    {
        foreach (var key in keys)
        {
            yield return ConvertKey(key);
        }
    }
}
