// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// A vectorizable text search that logs operations to an <see cref="ILogger"/>
/// </summary>
[Experimental("SKEXP0020")]
public partial class LoggingVectorizableTextSearch<TRecord> : IVectorizableTextSearch<TRecord>
{
    /// <summary>An <see cref="ILogger"/> instance used for all logging.</summary>
    private readonly ILogger _logger;

    /// <summary>The underlying <see cref="IVectorizableTextSearch{TRecord}"/>.</summary>
    private readonly IVectorizableTextSearch<TRecord> _innerSearch;

    /// <summary>
    /// Initializes a new instance of the <see cref="LoggingVectorizableTextSearch{TRecord}"/> class.
    /// </summary>
    /// <param name="innerSearch">The underlying <see cref="IVectorizableTextSearch{TRecord}"/>.</param>
    /// <param name="logger">An <see cref="ILogger"/> instance used for all logging.</param>
    public LoggingVectorizableTextSearch(IVectorizableTextSearch<TRecord> innerSearch, ILogger logger)
    {
        this._innerSearch = innerSearch ?? throw new ArgumentNullException(nameof(innerSearch));
        this._logger = logger ?? throw new ArgumentNullException(nameof(logger));
    }

    /// <inheritdoc/>
    public async Task<VectorSearchResults<TRecord>> VectorizableTextSearchAsync(string searchText, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        this.VectorizableTextSearchInvoked(nameof(VectorizableTextSearchAsync));

        try
        {
            var result = await this._innerSearch
                .VectorizableTextSearchAsync(searchText, options, cancellationToken)
                .ConfigureAwait(false);

            this.VectorizableTextSearchCompleted(nameof(VectorizableTextSearchAsync));

            return result;
        }
        catch (OperationCanceledException)
        {
            this.VectorizableTextSearchCanceled(nameof(VectorizableTextSearchAsync));
            throw;
        }
        catch (Exception ex)
        {
            this.VectorizableTextSearchFailed(nameof(VectorizableTextSearchAsync), ex);
            throw;
        }
    }

    #region private

    [LoggerMessage(LogLevel.Debug, "{OperationName} invoked.")]
    private partial void VectorizableTextSearchInvoked(string operationName);

    [LoggerMessage(LogLevel.Debug, "{OperationName} completed.")]
    private partial void VectorizableTextSearchCompleted(string operationName);

    [LoggerMessage(LogLevel.Debug, "{OperationName} canceled.")]
    private partial void VectorizableTextSearchCanceled(string operationName);

    [LoggerMessage(LogLevel.Error, "{OperationName} failed.")]
    private partial void VectorizableTextSearchFailed(string operationName, Exception exception);

    #endregion
}
