// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// A vectorized search that logs operations to an <see cref="ILogger"/>
/// </summary>
[Experimental("SKEXP0020")]
public partial class LoggingVectorizedSearch<TRecord> : IVectorizedSearch<TRecord>
{
    /// <summary>An <see cref="ILogger"/> instance used for all logging.</summary>
    private readonly ILogger _logger;

    /// <summary>The underlying <see cref="IVectorizedSearch{TRecord}"/>.</summary>
    private readonly IVectorizedSearch<TRecord> _innerSearch;

    /// <summary>
    /// Initializes a new instance of the <see cref="LoggingVectorizedSearch{TRecord}"/> class.
    /// </summary>
    /// <param name="innerSearch">The underlying <see cref="IVectorizedSearch{TRecord}"/>.</param>
    /// <param name="logger">An <see cref="ILogger"/> instance used for all logging.</param>
    public LoggingVectorizedSearch(IVectorizedSearch<TRecord> innerSearch, ILogger logger)
    {
        this._innerSearch = innerSearch ?? throw new ArgumentNullException(nameof(innerSearch));
        this._logger = logger ?? throw new ArgumentNullException(nameof(logger));
    }

    /// <inheritdoc/>
    public async Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        this.VectorizedSearchInvoked(nameof(VectorizedSearchAsync));

        try
        {
            var result = await this._innerSearch
                .VectorizedSearchAsync(vector, options, cancellationToken)
                .ConfigureAwait(false);

            this.VectorizedSearchCompleted(nameof(VectorizedSearchAsync));

            return result;
        }
        catch (OperationCanceledException)
        {
            this.VectorizedSearchCanceled(nameof(VectorizedSearchAsync));
            throw;
        }
        catch (Exception ex)
        {
            this.VectorizedSearchFailed(nameof(VectorizedSearchAsync), ex);
            throw;
        }
    }

    #region private

    [LoggerMessage(LoggingEventIds.VectorizedSearchInvoked, LogLevel.Debug, "{OperationName} invoked.")]
    private partial void VectorizedSearchInvoked(string operationName);

    [LoggerMessage(LoggingEventIds.VectorizedSearchCompleted, LogLevel.Debug, "{OperationName} completed.")]
    private partial void VectorizedSearchCompleted(string operationName);

    [LoggerMessage(LoggingEventIds.VectorizedSearchCanceled, LogLevel.Debug, "{OperationName} canceled.")]
    private partial void VectorizedSearchCanceled(string operationName);

    [LoggerMessage(LoggingEventIds.VectorizedSearchFailed, LogLevel.Error, "{OperationName} failed.")]
    private partial void VectorizedSearchFailed(string operationName, Exception exception);

    #endregion
}
