// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;
using System.Text.Json;
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
public partial class LoggingVectorStoreRecordCollection<TKey, TRecord> : IVectorStoreRecordCollection<TKey, TRecord> where TKey : notnull
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
{
    /// <summary>An <see cref="ILogger"/> instance used for all logging.</summary>
    private readonly ILogger _logger;

    /// <summary>The underlying <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</summary>
    private readonly IVectorStoreRecordCollection<TKey, TRecord> _innerCollection;

    /// <summary>Gets or sets JSON serialization options to use when serializing logging data.</summary>
    public JsonSerializerOptions? JsonSerializerOptions { get; set; }

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
    public string CollectionName => this._innerCollection.CollectionName;

    /// <inheritdoc/>
    public async Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        var collectionExists = await LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(CollectionExistsAsync),
            () => this._innerCollection.CollectionExistsAsync(cancellationToken))
            .ConfigureAwait(false);

        if (this._logger.IsEnabled(LogLevel.Debug))
        {
            this.LogCollectionExistsResult(collectionExists);
        }

        return collectionExists;
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
        if (this._logger.IsEnabled(LogLevel.Trace))
        {
            this.LogDelete(LoggingExtensions.AsJson(key, this.JsonSerializerOptions));
        }

        return LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(DeleteAsync),
            () => this._innerCollection.DeleteAsync(key, cancellationToken));
    }

    /// <inheritdoc/>
    public Task DeleteBatchAsync(IEnumerable<TKey> keys, CancellationToken cancellationToken = default)
    {
        if (this._logger.IsEnabled(LogLevel.Trace))
        {
            this.LogDeleteBatch(LoggingExtensions.AsJson(keys, this.JsonSerializerOptions));
        }

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
    public async Task<TRecord?> GetAsync(TKey key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        if (this._logger.IsEnabled(LogLevel.Trace))
        {
            this.LogGet(LoggingExtensions.AsJson(key, this.JsonSerializerOptions));
        }

        var record = await LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(GetAsync),
            () => this._innerCollection.GetAsync(key, options, cancellationToken))
            .ConfigureAwait(false);

        if (this._logger.IsEnabled(LogLevel.Trace))
        {
            this.LogGetResult(LoggingExtensions.AsJson(record, this.JsonSerializerOptions));
        }

        return record;
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<TKey> keys, GetRecordOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var records = LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(GetBatchAsync),
            () => this._innerCollection.GetBatchAsync(keys, options, cancellationToken),
            cancellationToken);

        await foreach (var record in records.ConfigureAwait(false))
        {
            if (this._logger.IsEnabled(LogLevel.Trace))
            {
                this.LogGetResult(LoggingExtensions.AsJson(record, this.JsonSerializerOptions));
            }

            yield return record;
        }
    }

    /// <inheritdoc/>
    public async Task<TKey> UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        if (this._logger.IsEnabled(LogLevel.Trace))
        {
            this.LogUpsert(LoggingExtensions.AsJson(record, this.JsonSerializerOptions));
        }

        var key = await LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(UpsertAsync),
            () => this._innerCollection.UpsertAsync(record, cancellationToken))
            .ConfigureAwait(false);

        if (this._logger.IsEnabled(LogLevel.Trace))
        {
            this.LogUpsertResult(LoggingExtensions.AsJson(key, this.JsonSerializerOptions));
        }

        return key;
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<TKey> UpsertBatchAsync(IEnumerable<TRecord> records, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        if (this._logger.IsEnabled(LogLevel.Trace))
        {
            this.LogUpsertBatch(LoggingExtensions.AsJson(records, this.JsonSerializerOptions));
        }

        var keys = LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(UpsertBatchAsync),
            () => this._innerCollection.UpsertBatchAsync(records, cancellationToken),
            cancellationToken);

        await foreach (var key in keys.ConfigureAwait(false))
        {
            if (this._logger.IsEnabled(LogLevel.Trace))
            {
                this.LogUpsertResult(LoggingExtensions.AsJson(key, this.JsonSerializerOptions));
            }

            yield return key;
        }
    }

    /// <inheritdoc/>
    public Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        return LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(VectorizedSearchAsync),
            () => this._innerCollection.VectorizedSearchAsync(vector, options, cancellationToken));
    }

    #region private

    [LoggerMessage(LogLevel.Debug, "Collection exists: {CollectionExists}")]
    private partial void LogCollectionExistsResult(bool collectionExists);

    [LoggerMessage(LogLevel.Trace, "Deleting a record with key: {Key}")]
    private partial void LogDelete(string key);

    [LoggerMessage(LogLevel.Trace, "Deleting records with keys: {Keys}")]
    private partial void LogDeleteBatch(string keys);

    [LoggerMessage(LogLevel.Trace, "Getting a record with key: {Key}")]
    private partial void LogGet(string key);

    [LoggerMessage(LogLevel.Trace, "Getting records with keys: {Keys}")]
    private partial void LogGetBatch(string keys);

    [LoggerMessage(LogLevel.Trace, "Retrieved record: {Record}")]
    private partial void LogGetResult(string record);

    [LoggerMessage(LogLevel.Trace, "Upserting a record: {Record}")]
    private partial void LogUpsert(string record);

    [LoggerMessage(LogLevel.Trace, "Upserting records: {Records}")]
    private partial void LogUpsertBatch(string records);

    [LoggerMessage(LogLevel.Trace, "Upserted record with key: {Key}")]
    private partial void LogUpsertResult(string key);

    #endregion
}
