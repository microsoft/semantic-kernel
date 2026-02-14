// Copyright (c) Microsoft. All rights reserved.

using System.Linq.Expressions;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.CosmosNoSql;

namespace CosmosNoSql.ConformanceTests.Support;

#pragma warning disable CA1812 // Internal class that is apparently never instantiated

/// <summary>
/// Adapts a <see cref="CosmosNoSqlDynamicCollection"/> (which requires <see cref="CosmosNoSqlKey"/> keys)
/// to accept plain keys (string, Guid, etc.) by wrapping them in <see cref="CosmosNoSqlKey"/>.
/// Both the adapter and inner collection use <c>object</c> as the key type; the adapter intercepts Get/Delete calls
/// to convert plain keys to <see cref="CosmosNoSqlKey"/> before forwarding.
/// </summary>
internal sealed class CosmosNoSqlDynamicCollectionAdapter(
    VectorStoreCollection<object, Dictionary<string, object?>> inner)
    : VectorStoreCollection<object, Dictionary<string, object?>>
{
    public override string Name => inner.Name;

    public override Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
        => inner.CollectionExistsAsync(cancellationToken);

    public override Task EnsureCollectionExistsAsync(CancellationToken cancellationToken = default)
        => inner.EnsureCollectionExistsAsync(cancellationToken);

    public override Task EnsureCollectionDeletedAsync(CancellationToken cancellationToken = default)
        => inner.EnsureCollectionDeletedAsync(cancellationToken);

    public override Task<Dictionary<string, object?>?> GetAsync(object key, RecordRetrievalOptions? options = null, CancellationToken cancellationToken = default)
        => key is null
            ? throw new ArgumentNullException(nameof(key))
            : inner.GetAsync(ConvertKey(key), options, cancellationToken);

    public override IAsyncEnumerable<Dictionary<string, object?>> GetAsync(IEnumerable<object> keys, RecordRetrievalOptions? options = null, CancellationToken cancellationToken = default)
        => keys is null
            ? throw new ArgumentNullException(nameof(keys))
            : inner.GetAsync(keys.Select(ConvertKey), options, cancellationToken);

    public override IAsyncEnumerable<Dictionary<string, object?>> GetAsync(
        Expression<Func<Dictionary<string, object?>, bool>> filter,
        int top,
        FilteredRecordRetrievalOptions<Dictionary<string, object?>>? options = null,
        CancellationToken cancellationToken = default)
        => inner.GetAsync(filter, top, options, cancellationToken);

    public override Task UpsertAsync(Dictionary<string, object?> record, CancellationToken cancellationToken = default)
        => inner.UpsertAsync(record, cancellationToken);

    public override Task UpsertAsync(IEnumerable<Dictionary<string, object?>> records, CancellationToken cancellationToken = default)
        => inner.UpsertAsync(records, cancellationToken);

    public override Task DeleteAsync(object key, CancellationToken cancellationToken = default)
        => key is null
            ? throw new ArgumentNullException(nameof(key))
            : inner.DeleteAsync(ConvertKey(key), cancellationToken);

    public override Task DeleteAsync(IEnumerable<object> keys, CancellationToken cancellationToken = default)
        => keys is null
            ? throw new ArgumentNullException(nameof(keys))
            : inner.DeleteAsync(keys.Select(ConvertKey), cancellationToken);

    public override IAsyncEnumerable<VectorSearchResult<Dictionary<string, object?>>> SearchAsync<TInput>(
        TInput searchValue,
        int top,
        VectorSearchOptions<Dictionary<string, object?>>? options = null,
        CancellationToken cancellationToken = default)
        => inner.SearchAsync(searchValue, top, options, cancellationToken);

    public override object? GetService(Type serviceType, object? serviceKey = null)
        => inner.GetService(serviceType, serviceKey);

    /// <summary>
    /// Wraps a plain key (e.g. string "1") in a <see cref="CosmosNoSqlKey"/> using the key's string
    /// representation as the partition key.
    /// If the key is already a <see cref="CosmosNoSqlKey"/>, returns it unchanged (boxed).
    /// </summary>
    private static object ConvertKey(object key)
    {
        if (key is CosmosNoSqlKey)
        {
            return key;
        }

        // Wrap keys using their string representation
        var keyString = key.ToString() ?? string.Empty;
        return new CosmosNoSqlKey(keyString, keyString);
    }
}
