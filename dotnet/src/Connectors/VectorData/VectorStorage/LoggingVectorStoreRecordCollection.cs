// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// A vector store record collection that logs operations to an <see cref="ILogger"/>
/// </summary>
[Experimental("SKEXP0020")]
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public class LoggingVectorStoreRecordCollection<TKey, TRecord> : DelegatingVectorStoreRecordCollection<TKey, TRecord> where TKey : notnull
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
{
    /// <summary>An <see cref="ILogger"/> instance used for all logging.</summary>
    private readonly ILogger _logger;

    /// <summary>The underlying <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</summary>
    private readonly IVectorStoreRecordCollection<TKey, TRecord> _innerCollection;

    /// <summary>
    /// Initializes a new instance of the <see cref="LoggingVectorStoreRecordCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="innerCollection">The underlying <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="logger">An <see cref="ILogger"/> instance that will be used for all logging.</param>
    public LoggingVectorStoreRecordCollection(IVectorStoreRecordCollection<TKey, TRecord> innerCollection, ILogger logger)
        : base(innerCollection)
    {
        Verify.NotNull(innerCollection);
        Verify.NotNull(logger);

        this._innerCollection = innerCollection;
        this._logger = logger;
    }

    /// <inheritdoc/>
    public override Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        return LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(CollectionExistsAsync),
            () => base.CollectionExistsAsync(cancellationToken));
    }

    /// <inheritdoc/>
    public override Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        return LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(CreateCollectionAsync),
            () => base.CreateCollectionAsync(cancellationToken));
    }

    /// <inheritdoc/>
    public override Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default)
    {
        return LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(CreateCollectionIfNotExistsAsync),
            () => base.CreateCollectionIfNotExistsAsync(cancellationToken));
    }

    /// <inheritdoc/>
    public override Task DeleteAsync(TKey key, CancellationToken cancellationToken = default)
    {
        return LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(DeleteAsync),
            () => base.DeleteAsync(key, cancellationToken));
    }

    /// <inheritdoc/>
    public override Task DeleteBatchAsync(IEnumerable<TKey> keys, CancellationToken cancellationToken = default)
    {
        return LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(DeleteBatchAsync),
            () => base.DeleteBatchAsync(keys, cancellationToken));
    }

    /// <inheritdoc/>
    public override Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
    {
        return LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(DeleteCollectionAsync),
            () => base.DeleteCollectionAsync(cancellationToken));
    }

    /// <inheritdoc/>
    public override Task<TRecord?> GetAsync(TKey key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        return LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(GetAsync),
            () => base.GetAsync(key, options, cancellationToken));
    }

    /// <inheritdoc/>
    public override IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<TKey> keys, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        return LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(GetBatchAsync),
            () => base.GetBatchAsync(keys, options, cancellationToken),
            cancellationToken);
    }

    /// <inheritdoc/>
    public override Task<TKey> UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        return LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(UpsertAsync),
            () => base.UpsertAsync(record, cancellationToken));
    }

    /// <inheritdoc/>
    public override IAsyncEnumerable<TKey> UpsertBatchAsync(IEnumerable<TRecord> records, CancellationToken cancellationToken = default)
    {
        return LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(UpsertBatchAsync),
            () => base.UpsertBatchAsync(records, cancellationToken),
            cancellationToken);
    }

    /// <inheritdoc/>
    public override Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        return LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(VectorizedSearchAsync),
            () => base.VectorizedSearchAsync(vector, options, cancellationToken));
    }
}
