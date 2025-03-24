// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Provides an optional base class for an <see cref="IKeywordHybridSearch{TRecord}"/> that passes through calls to another instance.
/// </summary>
/// <remarks>
/// This is recommended as a base type when building services that can be chained around an underlying <see cref="IKeywordHybridSearch{TRecord}"/>.
/// The default implementation simply passes each call to the inner search instance.
/// </remarks>
/// <typeparam name="TRecord">The record data model to use for retrieving data from the store.</typeparam>
[Experimental("SKEXP0020")]
public class DelegatingKeywordHybridSearch<TRecord> : IKeywordHybridSearch<TRecord>
{
    /// <summary>Gets the inner <see cref="IKeywordHybridSearch{TRecord}"/>.</summary>
    protected IKeywordHybridSearch<TRecord> InnerSearch { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="DelegatingKeywordHybridSearch{TRecord}"/> class.
    /// </summary>
    /// <param name="innerSearch">The wrapped search instance.</param>
    protected DelegatingKeywordHybridSearch(IKeywordHybridSearch<TRecord> innerSearch)
    {
        this.InnerSearch = innerSearch ?? throw new ArgumentNullException(nameof(innerSearch));
    }

    /// <inheritdoc />
    public virtual Task<VectorSearchResults<TRecord>> HybridSearchAsync<TVector>(
        TVector vector,
        ICollection<string> keywords,
        HybridSearchOptions<TRecord>? options = default,
        CancellationToken cancellationToken = default)
    {
        return this.InnerSearch.HybridSearchAsync(vector, keywords, options, cancellationToken);
    }
}
