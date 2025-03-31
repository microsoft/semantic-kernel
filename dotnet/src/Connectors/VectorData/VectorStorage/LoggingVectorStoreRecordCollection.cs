// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

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

    /// <summary>
    /// Initializes a new instance of the <see cref="LoggingVectorStoreRecordCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="innerCollection">The underlying <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="logger">An <see cref="ILogger"/> instance that will be used for all logging.</param>
    public LoggingVectorStoreRecordCollection(IVectorStoreRecordCollection<TKey, TRecord> innerCollection, ILogger logger)
    {
        this._innerCollection = innerCollection ?? throw new ArgumentNullException(nameof(innerCollection));
        this._logger = logger ?? throw new ArgumentNullException(nameof(logger));
    }

    /// <inheritdoc/>
    public string CollectionName => this._innerCollection.CollectionName;

    /// <inheritdoc/>
    public async Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        this.CollectionExistsInvoked(nameof(CollectionExistsAsync), this.CollectionName);

        try
        {
            var result = await this._innerCollection
                .CollectionExistsAsync(cancellationToken)
                .ConfigureAwait(false);

            this.CollectionExistsCompleted(nameof(CollectionExistsAsync), this.CollectionName, result);

            return result;
        }
        catch (OperationCanceledException)
        {
            this.CollectionExistsCanceled(nameof(CollectionExistsAsync), this.CollectionName);
            throw;
        }
        catch (Exception ex)
        {
            this.CollectionExistsFailed(nameof(CollectionExistsAsync), this.CollectionName, ex);
            throw;
        }
    }

    /// <inheritdoc/>
    public async Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        this.CreateCollectionInvoked(nameof(CreateCollectionAsync), this.CollectionName);

        try
        {
            await this._innerCollection
                .CreateCollectionAsync(cancellationToken)
                .ConfigureAwait(false);

            this.CreateCollectionCompleted(nameof(CreateCollectionAsync), this.CollectionName);
        }
        catch (OperationCanceledException)
        {
            this.CreateCollectionCanceled(nameof(CreateCollectionAsync), this.CollectionName);
            throw;
        }
        catch (Exception ex)
        {
            this.CreateCollectionFailed(nameof(CreateCollectionAsync), this.CollectionName, ex);
            throw;
        }
    }

    /// <inheritdoc/>
    public async Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default)
    {
        this.CreateCollectionIfNotExistsInvoked(nameof(CreateCollectionIfNotExistsAsync), this.CollectionName);

        try
        {
            await this._innerCollection
                .CreateCollectionIfNotExistsAsync(cancellationToken)
                .ConfigureAwait(false);

            this.CreateCollectionIfNotExistsCompleted(nameof(CreateCollectionIfNotExistsAsync), this.CollectionName);
        }
        catch (OperationCanceledException)
        {
            this.CreateCollectionIfNotExistsCanceled(nameof(CreateCollectionIfNotExistsAsync), this.CollectionName);
            throw;
        }
        catch (Exception ex)
        {
            this.CreateCollectionIfNotExistsFailed(nameof(CreateCollectionIfNotExistsAsync), this.CollectionName, ex);
            throw;
        }
    }

    /// <inheritdoc/>
    public async Task DeleteAsync(TKey key, CancellationToken cancellationToken = default)
    {
        var keyString = key.ToString();

        if (this._logger.IsEnabled(LogLevel.Debug))
        {
            if (this._logger.IsEnabled(LogLevel.Trace))
            {
                this.DeleteInvokedSensitive(nameof(DeleteAsync), this.CollectionName, keyString);
            }
            else
            {
                this.DeleteInvoked(nameof(DeleteAsync), this.CollectionName);
            }
        }

        try
        {
            await this._innerCollection
                .DeleteAsync(key, cancellationToken)
                .ConfigureAwait(false);

            if (this._logger.IsEnabled(LogLevel.Debug))
            {
                if (this._logger.IsEnabled(LogLevel.Trace))
                {
                    this.DeleteCompletedSensitive(nameof(DeleteAsync), this.CollectionName, keyString);
                }
                else
                {
                    this.DeleteCompleted(nameof(DeleteAsync), this.CollectionName);
                }
            }
        }
        catch (OperationCanceledException)
        {
            this.DeleteCanceled(nameof(DeleteAsync), this.CollectionName);
            throw;
        }
        catch (Exception ex)
        {
            this.DeleteFailed(nameof(DeleteAsync), this.CollectionName, ex);
            throw;
        }
    }

    /// <inheritdoc/>
    public async Task DeleteBatchAsync(IEnumerable<TKey> keys, CancellationToken cancellationToken = default)
    {
        var keysString = string.Join(",", keys.Select(k => k.ToString()));

        if (this._logger.IsEnabled(LogLevel.Debug))
        {
            if (this._logger.IsEnabled(LogLevel.Trace))
            {
                this.DeleteBatchInvokedSensitive(nameof(DeleteBatchAsync), this.CollectionName, keysString);
            }
            else
            {
                this.DeleteBatchInvoked(nameof(DeleteBatchAsync), this.CollectionName);
            }
        }

        try
        {
            await this._innerCollection
                .DeleteBatchAsync(keys, cancellationToken)
                .ConfigureAwait(false);

            if (this._logger.IsEnabled(LogLevel.Debug))
            {
                if (this._logger.IsEnabled(LogLevel.Trace))
                {
                    this.DeleteBatchCompletedSensitive(nameof(DeleteBatchAsync), this.CollectionName, keysString);
                }
                else
                {
                    this.DeleteBatchCompleted(nameof(DeleteBatchAsync), this.CollectionName);
                }
            }
        }
        catch (OperationCanceledException)
        {
            this.DeleteBatchCanceled(nameof(DeleteBatchAsync), this.CollectionName);
            throw;
        }
        catch (Exception ex)
        {
            this.DeleteBatchFailed(nameof(DeleteBatchAsync), this.CollectionName, ex);
            throw;
        }
    }

    /// <inheritdoc/>
    public async Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
    {
        this.DeleteCollectionInvoked(nameof(DeleteCollectionAsync), this.CollectionName);

        try
        {
            await this._innerCollection
                .DeleteCollectionAsync(cancellationToken)
                .ConfigureAwait(false);

            this.DeleteCollectionCompleted(nameof(DeleteCollectionAsync), this.CollectionName);
        }
        catch (OperationCanceledException)
        {
            this.DeleteCollectionCanceled(nameof(DeleteCollectionAsync), this.CollectionName);
            throw;
        }
        catch (Exception ex)
        {
            this.DeleteCollectionFailed(nameof(DeleteCollectionAsync), this.CollectionName, ex);
            throw;
        }
    }

    /// <inheritdoc/>
    public async Task<TRecord?> GetAsync(TKey key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        var keyString = key.ToString();

        if (this._logger.IsEnabled(LogLevel.Debug))
        {
            if (this._logger.IsEnabled(LogLevel.Trace))
            {
                this.GetInvokedSensitive(nameof(GetAsync), this.CollectionName, keyString);
            }
            else
            {
                this.GetInvoked(nameof(GetAsync), this.CollectionName);
            }
        }

        try
        {
            var result = await this._innerCollection
                .GetAsync(key, options, cancellationToken)
                .ConfigureAwait(false);

            if (this._logger.IsEnabled(LogLevel.Debug))
            {
                if (this._logger.IsEnabled(LogLevel.Trace))
                {
                    this.GetCompletedSensitive(nameof(GetAsync), this.CollectionName, keyString);
                }
                else
                {
                    this.GetCompleted(nameof(GetAsync), this.CollectionName);
                }
            }

            return result;
        }
        catch (OperationCanceledException)
        {
            this.GetCanceled(nameof(GetAsync), this.CollectionName);
            throw;
        }
        catch (Exception ex)
        {
            this.GetFailed(nameof(GetAsync), this.CollectionName, ex);
            throw;
        }
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<TKey> keys, GetRecordOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var keysString = string.Join(",", keys.Select(k => k.ToString()));

        if (this._logger.IsEnabled(LogLevel.Debug))
        {
            if (this._logger.IsEnabled(LogLevel.Trace))
            {
                this.GetBatchInvokedSensitive(nameof(GetBatchAsync), this.CollectionName, keysString);
            }
            else
            {
                this.GetBatchInvoked(nameof(GetBatchAsync), this.CollectionName);
            }
        }

        IAsyncEnumerator<TRecord> enumerator;

        try
        {
            enumerator = this._innerCollection
                .GetBatchAsync(keys, options, cancellationToken)
                .GetAsyncEnumerator(cancellationToken);
        }
        catch (OperationCanceledException)
        {
            this.GetBatchCanceled(nameof(GetBatchAsync), this.CollectionName);
            throw;
        }
        catch (Exception ex)
        {
            this.GetBatchFailed(nameof(GetBatchAsync), this.CollectionName, ex);
            throw;
        }

        try
        {
            while (true)
            {
                try
                {
                    if (!await enumerator.MoveNextAsync().ConfigureAwait(false))
                    {
                        break;
                    }
                }
                catch (OperationCanceledException)
                {
                    this.GetBatchCanceled(nameof(GetBatchAsync), this.CollectionName);
                    throw;
                }
                catch (Exception ex)
                {
                    this.GetBatchFailed(nameof(GetBatchAsync), this.CollectionName, ex);
                    throw;
                }

                yield return enumerator.Current;
            }

            if (this._logger.IsEnabled(LogLevel.Debug))
            {
                if (this._logger.IsEnabled(LogLevel.Trace))
                {
                    this.GetBatchCompletedSensitive(nameof(GetBatchAsync), this.CollectionName, keysString);
                }
                else
                {
                    this.GetBatchCompleted(nameof(GetBatchAsync), this.CollectionName);
                }
            }
        }
        finally
        {
            await enumerator.DisposeAsync().ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    public async Task<TKey> UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        this.UpsertInvoked(nameof(UpsertAsync), this.CollectionName);

        try
        {
            var key = await this._innerCollection
                .UpsertAsync(record, cancellationToken)
                .ConfigureAwait(false);

            if (this._logger.IsEnabled(LogLevel.Debug))
            {
                if (this._logger.IsEnabled(LogLevel.Trace))
                {
                    this.UpsertCompletedSensitive(nameof(UpsertAsync), this.CollectionName, key.ToString());
                }
                else
                {
                    this.UpsertCompleted(nameof(UpsertAsync), this.CollectionName);
                }
            }

            return key;
        }
        catch (OperationCanceledException)
        {
            this.UpsertCanceled(nameof(UpsertAsync), this.CollectionName);
            throw;
        }
        catch (Exception ex)
        {
            this.UpsertFailed(nameof(UpsertAsync), this.CollectionName, ex);
            throw;
        }
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<TKey> UpsertBatchAsync(IEnumerable<TRecord> records, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var keys = new List<string?>();

        this.UpsertBatchInvoked(nameof(UpsertBatchAsync), this.CollectionName);

        IAsyncEnumerator<TKey> enumerator;

        try
        {
            enumerator = this._innerCollection
                .UpsertBatchAsync(records, cancellationToken)
                .GetAsyncEnumerator(cancellationToken);
        }
        catch (OperationCanceledException)
        {
            this.UpsertBatchCanceled(nameof(UpsertBatchAsync), this.CollectionName);
            throw;
        }
        catch (Exception ex)
        {
            this.UpsertBatchFailed(nameof(UpsertBatchAsync), this.CollectionName, ex);
            throw;
        }

        try
        {
            while (true)
            {
                try
                {
                    if (!await enumerator.MoveNextAsync().ConfigureAwait(false))
                    {
                        break;
                    }
                }
                catch (OperationCanceledException)
                {
                    this.UpsertBatchCanceled(nameof(UpsertBatchAsync), this.CollectionName);
                    throw;
                }
                catch (Exception ex)
                {
                    this.UpsertBatchFailed(nameof(UpsertBatchAsync), this.CollectionName, ex);
                    throw;
                }

                keys.Add(enumerator.Current.ToString());

                yield return enumerator.Current;
            }

            var keysString = string.Join(",", keys);

            if (this._logger.IsEnabled(LogLevel.Debug))
            {
                if (this._logger.IsEnabled(LogLevel.Trace))
                {
                    this.UpsertBatchCompletedSensitive(nameof(UpsertBatchAsync), this.CollectionName, keysString);
                }
                else
                {
                    this.UpsertBatchCompleted(nameof(UpsertBatchAsync), this.CollectionName);
                }
            }
        }
        finally
        {
            await enumerator.DisposeAsync().ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    public async Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        this.VectorizedSearchInvoked(nameof(VectorizedSearchAsync), this.CollectionName);

        try
        {
            var result = await this._innerCollection
                .VectorizedSearchAsync(vector, options, cancellationToken)
                .ConfigureAwait(false);

            this.VectorizedSearchCompleted(nameof(VectorizedSearchAsync), this.CollectionName);

            return result;
        }
        catch (OperationCanceledException)
        {
            this.VectorizedSearchCanceled(nameof(VectorizedSearchAsync), this.CollectionName);
            throw;
        }
        catch (Exception ex)
        {
            this.VectorizedSearchFailed(nameof(VectorizedSearchAsync), this.CollectionName, ex);
            throw;
        }
    }

    #region private

    [LoggerMessage(LogLevel.Debug, "{OperationName} invoked. Collection name: {CollectionName}.")]
    private partial void CollectionExistsInvoked(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Debug, "{OperationName} completed. Collection name: {CollectionName}. Collection exists: {CollectionExists}")]
    private partial void CollectionExistsCompleted(string operationName, string collectionName, bool collectionExists);

    [LoggerMessage(LogLevel.Debug, "{OperationName} canceled. Collection name: {CollectionName}.")]
    private partial void CollectionExistsCanceled(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Error, "{OperationName} failed. CollectionName: {CollectionName}.")]
    private partial void CollectionExistsFailed(string operationName, string collectionName, Exception exception);

    [LoggerMessage(LogLevel.Debug, "{OperationName} invoked. Collection name: {CollectionName}.")]
    private partial void CreateCollectionInvoked(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Debug, "{OperationName} completed. Collection name: {CollectionName}.")]
    private partial void CreateCollectionCompleted(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Debug, "{OperationName} canceled. Collection name: {CollectionName}.")]
    private partial void CreateCollectionCanceled(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Error, "{OperationName} failed. CollectionName: {CollectionName}.")]
    private partial void CreateCollectionFailed(string operationName, string collectionName, Exception exception);

    [LoggerMessage(LogLevel.Debug, "{OperationName} invoked. Collection name: {CollectionName}.")]
    private partial void CreateCollectionIfNotExistsInvoked(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Debug, "{OperationName} completed. Collection name: {CollectionName}.")]
    private partial void CreateCollectionIfNotExistsCompleted(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Debug, "{OperationName} canceled. Collection name: {CollectionName}.")]
    private partial void CreateCollectionIfNotExistsCanceled(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Error, "{OperationName} failed. CollectionName: {CollectionName}.")]
    private partial void CreateCollectionIfNotExistsFailed(string operationName, string collectionName, Exception exception);

    [LoggerMessage(LogLevel.Trace, "{OperationName} invoked. Collection Name: {CollectionName}. Key: {Key}.")]
    private partial void DeleteInvokedSensitive(string operationName, string collectionName, string? key);

    [LoggerMessage(LogLevel.Trace, "{OperationName} completed. Collection Name: {CollectionName}. Key: {Key}.")]
    private partial void DeleteCompletedSensitive(string operationName, string collectionName, string? key);

    [LoggerMessage(LogLevel.Debug, "{OperationName} invoked. Collection Name: {CollectionName}.")]
    private partial void DeleteInvoked(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Debug, "{OperationName} completed. Collection Name: {CollectionName}.")]
    private partial void DeleteCompleted(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Debug, "{OperationName} canceled. Collection Name: {CollectionName}.")]
    private partial void DeleteCanceled(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Error, "{OperationName} failed. Collection Name: {CollectionName}.")]
    private partial void DeleteFailed(string operationName, string collectionName, Exception exception);

    [LoggerMessage(LogLevel.Trace, "{OperationName} invoked. Collection Name: {CollectionName}. Keys: {Keys}.")]
    private partial void DeleteBatchInvokedSensitive(string operationName, string collectionName, string? keys);

    [LoggerMessage(LogLevel.Trace, "{OperationName} completed. Collection Name: {CollectionName}. Keys: {Keys}.")]
    private partial void DeleteBatchCompletedSensitive(string operationName, string collectionName, string? keys);

    [LoggerMessage(LogLevel.Debug, "{OperationName} invoked. Collection Name: {CollectionName}.")]
    private partial void DeleteBatchInvoked(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Debug, "{OperationName} completed. Collection Name: {CollectionName}.")]
    private partial void DeleteBatchCompleted(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Debug, "{OperationName} canceled. Collection Name: {CollectionName}.")]
    private partial void DeleteBatchCanceled(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Error, "{OperationName} failed. Collection Name: {CollectionName}.")]
    private partial void DeleteBatchFailed(string operationName, string collectionName, Exception exception);

    [LoggerMessage(LogLevel.Debug, "{OperationName} invoked. Collection Name: {CollectionName}.")]
    private partial void DeleteCollectionInvoked(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Debug, "{OperationName} completed. CollectionName: {CollectionName}.")]
    private partial void DeleteCollectionCompleted(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Debug, "{OperationName} canceled. CollectionName: {CollectionName}.")]
    private partial void DeleteCollectionCanceled(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Error, "{OperationName} failed. CollectionName: {CollectionName}.")]
    private partial void DeleteCollectionFailed(string operationName, string collectionName, Exception exception);

    [LoggerMessage(LogLevel.Debug, "{OperationName} invoked. Collection Name: {CollectionName}.")]
    private partial void GetInvoked(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Debug, "{OperationName} completed. Collection Name: {CollectionName}.")]
    private partial void GetCompleted(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Trace, "{OperationName} invoked. Collection Name: {CollectionName}. Key: {Key}.")]
    private partial void GetInvokedSensitive(string operationName, string collectionName, string? key);

    [LoggerMessage(LogLevel.Trace, "{OperationName} completed. Collection Name: {CollectionName}. Key: {Key}.")]
    private partial void GetCompletedSensitive(string operationName, string collectionName, string? key);

    [LoggerMessage(LogLevel.Debug, "{OperationName} canceled. Collection Name: {CollectionName}.")]
    private partial void GetCanceled(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Error, "{OperationName} failed. Collection Name: {CollectionName}.")]
    private partial void GetFailed(string operationName, string collectionName, Exception exception);

    [LoggerMessage(LogLevel.Debug, "{OperationName} invoked. Collection Name: {CollectionName}.")]
    private partial void GetBatchInvoked(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Debug, "{OperationName} completed. Collection Name: {CollectionName}.")]
    private partial void GetBatchCompleted(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Trace, "{OperationName} invoked. Collection Name: {CollectionName}. Keys: {Keys}.")]
    private partial void GetBatchInvokedSensitive(string operationName, string collectionName, string? keys);

    [LoggerMessage(LogLevel.Trace, "{OperationName} completed. Collection Name: {CollectionName}. Keys: {Keys}.")]
    private partial void GetBatchCompletedSensitive(string operationName, string collectionName, string? keys);

    [LoggerMessage(LogLevel.Debug, "{OperationName} canceled. Collection Name: {CollectionName}.")]
    private partial void GetBatchCanceled(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Error, "{OperationName} failed. Collection Name: {CollectionName}.")]
    private partial void GetBatchFailed(string operationName, string collectionName, Exception exception);

    [LoggerMessage(LogLevel.Debug, "{OperationName} invoked. Collection name: {CollectionName}.")]
    private partial void UpsertInvoked(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Debug, "{OperationName} completed. Collection name: {CollectionName}.")]
    private partial void UpsertCompleted(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Trace, "{OperationName} completed. Collection name: {CollectionName}. Key: {Key}.")]
    private partial void UpsertCompletedSensitive(string operationName, string collectionName, string? key);

    [LoggerMessage(LogLevel.Debug, "{OperationName} canceled. Collection name: {CollectionName}.")]
    private partial void UpsertCanceled(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Error, "{OperationName} failed. CollectionName: {CollectionName}.")]
    private partial void UpsertFailed(string operationName, string collectionName, Exception exception);

    [LoggerMessage(LogLevel.Debug, "{OperationName} invoked. Collection name: {CollectionName}.")]
    private partial void UpsertBatchInvoked(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Debug, "{OperationName} completed. Collection name: {CollectionName}.")]
    private partial void UpsertBatchCompleted(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Trace, "{OperationName} completed. Collection name: {CollectionName}. Keys: {Keys}.")]
    private partial void UpsertBatchCompletedSensitive(string operationName, string collectionName, string keys);

    [LoggerMessage(LogLevel.Debug, "{OperationName} canceled. Collection name: {CollectionName}.")]
    private partial void UpsertBatchCanceled(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Error, "{OperationName} failed. CollectionName: {CollectionName}.")]
    private partial void UpsertBatchFailed(string operationName, string collectionName, Exception exception);

    [LoggerMessage(LogLevel.Debug, "{OperationName} invoked. Collection Name: {CollectionName}.")]
    private partial void VectorizedSearchInvoked(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Debug, "{OperationName} completed. Collection Name: {CollectionName}.")]
    private partial void VectorizedSearchCompleted(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Debug, "{OperationName} canceled. Collection Name: {CollectionName}.")]
    private partial void VectorizedSearchCanceled(string operationName, string collectionName);

    [LoggerMessage(LogLevel.Error, "{OperationName} failed. Collection Name: {CollectionName}.")]
    private partial void VectorizedSearchFailed(string operationName, string collectionName, Exception exception);

    #endregion
}
