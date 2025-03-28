// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Provides an optional base class for an <see cref="IVectorizedSearch{TRecord}"/> that passes through calls to another instance.
/// </summary>
/// <remarks>
/// This is recommended as a base type when building services that can be chained around an underlying <see cref="IVectorizedSearch{TRecord}"/>.
/// The default implementation simply passes each call to the inner search instance.
/// </remarks>
/// <typeparam name="TRecord">The record data model to use for retrieving data from the store.</typeparam>
[Experimental("SKEXP0020")]
public class DelegatingVectorizedSearch<TRecord> : IVectorizedSearch<TRecord>
{
    /// <summary>Gets the inner <see cref="IVectorizedSearch{TRecord}"/>.</summary>
    protected IVectorizedSearch<TRecord> InnerSearch { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="DelegatingVectorizedSearch{TRecord}"/> class.
    /// </summary>
    /// <param name="innerSearch">The wrapped search instance.</param>
    protected DelegatingVectorizedSearch(IVectorizedSearch<TRecord> innerSearch)
    {
        this.InnerSearch = innerSearch ?? throw new ArgumentNullException(nameof(innerSearch));
    }

    /// <inheritdoc />
    public virtual Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(
        TVector vector,
        VectorSearchOptions<TRecord>? options = default,
        CancellationToken cancellationToken = default)
    {
        return this.InnerSearch.VectorizedSearchAsync(vector, options, cancellationToken);
    }
}
