// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// A vectorized search that logs operations to an <see cref="ILogger"/>
/// </summary>
[Experimental("SKEXP0020")]
public class LoggingVectorizedSearch<TRecord> : IVectorizedSearch<TRecord>
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
        this._innerSearch = innerSearch;
        this._logger = logger;
    }

    /// <inheritdoc/>
    public Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        return LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(VectorizedSearchAsync),
            () => this._innerSearch.VectorizedSearchAsync(vector, options, cancellationToken));
    }
}
