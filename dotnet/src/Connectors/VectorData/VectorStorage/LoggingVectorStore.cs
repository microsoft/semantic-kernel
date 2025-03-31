// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;
using System.Threading;
using Microsoft.Extensions.Logging;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// A vector store that logs operations to an <see cref="ILogger"/>
/// </summary>
[Experimental("SKEXP0020")]
public partial class LoggingVectorStore : IVectorStore
{
    /// <summary>An <see cref="ILogger"/> instance used for all logging.</summary>
    private readonly ILogger _logger;

    /// <summary>The underlying <see cref="IVectorStore"/>.</summary>
    private readonly IVectorStore _innerStore;

    /// <summary>
    /// Initializes a new instance of the <see cref="LoggingVectorStore"/> class.
    /// </summary>
    /// <param name="innerStore">The underlying <see cref="IVectorStore"/>.</param>
    /// <param name="logger">An <see cref="ILogger"/> instance that will be used for all logging.</param>
    public LoggingVectorStore(IVectorStore innerStore, ILogger logger)
    {
        this._innerStore = innerStore ?? throw new ArgumentNullException(nameof(innerStore));
        this._logger = logger ?? throw new ArgumentNullException(nameof(logger));
    }

    /// <inheritdoc/>
    public IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null) where TKey : notnull
    {
        return
            new LoggingVectorStoreRecordCollection<TKey, TRecord>(
                this._innerStore.GetCollection<TKey, TRecord>(name, vectorStoreRecordDefinition),
                this._logger);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> ListCollectionNamesAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var collections = new List<string>();

        this.ListCollectionNamesInvoked(nameof(ListCollectionNamesAsync));

        IAsyncEnumerator<string> enumerator;

        try
        {
            enumerator = this._innerStore.ListCollectionNamesAsync(cancellationToken).GetAsyncEnumerator(cancellationToken);
        }
        catch (OperationCanceledException)
        {
            this.ListCollectionNamesCanceled(nameof(ListCollectionNamesAsync));
            throw;
        }
        catch (Exception ex)
        {
            this.ListCollectionNamesFailed(nameof(ListCollectionNamesAsync), ex);
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
                    this.ListCollectionNamesCanceled(nameof(ListCollectionNamesAsync));
                    throw;
                }
                catch (Exception ex)
                {
                    this.ListCollectionNamesFailed(nameof(ListCollectionNamesAsync), ex);
                    throw;
                }

                collections.Add(enumerator.Current);

                yield return enumerator.Current;
            }

            if (this._logger.IsEnabled(LogLevel.Debug))
            {
                this.ListCollectionNamesCompleted(nameof(ListCollectionNamesAsync), string.Join(",", collections));
            }
        }
        finally
        {
            await enumerator.DisposeAsync().ConfigureAwait(false);
        }
    }

    #region private

    [LoggerMessage(LogLevel.Debug, "{OperationName} invoked.")]
    private partial void ListCollectionNamesInvoked(string operationName);

    [LoggerMessage(LogLevel.Debug, "{OperationName} completed. Collections: {Collections}")]
    private partial void ListCollectionNamesCompleted(string operationName, string collections);

    [LoggerMessage(LogLevel.Debug, "{OperationName} canceled.")]
    private partial void ListCollectionNamesCanceled(string operationName);

    [LoggerMessage(LogLevel.Error, "{OperationName} failed.")]
    private partial void ListCollectionNamesFailed(string operationName, Exception exception);

    #endregion
}
