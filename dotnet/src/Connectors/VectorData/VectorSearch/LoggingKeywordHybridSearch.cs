// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// A keyword hybrid search that logs operations to an <see cref="ILogger"/>
/// </summary>
[Experimental("SKEXP0020")]
public partial class LoggingKeywordHybridSearch<TRecord> : IKeywordHybridSearch<TRecord>
{
    /// <summary>An <see cref="ILogger"/> instance used for all logging.</summary>
    private readonly ILogger _logger;

    /// <summary>The underlying <see cref="IKeywordHybridSearch{TRecord}"/>.</summary>
    private readonly IKeywordHybridSearch<TRecord> _innerSearch;

    /// <summary>
    /// Initializes a new instance of the <see cref="LoggingKeywordHybridSearch{TRecord}"/> class.
    /// </summary>
    /// <param name="innerSearch">The underlying <see cref="LoggingKeywordHybridSearch{TRecord}"/>.</param>
    /// <param name="logger">An <see cref="ILogger"/> instance that will be used for all logging.</param>
    public LoggingKeywordHybridSearch(IKeywordHybridSearch<TRecord> innerSearch, ILogger logger)
    {
        this._innerSearch = innerSearch ?? throw new ArgumentNullException(nameof(innerSearch));
        this._logger = logger ?? throw new ArgumentNullException(nameof(logger));
    }

    /// <inheritdoc/>
    public async Task<VectorSearchResults<TRecord>> HybridSearchAsync<TVector>(TVector vector, ICollection<string> keywords, HybridSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        this.HybridSearchInvoked(nameof(HybridSearchAsync));

        try
        {
            var result = await this._innerSearch
                .HybridSearchAsync(vector, keywords, options, cancellationToken)
                .ConfigureAwait(false);

            this.HybridSearchCompleted(nameof(HybridSearchAsync));

            return result;
        }
        catch (OperationCanceledException)
        {
            this.HybridSearchCanceled(nameof(HybridSearchAsync));
            throw;
        }
        catch (Exception ex)
        {
            this.HybridSearchFailed(nameof(HybridSearchAsync), ex);
            throw;
        }
    }

    #region private

    [LoggerMessage(LoggingEventIds.HybridSearchInvoked, LogLevel.Debug, "{OperationName} invoked.")]
    private partial void HybridSearchInvoked(string operationName);

    [LoggerMessage(LoggingEventIds.HybridSearchCompleted, LogLevel.Debug, "{OperationName} completed.")]
    private partial void HybridSearchCompleted(string operationName);

    [LoggerMessage(LoggingEventIds.HybridSearchCanceled, LogLevel.Debug, "{OperationName} canceled.")]
    private partial void HybridSearchCanceled(string operationName);

    [LoggerMessage(LoggingEventIds.HybridSearchFailed, LogLevel.Error, "{OperationName} failed.")]
    private partial void HybridSearchFailed(string operationName, Exception exception);

    #endregion
}
