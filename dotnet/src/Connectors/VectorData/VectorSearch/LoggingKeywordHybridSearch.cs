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
/// A keyword hybrid search that logs operations to an <see cref="ILogger"/>
/// </summary>
[Experimental("SKEXP0020")]
public class LoggingKeywordHybridSearch<TRecord> : IKeywordHybridSearch<TRecord>
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
        Verify.NotNull(innerSearch);
        Verify.NotNull(logger);

        this._innerSearch = innerSearch;
        this._logger = logger;
    }

    /// <inheritdoc/>
    public Task<VectorSearchResults<TRecord>> HybridSearchAsync<TVector>(TVector vector, ICollection<string> keywords, HybridSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        return LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(HybridSearchAsync),
            () => this._innerSearch.HybridSearchAsync(vector, keywords, options, cancellationToken));
    }

    /// <inheritdoc/>
    public object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is null && serviceType.IsInstanceOfType(this) ? this :
            this._innerSearch.GetService(serviceType, serviceKey);
    }
}
