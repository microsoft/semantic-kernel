// Copyright (c) Microsoft. All rights reserved.

using System;
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
public class LoggingVectorStoreRecordCollection<TKey, TRecord> : IVectorStoreRecordCollection<TKey, TRecord> where TKey : notnull
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
    {
        Verify.NotNull(innerCollection);
        Verify.NotNull(logger);

        this._innerCollection = innerCollection;
        this._logger = logger;
    }

    /// <inheritdoc/>
    [Obsolete("Use GetService(typeof(VectorStoreRecordCollectionMetadata)) to get an information about vector store record collection.")]
    public string CollectionName => this._innerCollection.CollectionName;

    /// <inheritdoc/>
    public Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        return LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(CollectionExistsAsync),
            () => this._innerCollection.CollectionExistsAsync(cancellationToken));
    }

    /// <inheritdoc/>
    public Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        return LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(CreateCollectionAsync),
            () => this._innerCollection.CreateCollectionAsync(cancellationToken));
    }

    /// <inheritdoc/>
    public Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default)
    {
        return LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(CreateCollectionIfNotExistsAsync),
            () => this._innerCollection.CreateCollectionIfNotExistsAsync(cancellationToken));
    }

    /// <inheritdoc/>
    public Task DeleteAsync(TKey key, CancellationToken cancellationToken = default)
    {
        return LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(DeleteAsync),
            () => this._innerCollection.DeleteAsync(key, cancellationToken));
    }

    /// <inheritdoc/>
    public Task DeleteBatchAsync(IEnumerable<TKey> keys, CancellationToken cancellationToken = default)
    {
        return LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(DeleteBatchAsync),
            () => this._innerCollection.DeleteBatchAsync(keys, cancellationToken));
    }

    /// <inheritdoc/>
    public Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
    {
        return LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(DeleteCollectionAsync),
            () => this._innerCollection.DeleteCollectionAsync(cancellationToken));
    }

    /// <inheritdoc/>
    public Task<TRecord?> GetAsync(TKey key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        return LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(GetAsync),
            () => this._innerCollection.GetAsync(key, options, cancellationToken));
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<TKey> keys, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        return LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(GetBatchAsync),
            () => this._innerCollection.GetBatchAsync(keys, options, cancellationToken),
            cancellationToken);
    }

    /// <inheritdoc/>
    public object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is null && serviceType.IsInstanceOfType(this) ? this :
            this._innerCollection.GetService(serviceType, serviceKey);
    }

    /// <inheritdoc/>
    public Task<TKey> UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        return LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(UpsertAsync),
            () => this._innerCollection.UpsertAsync(record, cancellationToken));
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<TKey> UpsertBatchAsync(IEnumerable<TRecord> records, CancellationToken cancellationToken = default)
    {
        return LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(UpsertBatchAsync),
            () => this._innerCollection.UpsertBatchAsync(records, cancellationToken),
            cancellationToken);
    }

    /// <inheritdoc/>
    public Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        return LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(VectorizedSearchAsync),
            () => this._innerCollection.VectorizedSearchAsync(vector, options, cancellationToken));
    }
}
